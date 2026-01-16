from models.forward.xgboost_model import XGBoostModel
from models.forward.rf_model import RandomForestModel
from models.forward.bert_model import BertRegressionModel


class ModelRegistry:
    """
    模型注册与调度中心
    """

    _models = {
        "XGBoost": XGBoostModel(),
        "RandomForest": RandomForestModel(),
        "BERT-Regression": BertRegressionModel(),
    }

    @classmethod
    def get_model(cls, name: str):
        return cls._models.get(name)

    @classmethod
    def list_models(cls):
        return list(cls._models.keys())
