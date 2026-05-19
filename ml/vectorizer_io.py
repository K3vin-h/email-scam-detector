import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def save_vectorizer(vectorizer: TfidfVectorizer, path: Path) -> None:
    """Save the fitted TF-IDF vectorizer without pickle deserialization risk."""
    payload = {
        "version": 1,
        "params": {
            "max_features": vectorizer.max_features,
            "sublinear_tf": vectorizer.sublinear_tf,
            "lowercase": vectorizer.lowercase,
            "ngram_range": vectorizer.ngram_range,
            "stop_words": vectorizer.stop_words,
        },
        "vocabulary": {
            term: int(index) for term, index in vectorizer.vocabulary_.items()
        },
        "idf": vectorizer.idf_.tolist(),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def load_vectorizer(path: Path) -> TfidfVectorizer:
    """Load a fitted TF-IDF vectorizer from the trusted JSON artifact format."""
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"Vectorizer artifact not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Vectorizer artifact is not valid JSON: {path}") from exc

    if payload.get("version") != 1:
        raise RuntimeError("Unsupported vectorizer artifact version.")

    vocabulary = payload.get("vocabulary")
    idf = payload.get("idf")
    params = payload.get("params", {})
    if not isinstance(vocabulary, dict) or not isinstance(idf, list):
        raise RuntimeError("Vectorizer artifact is missing vocabulary or IDF data.")

    vectorizer = TfidfVectorizer(
        vocabulary=vocabulary,
        max_features=params.get("max_features"),
        sublinear_tf=params.get("sublinear_tf", True),
        lowercase=params.get("lowercase", True),
        ngram_range=tuple(params.get("ngram_range", (1, 1))),
        stop_words=params.get("stop_words"),
    )
    vectorizer.fit([""])
    vectorizer.idf_ = np.array(idf, dtype=np.float64)
    return vectorizer
