import pickle


def try_load_model(file_path: str):
    try:
        with open(file_path, "rb") as f:
            model = pickle.load(f)
    except Exception as e:
        raise ValueError(f"Model file cannot be loaded: {e}")

    if not hasattr(model, "predict"):
        raise ValueError("Uploaded object has no predict() method")

    return model
