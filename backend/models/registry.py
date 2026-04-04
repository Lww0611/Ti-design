class ModelRegistry:
    _models = {}

    @classmethod
    def get_model(cls, name: str):
        if name not in cls._models:
            if name == "BERT-XGB-v2":
                from models.forward.bert_xgb_v2_model import BertXGBV2Model
                cls._models[name] = BertXGBV2Model()
            elif name == "MatSciBERT-XGB":
                from models.forward.matscibert_xgb_model import MatSciBERTXGBModel
                cls._models[name] = MatSciBERTXGBModel()

        return cls._models.get(name)

    @classmethod
    def list_models(cls):
        return ["BERT-XGB-v2", "MatSciBERT-XGB"]