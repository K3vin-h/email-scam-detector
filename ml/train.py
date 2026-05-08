"""
train.py — Trains the scam classifier end-to-end.

Run: python -m ml.train

What this script does step-by-step:
  1. Load emails.csv  (built by download_data.py)
  2. Turn email text into numbers with TF-IDF
  3. Split into train / validation / test sets
  4. Build the neural network
  5. Loop through training data many times (epochs), updating weights each time
  6. After each epoch, check performance on the validation set
  7. Save the best model and the vectorizer to disk
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader

from ml.dataset import SpamDataset
from ml.model import ScamClassifier

PROCESSED_DIR = Path("data/processed")
ML_DIR = Path("ml")

# ── Hyperparameters ───────────────────────────────────────────────────────────
# These are settings the programmer chooses (not learned by the network).
# They control HOW training happens, not WHAT the network learns.
EPOCHS = 10           # How many full passes through the training data
BATCH_SIZE = 64       # How many emails to process together before updating weights
LEARNING_RATE = 1e-3  # How large a step to take when adjusting weights
MAX_FEATURES = 10_000 # Maximum number of words to track in the TF-IDF vocabulary


def load_and_split(csv_path: Path):
    """
    Load emails.csv and split into train / validation / test sets.

    Why three splits?
    - Train   (70%): the model sees and learns from this data
    - Val     (15%): we check progress here after each epoch, but never train on it
    - Test    (15%): used ONCE at the very end; gives an honest accuracy estimate

    We need separate splits because a model that is tested on its own training
    data will look unrealistically good — it has essentially memorised the answers.
    """
    df = pd.read_csv(csv_path).dropna(subset=["text"])
    df = df[df["text"].str.strip() != ""]

    X = df["text"].tolist()
    y = df["label"].values

    # stratify=y ensures each split has the same spam/ham ratio as the full dataset.
    # random_state=42 makes the split reproducible — same split every run.
    X_train, X_rest, y_train, y_rest = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_rest, y_rest, test_size=0.50, random_state=42, stratify=y_rest
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def build_tfidf(texts_train: list[str]) -> tuple[TfidfVectorizer, np.ndarray]:
    """
    Fit a TF-IDF vectorizer on training text and transform it to numbers.

    TF-IDF (Term Frequency-Inverse Document Frequency):
    - Each email becomes a row of numbers, one per vocabulary word.
    - Words rare in general but common in this email get high scores.
    - Common words like "the" or "and" get very low scores.

    This gives the model numerical features it can actually learn from.
    We fit ONLY on training data to avoid letting the model "peek" at test words.
    """
    # sublinear_tf=True applies log scaling to term frequencies,
    # so a word appearing 100 times isn't weighted 100x more than one appearing once.
    vectorizer = TfidfVectorizer(max_features=MAX_FEATURES, sublinear_tf=True)
    X_train = vectorizer.fit_transform(texts_train).toarray()
    return vectorizer, X_train


def run_epoch(model, loader, criterion, optimizer) -> tuple[float, float]:
    """
    One training epoch: loop over all batches, compute loss, update weights.
    Returns (average_loss, accuracy).
    """
    # model.train() enables training-only behaviours (e.g. Dropout is active).
    model.train()
    total_loss, correct, total = 0.0, 0, 0

    for X_batch, y_batch in loader:
        # ── Forward pass ──────────────────────────────────────────────────────
        # Run the batch through the network to get predictions (probabilities).
        predictions = model(X_batch)

        # ── Compute loss ──────────────────────────────────────────────────────
        # BCELoss (Binary Cross-Entropy Loss) measures how far predictions are
        # from the true labels. 0 = perfect prediction, higher = more wrong.
        loss = criterion(predictions, y_batch)

        # ── Backward pass ─────────────────────────────────────────────────────
        # zero_grad() clears old gradient calculations (they accumulate otherwise).
        # loss.backward() tells PyTorch to calculate: "which weights caused this
        # error, and by how much?" — this is backpropagation.
        # optimizer.step() uses those gradients to nudge each weight slightly
        # in the direction that reduces loss.
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        correct += (predictions.round() == y_batch).sum().item()
        total += len(y_batch)

    return total_loss / len(loader), correct / total


def evaluate(model, loader, criterion) -> tuple[float, float]:
    """
    Evaluate model on a dataset without updating any weights.
    Used to check validation performance after each epoch.
    """
    # model.eval() disables Dropout — we want consistent, deterministic output.
    # torch.no_grad() skips gradient tracking, saving memory and time.
    model.eval()
    total_loss, correct, total = 0.0, 0, 0

    with torch.no_grad():
        for X_batch, y_batch in loader:
            predictions = model(X_batch)
            total_loss += criterion(predictions, y_batch).item()
            correct += (predictions.round() == y_batch).sum().item()
            total += len(y_batch)

    return total_loss / len(loader), correct / total


def main():
    print("Loading dataset...")
    X_train_raw, X_val_raw, X_test_raw, y_train, y_val, y_test = load_and_split(
        PROCESSED_DIR / "emails.csv"
    )
    print(f"  Train: {len(y_train):,}   Val: {len(y_val):,}   Test: {len(y_test):,}")

    print("\nBuilding TF-IDF features...")
    vectorizer, X_train = build_tfidf(X_train_raw)
    # Transform val/test with the SAME vocabulary (never re-fit on them).
    X_val = vectorizer.transform(X_val_raw).toarray()
    X_test = vectorizer.transform(X_test_raw).toarray()
    print(f"  Vocabulary size: {X_train.shape[1]:,} features per email")

    # Save the test set so evaluate.py can use it without re-splitting.
    np.save(PROCESSED_DIR / "X_test.npy", X_test)
    np.save(PROCESSED_DIR / "y_test.npy", y_test)

    # ── DataLoaders ───────────────────────────────────────────────────────────
    # DataLoader wraps a Dataset and handles batching + shuffling automatically.
    # shuffle=True on training ensures the model sees data in a different order
    # each epoch, preventing it from learning spurious ordering patterns.
    train_loader = DataLoader(SpamDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(SpamDataset(X_val, y_val), batch_size=BATCH_SIZE)

    # ── Model setup ───────────────────────────────────────────────────────────
    model = ScamClassifier(input_dim=X_train.shape[1])

    # BCELoss is the standard loss function for binary (yes/no) classification.
    criterion = nn.BCELoss()

    # Adam optimizer: adjusts weights after each batch.
    # It's an improved gradient descent that adapts the learning rate
    # automatically — a safe default that works well in most situations.
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # ── Training loop ─────────────────────────────────────────────────────────
    print(f"\nTraining for {EPOCHS} epochs  (batch size={BATCH_SIZE})...")
    print(f"{'Epoch':>5}  {'Train Loss':>10}  {'Train Acc':>9}  {'Val Loss':>8}  {'Val Acc':>7}")
    print("-" * 50)

    best_val_loss = float("inf")

    for epoch in range(1, EPOCHS + 1):
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc = evaluate(model, val_loader, criterion)

        print(f"{epoch:>5}  {train_loss:>10.4f}  {train_acc:>8.1%}  {val_loss:>8.4f}  {val_acc:>6.1%}")

        # Save model only when validation loss improves — this gives us the
        # best checkpoint, not just the final state at epoch 10.
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), ML_DIR / "model.pt")

    print(f"\nBest val loss: {best_val_loss:.4f} — model saved to ml/model.pt")

    # Save the fitted vectorizer so predict.py uses the exact same vocabulary.
    with open(ML_DIR / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    print("Vectorizer saved to ml/vectorizer.pkl")
    print("\nRun `python -m ml.evaluate` to see test-set metrics.")


if __name__ == "__main__":
    main()
