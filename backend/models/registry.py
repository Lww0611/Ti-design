class ModelRegistry:
    _models = {}
    _aliases = {
        "MiniLM-XGBoost-Dual-v2": "MiniLM-XGBoost-Dual-v2",
        "BERT-XGB-v2": "MiniLM-XGBoost-Dual-v2",
        "BERT-Tabular-v3": "BERT-Tabular-v3",
        "BERT-v3": "BERT-Tabular-v3",
        "MatSciBERT-XGBoost-Dual-v1": "MatSciBERT-XGBoost-Dual-v1",
        "MatSciBERT-XGB": "MatSciBERT-XGBoost-Dual-v1",
    }

    @classmethod
    def get_model(cls, name: str):
        canonical = cls._aliases.get(name, name)
        if canonical not in cls._models:
            if canonical == "MiniLM-XGBoost-Dual-v2":
                from models.forward.bert_xgb_v2_model import BertXGBV2Model
                cls._models[canonical] = BertXGBV2Model()
            elif canonical == "BERT-Tabular-v3":
                from models.forward.bert_v3_model import BertV3Model
                cls._models[canonical] = BertV3Model()
            elif canonical == "MatSciBERT-XGBoost-Dual-v1":
                from models.forward.matscibert_xgb_model import MatSciBERTXGBModel
                cls._models[canonical] = MatSciBERTXGBModel()

        return cls._models.get(canonical)

    @classmethod
    def list_models(cls):
        return [
            "MiniLM-XGBoost-Dual-v2",
            "BERT-Tabular-v3",
            "MatSciBERT-XGBoost-Dual-v1",
        ]