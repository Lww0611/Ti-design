import math
from typing import Dict, List, Sequence, Tuple

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

    @staticmethod
    def _three_centers(lo: float, hi: float) -> List[float]:
        """在 [lo,hi] 上取端点与中点；区间极窄时退化为单点。"""
        if hi < lo:
            lo, hi = hi, lo
        if hi - lo < 1e-3:
            return [(lo + hi) / 2.0]
        return [lo, (lo + hi) / 2.0, hi]

    def _cond_centers_grid(
        self,
        target_strength: Sequence[float] | None,
        target_elongation: Sequence[float] | None,
    ) -> List[Tuple[float, float]]:
        """
        在用户给定的 Rm、A 目标区间上取网格中心（最多 3×3）。
        单一中心时 CVAE 条件变化弱，滑块几乎不改变采样分布；网格让目标范围真正参与条件生成。
        """
        if target_strength and len(target_strength) == 2:
            r0, r1 = float(target_strength[0]), float(target_strength[1])
            rm_pts = self._three_centers(r0, r1)
        else:
            rm_pts = [1000.0]

        if target_elongation and len(target_elongation) == 2:
            a0, a1 = float(target_elongation[0]), float(target_elongation[1])
            a_pts = self._three_centers(a0, a1)
        else:
            a_pts = [15.0]

        return [(r, a) for r in rm_pts for a in a_pts]

    def _scaled_cond_tensor(self, rm_center: float, a_center: float) -> torch.Tensor:
        cond_raw = np.array([[rm_center, a_center]], dtype=np.float32)
        cond_scaled = self.scaler.transform(cond_raw)[0]
        return torch.tensor(cond_scaled, dtype=torch.float32, device=self.device)

    def _decoder_rows_to_compositions(
        self,
        x_np: np.ndarray,
        constraints: Dict[str, Sequence[float]],
    ) -> List[Dict[str, float]]:
        n = x_np.shape[0]
        results: List[Dict[str, float]] = []
        for i in range(n):
            vec = x_np[i]
            comp: Dict[str, float] = {}
            for idx, ele in enumerate(self.elements):
                val = float(vec[idx])
                if math.isnan(val) or math.isinf(val):
                    val = 0.0
                if val < 0:
                    val = 0.0

                min_v, max_v = constraints.get(ele, [0.0, 0.0])
                min_v, max_v = float(min_v), float(max_v)
                if max_v <= 0:
                    val = 0.0
                else:
                    scaled = 1.0 / (1.0 + math.exp(-val))
                    val = min_v + (max_v - min_v) * scaled

                comp[ele] = round(val, 3)
            results.append(comp)
        return results

    def sample_compositions(
        self,
        constraints: Dict[str, Sequence[float]],
        target_strength: Sequence[float] | None,
        target_elongation: Sequence[float] | None,
        n_samples: int = 100,
    ) -> List[Dict[str, float]]:
        """
        在目标 Rm×A 区间上网格取多个条件点，分别采样再合并，使前端滑块范围明显影响生成。
        """
        centers = self._cond_centers_grid(target_strength, target_elongation)
        n_centers = len(centers)
        per = max(1, (n_samples + n_centers - 1) // n_centers)

        out: List[Dict[str, float]] = []
        for rm_c, a_c in centers:
            cond_tensor = self._scaled_cond_tensor(rm_c, a_c)
            x = self.model.sample(cond_tensor, n_samples=per)
            out.extend(self._decoder_rows_to_compositions(x.cpu().numpy(), constraints))

        return out[:n_samples]

