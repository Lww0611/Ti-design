class ModelRegistry:
    _models = {}

    @classmethod
    def get_model(cls, name: str):
        if name not in cls._models:
            if name == "XGBoost":
                from models.forward.xgboost_model import XGBoostModel
                cls._models[name] = XGBoostModel()

            elif name == "RandomForest":
                from models.forward.rf_model import RandomForestModel
                cls._models[name] = RandomForestModel()

            elif name == "BERT-XGB-v2":
                from models.forward.bert_xgb_v2_model import BertXGBV2Model
                cls._models[name] = BertXGBV2Model()

        return cls._models.get(name)

    @classmethod
    def list_models(cls):
        return ["XGBoost", "RandomForest", "BERT-XGB-v2"]