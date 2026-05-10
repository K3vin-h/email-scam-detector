"""
dataset.py — Wraps our email data in a format PyTorch understands.

PyTorch needs data delivered in a specific way during training.
Rather than loading everything at once, it asks for one sample at a time
via a "Dataset" object. Think of it like a music library app: you hand it
a playlist object, and it asks for "track 42" or "how many tracks?" on demand.
"""
import torch
from torch.utils.data import Dataset


# ── What is Dataset? ──────────────────────────────────────────────────────────
# torch.utils.data.Dataset is a base class (a template). We inherit from it
# and fill in two required methods:
#
#   __len__      → "how many samples total?"
#   __getitem__  → "give me sample number N"
#
# PyTorch's DataLoader (used in train.py) calls these automatically to build
# batches, shuffle data, and run multiple samples in parallel.
class SpamDataset(Dataset):
    def __init__(self, features, labels):
        """
        features : 2D array, shape (num_emails, num_tfidf_features)
                   Each row is one email expressed as TF-IDF numbers.
        labels   : 1D array of 0s and 1s  (0 = legit, 1 = scam)
        """
        # ── What is a tensor? ─────────────────────────────────────────────────
        # A PyTorch tensor is like a Python list or NumPy array, but with two
        # superpowers: (1) PyTorch can do math on it extremely fast, and
        # (2) it can live on a GPU. Every piece of data in PyTorch must be
        # a tensor before the model can touch it.
        #
        # dtype=torch.float32 means each number is stored as a 32-bit float.
        # Neural networks work in float32 by convention — it's precise enough
        # and fast to compute.

        #the email features are converted to tensors via TF-IDF. TF is term frequency which is number of times term t appears in document d/ total terms in document d. IDF is the natural log of the total number of documents / number of documents containing term t.
        self.X = torch.tensor(features, dtype=torch.float32)

        # ── Why unsqueeze(-1)? ────────────────────────────────────────────────
        # Our labels are a flat list: [0, 1, 0, 1, ...]  → shape (N,)
        # But our model outputs one number PER email in shape (N, 1).
        # They need to match for the loss function to compare them.
        # unsqueeze(-1) adds a dimension at the end: (N,) → (N, 1).
        
        #since the label is either 0, 1 it doesnt fit the Neural Network requirements of a 2D array as seen with tensors X, hence we have to add a dimension. We add the dimension at the end because our model outputs one number per email, (total number of emails, email #1), (total number of emails, email #2), etc.
        self.y = torch.tensor(labels, dtype=torch.float32).unsqueeze(-1)

    def __len__(self):
        # PyTorch calls this to know the total dataset size.
        return len(self.y)

    def __getitem__(self, idx):
        # PyTorch calls this with a specific index to fetch one sample.
        # Returns a (features_tensor, label_tensor) pair for one email.
        return self.X[idx], self.y[idx]
