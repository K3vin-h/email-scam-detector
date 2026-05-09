# Scam Email Filter

## Machine Learning

The machine learning model is a neural network created using the pytorch framework. The model is trained on a dataset of scam and legit emails.

### Dataset Conversions

The email features (content) is converted into [TF-IDF](#tf-idf-term-frequency-inverse-document-frequency) numerical representations, and then is converted into tensors.

The emails are given a label depending on if it is a scam or not, 1 for scam and 0 for legit. However, the labels are 1D arrays, while the email features are 2D arrays. Hence, an extra dimension is added to the labels to match up with the email features array.

<details>
<summary><strong>TF-IDF (Term Frequency-Inverse Document Frequency)</strong></summary>

TF-IDF is a numerical statistic that reflects how important a word is to a document in a collection or corpus.

**Term Frequency (TF):** Measures how frequently a term appears in a document.

$$TF(t,\ d) = \frac{\text{Number of times term } t \text{ appears in } d}{\text{Total number of terms in } d}$$

**Inverse Document Frequency (IDF):** Measures how important a term is across the corpus.

$$IDF(t,\ D) = \log\left(\frac{\text{Total documents in } D}{\text{Documents containing term } t}\right)$$

**Combined score:**

$$TF\text{-}IDF(t,\ d,\ D) = TF(t,\ d) \times IDF(t,\ D)$$

**Source:** GeeksforGeeks — [Understanding TF-IDF](https://www.geeksforgeeks.org/machine-learning/understanding-tf-idf-term-frequency-inverse-document-frequency/)

</details>

### Neural Network

The neural network is made up of 3 layers. 
Layer 1: converts TF-IDF vectors to 256 dimensional vectors
The converted 256 dimensional vectors are multiplied by weights then added together. The weights start as random and then slowly adjust as the model is trained.
The result of the first layer are fed into a [ReLU](#relu-rectified-linear-unit) function.

<details>
<summary><strong>ReLU (Rectified Linear Unit)</strong></summary>

ReLU is an activation function applied after each layer. It turns any negative number to 0 and leaves positive numbers unchanged. This lets the network learn non-linear patterns.

$$ReLU(x) = \max(0,\ x)$$

For any input below 0, the output is 0. For any input above 0, the output equals the input.

![Graph showing ReLU output: flat at 0 for all negative inputs, then rising linearly for positive inputs](image.png)    

**Source:** GeeksforGeeks — [ReLU Activation Function in Deep Learning](https://www.geeksforgeeks.org/deep-learning/relu-activation-function-in-deep-learning/)

</details>

