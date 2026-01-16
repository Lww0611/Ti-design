import random
from models.base import BaseModel
from models.forward.xgboost_model import XGBoostModel


class RandomForestModel(BaseModel):
    name = "RandomForest"

    def predict(self, payload: dict) -> dict:
        base = XGBoostModel().predict(payload)
        base["model"] = self.name
        base["rm"] += random.uniform(-30, 30)
        base["a"] += random.uniform(-2, 2)
        return base
