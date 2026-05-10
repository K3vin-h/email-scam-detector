"""
model.py — Defines the neural network architecture.

A neural network is a chain of math operations. Data (TF-IDF numbers
representing an email) flows in at the top, gets transformed by each layer,
and a single probability comes out at the bottom:
"how likely is this email to be a scam?" (0.0 = definitely legit, 1.0 = definitely scam)

Each layer holds "weights" — grids of numbers that start random and are
gradually adjusted during training to produce better predictions.
"""
import torch.nn as nn


# ── What is nn.Module? ────────────────────────────────────────────────────────
# nn.Module is PyTorch's base class for all neural networks.
# By inheriting from it, our class automatically gains:
#   - Tracking of all learnable weights (so the optimizer can update them)
#   - Easy saving and loading with torch.save / torch.load
#   - A train() / eval() toggle for training vs. inference behaviour

#we are creating own neural network with the help of pytorch framework
class ScamClassifier(nn.Module):
    def __init__(self, input_dim: int):
        """
        input_dim: the TF-IDF vocabulary size — how many numbers represent
                   each email. Determined by the vectorizer in train.py.
        """
        # Always call super().__init__() first when inheriting from nn.Module.
        # This sets up all of PyTorch's internal bookkeeping.
        super().__init__()

        # ── Layer 1: input_dim numbers → 256 numbers ──────────────────────────
        # nn.Linear(a, b) is a "fully connected" layer.
        # Imagine 256 neurons, each receiving every TF-IDF feature as input.
        # Each neuron multiplies all inputs by its own weights and sums the result.
        # The layer's weights are a grid of (input_dim × 256) numbers — learned during training.

        #converts the TF-IDF vector to a 256 dimensional vector. The inital vector patterns gets turned into 256 dimensional patterns. The 256 patterns are multiplied by weights, then added together. The weights start as random and then slowly adjust as the model is trained.
        self.fc1 = nn.Linear(input_dim, 256)

        # ── ReLU activation ───────────────────────────────────────────────────
        # After a linear layer, numbers can be any value (positive or negative).
        # ReLU (Rectified Linear Unit) simply zeros out negative values: max(0, x).
        #
        # Why? Without a non-linear step like this, stacking multiple linear
        # layers would be mathematically identical to having just one layer —
        # they'd all collapse into a single linear transformation.
        # ReLU breaks that and allows the network to learn curved, complex patterns.

        #turns all negative numbers into 0, or lets them be. f(x) = max(0,x)
        
        self.relu = nn.ReLU()

        # ── Dropout ───────────────────────────────────────────────────────────
        # During training, Dropout randomly zeroes out 30% of neuron outputs.
        # This sounds destructive, but it's a powerful regularisation trick:
        # it prevents the network from "memorising" the training data
        # (called overfitting) by forcing it to learn redundant patterns.
        #
        # During evaluation / prediction, Dropout is automatically disabled
        # (model.eval() takes care of this) so all neurons contribute.
        self.dropout = nn.Dropout(0.3)

        # ── Layer 2: 256 numbers → 64 numbers ────────────────────────────────
        # Narrowing from 256 to 64 compresses the representation.
        # The network must decide which information is most important to keep.
        self.fc2 = nn.Linear(256, 64)

        # ── Output layer: 64 numbers → 1 number ──────────────────────────────
        # The final layer collapses everything into a single value per email.
        # That value is then passed through Sigmoid to become a probability.
        self.fc3 = nn.Linear(64, 1)

        # ── Sigmoid activation ────────────────────────────────────────────────
        # Sigmoid squishes any number into the range [0.0, 1.0]:
        #   sigmoid(x) = 1 / (1 + e^(-x))
        #
        # Large positive numbers → close to 1.0  (very likely scam)
        # Large negative numbers → close to 0.0  (very likely legit)
        # Zero → 0.5 (completely uncertain)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        """
        forward() describes how data moves through the network.
        PyTorch calls this automatically when you write model(some_data).

        x: a batch of emails as TF-IDF tensors, shape (batch_size, input_dim)
        Returns: a tensor of scam probabilities, shape (batch_size, 1)
        """
        # Layer 1 → ReLU → Dropout
        x = self.dropout(self.relu(self.fc1(x)))

        # Layer 2 → ReLU → Dropout
        x = self.dropout(self.relu(self.fc2(x)))

        # Output layer → Sigmoid (produces a probability)
        return self.sigmoid(self.fc3(x))
