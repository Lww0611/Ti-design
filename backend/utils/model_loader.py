import pickle
import io

def try_load_model(model_source):
    """
    支持加载二进制流(bytes)或文件路径(str)
    """
    try:
        if isinstance(model_source, bytes):
            # 从内存中读取
            model = pickle.load(io.BytesIO(model_source))
        else:
            # 从磁盘读取（兼容旧数据）
            with open(model_source, "rb") as f:
                model = pickle.load(f)

        if not hasattr(model, "predict"):
            raise ValueError("该对象没有 predict() 方法，不是有效的预测模型")
        return model
    except Exception as e:
        raise ValueError(f"模型解析失败: {str(e)}")