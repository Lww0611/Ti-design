import math
from typing import Dict, List, Sequence

import joblib
import numpy as np
import torch
from torch import nn


class CompositionCVAE(nn.Module):
    """
    组合成分条件 VAE。

    注意：
    - 这里的结构需要与训练时保持一致才能正确加载 state_dict。
    - 训练脚本中保存了 config = {input_dim, cond_dim, latent_dim, hidden_dim}，
      因此这里采用一个典型的两层 MLP 编码器 / 解码器结构。
    """

    def __init__(self, input_dim: int, cond_dim: int, latent_dim: int, hidden_dim: int) -> None:
        super().__init__()
        enc_in = input_dim + cond_dim
        dec_in = latent_dim + cond_dim

        self.encoder = nn.Sequential(
            nn.Linear(enc_in, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)

        self.decoder = nn.Sequential(
            nn.Linear(dec_in, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

        self.input_dim = input_dim
        self.cond_dim = cond_dim
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim

    def encode(self, x: torch.Tensor, c: torch.Tensor):
        h = self.encoder(torch.cat([x, c], dim=-1))
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor, c: torch.Tensor):
        h = torch.cat([z, c], dim=-1)
        x_recon = self.decoder(h)
        return x_recon

    def forward(self, x: torch.Tensor, c: torch.Tensor):
        mu, logvar = self.encode(x, c)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z, c)
        return recon, mu, logvar

    def sample(self, cond: torch.Tensor, n_samples: int) -> torch.Tensor:
        """
        基于单一 cond 采样多组成分。
        cond: [cond_dim] 或 [1, cond_dim]
        返回: [n_samples, input_dim]
        """
        if cond.dim() == 1:
            cond = cond.unsqueeze(0)
        cond = cond.to(next(self.parameters()).device)

        cond = cond.repeat(n_samples, 1)
        z = torch.randn(n_samples, self.latent_dim, device=cond.device)
        with torch.no_grad():
            x = self.decode(z, cond)
        return x


class CompositionGenerator:
    """
    封装：加载 CVAE + cond_scaler，并提供成分采样接口。
    """

    def __init__(
        self,
        ckpt_path: str,
        scaler_path: str,
        device: str | None = None,
    ) -> None:
        self.ckpt_path = ckpt_path
        self.scaler_path = scaler_path

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)

        self._load_model_and_scaler()

    def _load_model_and_scaler(self) -> None:
        ckpt = torch.load(self.ckpt_path, map_location=self.device)

        config = ckpt.get("config", {})
        input_dim = config.get("input_dim")
        cond_dim = config.get("cond_dim", 2)
        latent_dim = config.get("latent_dim", 16)
        hidden_dim = config.get("hidden_dim", 128)

        if input_dim is None:
            raise ValueError("CVAE checkpoint missing input_dim in config")

        self.model = CompositionCVAE(
            input_dim=input_dim,
            cond_dim=cond_dim,
            latent_dim=latent_dim,
            hidden_dim=hidden_dim,
        ).to(self.device)

        state = ckpt.get("model_state_dict")
        if state is None:
            raise ValueError("CVAE checkpoint missing 'model_state_dict'")

        # 如果结构不完全一致，load_state_dict 可能报错，外层调用需捕获异常。
        self.model.load_state_dict(state)
        self.model.eval()

        meta = ckpt.get("meta", {})
        elements: Sequence[str] = meta.get("elements", [])
        if not elements:
            raise ValueError("CVAE checkpoint meta['elements'] is empty")
        self.elements: List[str] = list(elements)

        self.scaler = joblib.load(self.scaler_path)

    def _build_cond_vector(
        self,
        target_strength: Sequence[float] | None,
        target_elongation: Sequence[float] | None,
    ) -> np.ndarray:
        """
        把目标区间转换为 2 维 cond（Rm_center, A_center），再用 scaler 归一化。
        """
        if target_strength and len(target_strength) == 2:
            rm_center = float((target_strength[0] + target_strength[1]) / 2.0)
        else:
            rm_center = 1000.0

        if target_elongation and len(target_elongation) == 2:
            a_center = float((target_elongation[0] + target_elongation[1]) / 2.0)
        else:
            a_center = 15.0

        cond_raw = np.array([[rm_center, a_center]], dtype=np.float32)
        cond_scaled = self.scaler.transform(cond_raw)
        return cond_scaled[0]

    def sample_compositions(
        self,
        constraints: Dict[str, Sequence[float]],
        target_strength: Sequence[float] | None,
        target_elongation: Sequence[float] | None,
        n_samples: int = 100,
    ) -> List[Dict[str, float]]:
        """
        根据约束和目标，从 CVAE 采样多组成分。
        """
        cond_vec = self._build_cond_vector(target_strength, target_elongation)
        cond_tensor = torch.tensor(cond_vec, dtype=torch.float32, device=self.device)

        x = self.model.sample(cond_tensor, n_samples=n_samples)  # [n_samples, input_dim]
        x_np = x.cpu().numpy()

        results: List[Dict[str, float]] = []

        for i in range(n_samples):
            vec = x_np[i]
            comp: Dict[str, float] = {}

            # 原训练时 elements 的顺序与 input_dim 对齐
            for idx, ele in enumerate(self.elements):
                val = float(vec[idx])
                # 限制在 [0, +inf) 避免出现明显负值
                if math.isnan(val) or math.isinf(val):
                    val = 0.0
                if val < 0:
                    val = 0.0

                min_v, max_v = constraints.get(ele, [0.0, 0.0])
                # 若 max_v 为 0，说明前端不希望此元素出现
                if max_v <= 0:
                    val = 0.0
                else:
                    # 把模型输出映射到 [min_v, max_v] 区间
                    # 这里使用一个简单的线性缩放：先 sigmoid，再缩放到区间
                    scaled = 1.0 / (1.0 + math.exp(-val))
                    val = min_v + (max_v - min_v) * scaled

                comp[ele] = round(val, 3)

            results.append(comp)

        return results

