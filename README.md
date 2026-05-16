# Scam Email Filter

## Machine Learning Pipeline

The machine learning model is a neural network created using the pytorch framework. The model is trained on a dataset of scam and legit emails.

### Dataset Preparation

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

### Neural Network Architecture

The neural network is made up of 3 layers. 
Layer 1: converts TF-IDF vectors to 256 dimensional vectors
The converted 256 dimensional vectors are multiplied by weights then added together. The weights start as random and then slowly adjust as the model is trained.
The result of the first layer are fed into a [ReLU](#relu-rectified-linear-unit) function.
Afterwards, dropout is applied to the neural network, which randomly excludes 30% of neurons. This prevents the model from overfitting and reduces over reliance on certain neurons.

Layer 2: same as layer 1 but converting 256 dimensional vectors to 64 dimensional vectors.

Layer 3: same as layer 1 and 2 but converting 64 dimensional vectors to 1 dimensional vectors.

The final number is fed into a Sigmoid function, which turns the number into a probability between 0 and 1. We use the sigmoid function because it converts the numbers into a probability between 0 and 1. Where 0 is least likely to be a scam and 1 is most likely to be a scam.

<details>
<summary><strong>ReLU (Rectified Linear Unit)</strong></summary>

ReLU is an activation function applied after each layer. It turns any negative number to 0 and leaves positive numbers unchanged. This lets the network learn non-linear patterns.

$$ReLU(x) = \max(0,\ x)$$

For any input below 0, the output is 0. For any input above 0, the output equals the input.

![Graph showing ReLU output: flat at 0 for all negative inputs, then rising linearly for positive inputs](image.png)    

**Source:** GeeksforGeeks — [ReLU Activation Function in Deep Learning](https://www.geeksforgeeks.org/deep-learning/relu-activation-function-in-deep-learning/)

</details>

## Training Process

The hyperparameters are set to the following values:
- Epochs: 10
- Batch size: 64
- Learning rate: 0.001
- Max features: 10,000 - how many words the model will track

The data set is split into 3 sets: train, validation, and test. This prevents the model from memorising the dataset. 

The loss function is Binary Cross Entropy Loss. This measures the difference between the predicted probability and the actual label. A loss of 0 means the model is perfect. A higher loss means the model is wrong. Then backpropogation occurs, where weights are adjusted to reduce loss. 

Adam optimiser is used to update the weights, we use adam since our model does not need much tuning and adam is able to quickly adjust to the loss.

The outputs are saved to vectorized.pkl for the vocabulary vectorizer and model.pt for the trained model.

## Evaluation
We use new data sets that the model has not seen before to evaluate its performance. These data sets are not used in the training, validation, or test sets. The model gets scored on three main metrics:
- Precision: Measures the proportion of positive identifications that were actually correct. High precision means the model rarely flags legitimate emails as scams.
- Recall: Measures the proportion of actual positives that were correctly identified. High recall means the model catches most of the actual scams.
- F1 score: The harmonic mean of precision and recall, providing a single score that balances both.

The f1 score of the model currently sits at 0.9655.


## Backend

Django is used for backend for this project, the uses consist of:
1. Models: defines the data models for where to store and retrieve data such as the emails, labels, and login credentials.
2. Views: handles the REST API calls from the front end, such as getting the email contents or applying a label
3. URLs: delegates requests to the correct view


### OAuth

The app uses OAuth to access the user's Gmail account. This allows the user to grant the app permission to access their emails without giving away their Gmail password.

When the user connects their Gmail account, the app redirects them to the Google permission screen to allow access to their emails. Then Google redirects the user back to
the app with a temporary authorization code. The backend exchanges this temporary code for an access token and a refresh token.

The access token is used to access the user's email. The refresh token is used to get new access tokens when the current access token expires. The refresh and access
tokens are stored locally in `token.json`.

### App Scopes

- `https://www.googleapis.com/auth/gmail.readonly`: Allows the app to read the user's emails.
- `https://www.googleapis.com/auth/gmail.labels`: Allows the app to read and manage Gmail labels.
- `https://www.googleapis.com/auth/gmail.modify`: Allows the app to modify Gmail messages, such as applying labels.

### Callback Routes

1. `/auth/gmail/`: Starts the OAuth login flow and redirects the user to Google.
2. `/auth/callback/`: Receives the response from Google after the user approves access, exchanges the authorization code for tokens, and saves them in `token.json`.

### Redirect URL

The redirect URL is:

`http://localhost:8000/auth/callback/`
