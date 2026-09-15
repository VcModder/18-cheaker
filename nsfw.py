from pathlib import Path

_model = None


def get_model():
    global _model

    if _model is None:
        from transformers import pipeline

        _model = pipeline(
            "image-classification",
            model="Falconsai/nsfw_image_detection"
        )

    return _model


def is_nsfw(image_path: str, threshold: float = 0.80) -> bool:
    if not Path(image_path).exists():
        return False

    try:
        results = get_model()(image_path)

        for result in results:
            if result["label"].lower() == "nsfw":
                return float(result["score"]) >= threshold

        return False

    except Exception as e:
        print("NSFW error:", e)
        return False
