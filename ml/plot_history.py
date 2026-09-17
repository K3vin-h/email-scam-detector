"""
plot_history.py — Plots training/validation accuracy and loss vs. epoch.

Run: python -m ml.plot_history

Reads ml/training_history.json (written by train.py) and saves a PNG chart
to ml/training_history.png.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

ML_DIR = Path("ml")
HISTORY_PATH = ML_DIR / "training_history.json"
OUTPUT_PATH = ML_DIR / "training_history.png"


def load_history(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(
            f"Training history not found: {path}. Run `python -m ml.train` first."
        ) from exc


def plot_history(history: list[dict], output_path: Path) -> None:
    epochs = [entry["epoch"] for entry in history]
    train_acc = [entry["train_acc"] for entry in history]
    val_acc = [entry["val_acc"] for entry in history]
    train_loss = [entry["train_loss"] for entry in history]
    val_loss = [entry["val_loss"] for entry in history]

    fig, (ax_acc, ax_loss) = plt.subplots(1, 2, figsize=(12, 5))

    ax_acc.plot(epochs, train_acc, label="Train Accuracy", marker="o")
    ax_acc.plot(epochs, val_acc, label="Val Accuracy", marker="o")
    ax_acc.set_xlabel("Epoch")
    ax_acc.set_ylabel("Accuracy")
    ax_acc.set_title("Accuracy vs. Epoch")
    ax_acc.legend()
    ax_acc.grid(True, alpha=0.3)

    ax_loss.plot(epochs, train_loss, label="Train Loss", marker="o")
    ax_loss.plot(epochs, val_loss, label="Val Loss", marker="o")
    ax_loss.set_xlabel("Epoch")
    ax_loss.set_ylabel("Loss")
    ax_loss.set_title("Loss vs. Epoch")
    ax_loss.legend()
    ax_loss.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path)
    print(f"Saved chart to {output_path}")


def main():
    history = load_history(HISTORY_PATH)
    plot_history(history, OUTPUT_PATH)


if __name__ == "__main__":
    main()
