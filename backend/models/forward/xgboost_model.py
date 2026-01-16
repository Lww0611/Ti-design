import random
from models.base import BaseModel


class XGBoostModel(BaseModel):
    name = "XGBoost"

    def predict(self, payload: dict) -> dict:
        elements = payload.get("elements", {})
        heat_treatment = payload.get("heatTreatment")

        base_rm = elements.get('Al', 0) * 50 + elements.get('V', 0) * 30 + 600

        ht_factor = 0
        if heat_treatment and heat_treatment.get("enabled"):
            for stage in heat_treatment.get("stages", []):
                if stage.get("temperature", 0) > 800:
                    ht_factor -= 50
                else:
                    ht_factor += 20

        rm = base_rm + ht_factor + random.uniform(-20, 20)
        a = 20 - (rm / 100) + random.uniform(-1, 1)

        return {
            "model": self.name,
            "rm": round(rm, 2),
            "rm_err": 15.0,
            "a": round(max(a, 0), 2),
            "a_err": 1.5
        }
