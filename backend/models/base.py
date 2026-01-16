from abc import ABC, abstractmethod


class BaseModel(ABC):
    """
    所有预测模型的统一接口
    """

    name: str = "base"

    @abstractmethod
    def predict(self, payload: dict) -> dict:
        """
        输入统一特征字典，输出预测结果
        """
        pass
