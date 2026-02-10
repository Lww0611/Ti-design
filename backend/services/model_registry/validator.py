def validate_metadata_against_dataset(
    features: list[str],
    target: str,
    dataset_columns: list[str],
):
    missing_features = set(features) - set(dataset_columns)
    if missing_features:
        raise ValueError(f"Missing features in dataset: {missing_features}")

    if target not in dataset_columns:
        raise ValueError(f"Target '{target}' not found in dataset")
