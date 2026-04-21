"""
Few-shot examples for MAANG-level MCQ generation.

User-provided gold standards for each category that define the quality benchmark.

TODO: USER MUST PROVIDE 30 EXAMPLES (10 per category) BEFORE IMPLEMENTATION CAN PROCEED.

Template for each example:
{
    "question": "The actual question text",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_answer": "B",  # A, B, C, or D
    "explanation": "Brief explanation (2-4 lines)",
    "category": "Conceptual",  # or Mathematical or Application
    "quality_notes": "What makes this a good MAANG-level question"
}
"""

import random
from typing import List


# ====================================================================
# CONCEPTUAL EXAMPLES (50% of questions)
# ====================================================================
# Focus on: Trade-offs, assumptions, failure cases, comparisons, limitations
# NOT: Simple definitions, fact recall
# Examples: "Why would X fail?", "When is Y preferred over Z?"

CONCEPTUAL_EXAMPLES = [
    {
        "question": "Why might a model with 99% accuracy still fail in production?",
        "option_a": "The model was trained on insufficient data",
        "option_b": "The dataset has severe class imbalance (99% negative class)",
        "option_c": "The model architecture is too simple",
        "option_d": "The learning rate was set too high during training",
        "correct_answer": "B",
        "explanation": "High accuracy can be misleading with imbalanced datasets. A naive classifier that always predicts the majority class achieves 99% accuracy but fails to detect the 1% minority class, rendering it useless in production.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of metric limitations and production trade-offs, not just accuracy as a metric"
    },
    {
        "question": "According to the Central Limit Theorem, as sample size increases, what happens?",
        "option_a": "The population becomes normally distributed",
        "option_b": "The sampling distribution of the mean approaches normality",
        "option_c": "The variance of the population becomes zero",
        "option_d": "The sample mean equals the population mean exactly",
        "correct_answer": "B",
        "explanation": "CLT states that regardless of population distribution, the sampling distribution of the mean approaches normality with sufficient sample size. This doesn't change the population distribution itself or guarantee exact equality of means.",
        "category": "Conceptual",
        "quality_notes": "Tests deep understanding of CLT's implications, distinguishing between population and sampling distributions"
    },
    {
        "question": "As model complexity increases while holding data fixed, what is the expected behavior?",
        "option_a": "Bias decreases and variance increases",
        "option_b": "Both bias and variance decrease",
        "option_c": "Bias increases and variance decreases",
        "option_d": "Both increase",
        "correct_answer": "A",
        "explanation": "More complex models fit training data better (lower bias) but become more sensitive to specific training samples (higher variance). This fundamental tradeoff governs the risk of overfitting as model capacity increases.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of bias-variance tradeoff as core ML principle"
    },
    {
        "question": "Which of the following violates a critical assumption of linear regression?",
        "option_a": "Homoscedastic residuals",
        "option_b": "Independent errors",
        "option_c": "Perfect multicollinearity among predictors",
        "option_d": "Linear relationship between X and Y",
        "correct_answer": "C",
        "explanation": "Perfect multicollinearity (when predictors are perfectly correlated) makes the design matrix singular, preventing unique coefficient estimation. Options A, B, and D are requirements, not violations.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of regression assumptions and why they matter for inference"
    },
    {
        "question": "Rejecting a true null hypothesis corresponds to which type of error?",
        "option_a": "Type II error",
        "option_b": "False negative",
        "option_c": "True positive",
        "option_d": "Type I error",
        "correct_answer": "D",
        "explanation": "Type I error (false positive) occurs when we reject H0 when it's actually true. Type II error (false negative) is failing to reject a false H0. Understanding this distinction is critical for hypothesis testing and significance level selection.",
        "category": "Conceptual",
        "quality_notes": "Tests statistical inference fundamentals with error type classification"
    },
    {
        "question": "In PCA, what do eigenvalues represent?",
        "option_a": "Correlation between original variables",
        "option_b": "Direction vectors of principal components",
        "option_c": "Variance explained by each principal component",
        "option_d": "Noise magnitude in the data",
        "correct_answer": "C",
        "explanation": "Eigenvalues quantify variance captured by each principal component. Larger eigenvalues indicate directions of greater variance. Eigenvectors (not eigenvalues) provide directions, and correlation is captured in the covariance matrix.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of PCA mathematical foundations and eigenvalue interpretation"
    },
    {
        "question": "A binary classifier has ROC-AUC = 0.5. What does this indicate about model performance?",
        "option_a": "Perfect classifier",
        "option_b": "Severe overfitting",
        "option_c": "Performance equivalent to random guessing",
        "option_d": "50% accuracy",
        "correct_answer": "C",
        "explanation": "AUC=0.5 means the model cannot distinguish between classes better than random chance. AUC=1.0 is perfect, AUC<0.5 suggests inverted predictions. Note that 50% accuracy ≠ random guessing for imbalanced datasets.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of ROC-AUC as a threshold-independent performance metric"
    },
    {
        "question": "What is the primary effect of L2 regularization on model weights?",
        "option_a": "Drops irrelevant features to exactly zero",
        "option_b": "Shrinks coefficients smoothly toward zero",
        "option_c": "Increases model variance",
        "option_d": "Makes the loss function non-convex",
        "correct_answer": "B",
        "explanation": "L2 regularization (Ridge) penalizes large weights, shrinking them toward (but rarely to) zero. L1 (Lasso) drives weights to exactly zero for sparsity. L2 reduces variance by constraining model capacity.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of regularization mechanisms and L1 vs L2 differences"
    },
    {
        "question": "What is the primary purpose of a held-out test set in machine learning?",
        "option_a": "Hyperparameter tuning",
        "option_b": "Feature engineering experimentation",
        "option_c": "Final unbiased evaluation of model generalization",
        "option_d": "Training optimization",
        "correct_answer": "C",
        "explanation": "The test set provides an unbiased estimate of generalization performance on unseen data. Using it for tuning (A) or feature engineering (B) contaminates the evaluation, causing overfitting to the test set itself.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of train/validation/test split purposes and data leakage risks"
    },
    {
        "question": "Why is k-fold cross-validation preferred over a single train-test split for model evaluation?",
        "option_a": "It reduces computation time",
        "option_b": "It gives lower training error",
        "option_c": "It provides a more reliable estimate of generalization error",
        "option_d": "It increases model complexity",
        "correct_answer": "C",
        "explanation": "K-fold CV averages performance across k different train/test splits, reducing variance in the generalization estimate compared to a single split. This is especially important for small datasets where a single split may be unrepresentative.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of cross-validation's statistical benefits over holdout validation"
    },
    {
        "question": "When is PCA MOST appropriate as a preprocessing technique?",
        "option_a": "When features are highly correlated and dimensionality reduction is needed",
        "option_b": "When data is fully labeled for supervised learning",
        "option_c": "When you need non-linear feature transformations",
        "option_d": "When you want to increase dimensionality for better expressiveness",
        "correct_answer": "A",
        "explanation": "PCA is most effective when features exhibit high correlation (redundancy), allowing variance capture in fewer dimensions. It's a linear transformation, doesn't require labels, and reduces (not increases) dimensionality.",
        "category": "Conceptual",
        "quality_notes": "Tests understanding of PCA's use case and when it provides the most benefit"
    }
]

# ====================================================================
# MATHEMATICAL EXAMPLES (25% of questions)
# ====================================================================
# Focus on: Quantitative intuition, probability reasoning, gradient understanding
# NOT: Long derivations, brute-force computation
# Examples: "What does this gradient mean?", "If P(A|B)=0.7, interpret this"

MATHEMATICAL_EXAMPLES = [
    {
        "question": "If a logistic regression model outputs P(y=1|x) = 0.7, what does this represent?",
        "option_a": "70% of training samples belong to class 1",
        "option_b": "The model is 70% confident this specific instance belongs to class 1",
        "option_c": "The model will misclassify 30% of instances",
        "option_d": "The decision boundary is at x = 0.7",
        "correct_answer": "B",
        "explanation": "Logistic regression outputs class probabilities for individual instances based on their features, not global statistics about the dataset or decision boundary values. P(y=1|x)=0.7 means the model predicts a 70% probability that this specific input x belongs to class 1.",
        "category": "Mathematical",
        "quality_notes": "Tests mathematical intuition of probability interpretation in ML context, not formula memorization"
    },
    {
        "question": "A dataset's covariance matrix has eigenvalues: 5, 3, 2. What percentage of total variance is captured by the first two principal components?",
        "option_a": "50%",
        "option_b": "80%",
        "option_c": "90%",
        "option_d": "60%",
        "correct_answer": "B",
        "explanation": "Total variance = 5+3+2 = 10. First two components capture 5+3 = 8. Variance explained = 8/10 = 80%. This tests understanding of eigenvalue interpretation in PCA.",
        "category": "Mathematical",
        "quality_notes": "Tests quantitative reasoning about variance decomposition in PCA, not just formula recall"
    },
    {
        "question": "For softmax function s(z_i) = e^(z_i) / Σ_j e^(z_j), which statement is true?",
        "option_a": "Multiplying all logits by a scalar leaves softmax unchanged",
        "option_b": "Adding the same constant to all logits leaves softmax unchanged",
        "option_c": "Applying ReLU before softmax gives the same result",
        "option_d": "Softmax outputs can be negative",
        "correct_answer": "B",
        "explanation": "Adding a constant c to all logits: e^(z_i+c) = e^c · e^(z_i). The e^c factor appears in both numerator and denominator, canceling out. This invariance property is crucial for numerical stability in implementations.",
        "category": "Mathematical",
        "quality_notes": "Tests deep understanding of softmax mathematical properties and numerical stability implications"
    },
    {
        "question": "Which identity correctly relates cross-entropy H(p,q) and KL divergence KL(p||q)?",
        "option_a": "H(p,q) = KL(p||q) − H(p)",
        "option_b": "H(p,q) = KL(p||q) + H(p)",
        "option_c": "H(p,q) = H(q) + KL(q||p)",
        "option_d": "KL(p||q) = H(q) − H(p)",
        "correct_answer": "B",
        "explanation": "Cross-entropy decomposes as H(p,q) = H(p) + KL(p||q), where H(p) is entropy of true distribution and KL term measures extra bits needed when using q instead of p. This fundamental relationship connects information theory to ML loss functions.",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of relationship between information-theoretic quantities used in ML"
    },
    {
        "question": "For binary cross-entropy with sigmoid σ(z), the gradient with respect to weights for one sample (x, y) equals:",
        "option_a": "(σ(w·x) − y) x",
        "option_b": "(y − σ(w·x)) x",
        "option_c": "σ(w·x)(1 − σ(w·x)) x",
        "option_d": "(y − w·x) x",
        "correct_answer": "A",
        "explanation": "The elegant gradient (prediction - target) × input arises from the derivative of log-sigmoid canceling with sigmoid's derivative. This simplification is why logistic regression training is computationally efficient.",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of gradient computation and why certain loss-activation combinations are preferred"
    },
    {
        "question": "For a real symmetric covariance matrix, eigenvectors are:",
        "option_a": "Always complex",
        "option_b": "Orthogonal (can be chosen orthonormal)",
        "option_c": "Always linearly dependent",
        "option_d": "Random directions",
        "correct_answer": "B",
        "explanation": "Spectral theorem guarantees real eigenvalues and orthogonal eigenvectors for real symmetric matrices. This property is fundamental to PCA, where orthogonal principal components represent uncorrelated directions of maximum variance.",
        "category": "Mathematical",
        "quality_notes": "Tests linear algebra understanding critical for dimensionality reduction techniques"
    },
    {
        "question": "For quadratic function f(x) = ½x^T Ax (A positive definite), gradient descent converges if:",
        "option_a": "α < 2 / λ_max(A)",
        "option_b": "α > 2 / λ_min(A)",
        "option_c": "α < 1 / λ_min(A)",
        "option_d": "Any α > 0 works",
        "correct_answer": "A",
        "explanation": "Convergence requires step size smaller than 2/λ_max. The largest eigenvalue determines convergence stability because it corresponds to the steepest direction. Too large α causes oscillation or divergence along this direction.",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of optimization theory and why learning rate selection matters"
    },
    {
        "question": "For Bernoulli distribution with parameter p, entropy H(p) = -p log p - (1-p) log(1-p) is maximized at:",
        "option_a": "p = 0",
        "option_b": "p = 0.25",
        "option_c": "p = 0.5",
        "option_d": "p = 1",
        "correct_answer": "C",
        "explanation": "Maximum entropy occurs at p=0.5 (uniform distribution), representing maximum uncertainty. As p approaches 0 or 1, entropy decreases toward 0 (certainty). This principle guides maximum entropy models and regularization.",
        "category": "Mathematical",
        "quality_notes": "Tests information-theoretic intuition about uncertainty quantification in probabilistic models"
    },
    {
        "question": "ROC-AUC (Area Under Receiver Operating Characteristic Curve) equals:",
        "option_a": "Model accuracy",
        "option_b": "Probability that a random positive is ranked above a random negative",
        "option_c": "Precision at threshold 0.5",
        "option_d": "Recall at threshold 0.5",
        "correct_answer": "B",
        "explanation": "AUC has an elegant interpretation: probability that the model ranks a randomly chosen positive example higher than a randomly chosen negative. This makes AUC threshold-independent and robust to class imbalance.",
        "category": "Mathematical",
        "quality_notes": "Tests deep understanding of ranking metrics beyond surface-level accuracy"
    },
    {
        "question": "K-means clustering minimizes:",
        "option_a": "Between-cluster variance",
        "option_b": "Within-cluster sum of squared distances",
        "option_c": "Total pairwise distances",
        "option_d": "Classification error",
        "correct_answer": "B",
        "explanation": "K-means minimizes Σ_k Σ_{x∈C_k} ||x - μ_k||², the sum of squared distances from points to their cluster centers. This is equivalent to maximizing between-cluster variance, but the algorithm directly optimizes within-cluster compactness.",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of optimization objectives in unsupervised learning"
    },
    {
        "question": "For softmax output layer with cross-entropy loss, the gradient with respect to logits z equals:",
        "option_a": "softmax(z) − y",
        "option_b": "y − softmax(z)",
        "option_c": "softmax(z)(1 − softmax(z))",
        "option_d": "log(softmax(z))",
        "correct_answer": "A",
        "explanation": "The gradient simplifies to (predicted probabilities - one-hot targets), a remarkably clean result. This arises from the derivative of log-softmax canceling with softmax's Jacobian. This simplicity makes softmax+cross-entropy the standard for multi-class classification.",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of why certain loss-activation pairs are computationally preferred"
    },
    {
        "question": "Which matrix decomposition guarantees A = UΣV^T with U and V orthonormal matrices?",
        "option_a": "Eigendecomposition",
        "option_b": "Singular Value Decomposition (SVD)",
        "option_c": "Cholesky decomposition",
        "option_d": "QR decomposition",
        "correct_answer": "B",
        "explanation": "SVD uniquely provides A = UΣV^T where U and V are orthonormal and Σ is diagonal with non-negative entries (singular values). Unlike eigendecomposition, SVD works for any matrix (not just square) and underpins techniques like PCA and recommender systems.",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of matrix factorization methods used in ML dimensionality reduction"
    },
    {
        "question": "As model complexity increases while holding data fixed, the bias-variance tradeoff shows:",
        "option_a": "Bias increases and variance decreases",
        "option_b": "Bias decreases and variance increases",
        "option_c": "Both increase",
        "option_d": "Both decrease",
        "correct_answer": "B",
        "explanation": "More complex models fit training data better (lower bias) but become more sensitive to specific training samples (higher variance). This fundamental tradeoff governs model selection: simple models underfit (high bias), complex models overfit (high variance).",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of the mathematical foundation of overfitting and model capacity"
    },
    {
        "question": "L2 regularization adds which gradient term to the standard loss gradient?",
        "option_a": "λ sign(w)",
        "option_b": "λ w",
        "option_c": "λ / w",
        "option_d": "λ w²",
        "correct_answer": "B",
        "explanation": "L2 penalty λ/2 ||w||² contributes gradient λw (weight decay). This shrinks weights proportionally toward zero during training. L1 (option A) gives λ sign(w) and induces sparsity, while L2 encourages small but non-zero weights.",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of regularization mathematics and its effect on weight updates"
    },
    {
        "question": "Which metric is the harmonic mean of precision and recall?",
        "option_a": "Accuracy",
        "option_b": "F1-score",
        "option_c": "ROC-AUC",
        "option_d": "Log-loss",
        "correct_answer": "B",
        "explanation": "F1 = 2PR/(P+R) is the harmonic mean, which is lower than arithmetic mean and heavily penalizes imbalanced precision/recall. This makes F1 suitable for scenarios requiring balanced performance (e.g., F1=0.18 when P=0.1, R=1.0, showing harmonic mean's sensitivity to low values).",
        "category": "Mathematical",
        "quality_notes": "Tests understanding of metric design and why harmonic mean is preferred for balancing precision-recall"
    }
]

# ====================================================================
# APPLICATION EXAMPLES (25% of questions)
# ====================================================================
# Focus on: Production scenarios, metric trade-offs, debugging, system design
# NOT: Pure theory without context
# Examples: "Model degrades, what's the root cause?", "A/B test shows X, what to do?"

APPLICATION_EXAMPLES = [
    {
        "question": "In a fraud detection system, you have a highly imbalanced dataset where fraudulent transactions constitute less than 1% of the data. The standard cross-entropy loss results in poor recall for the minority class. What is the best approach to improve fraud detection performance?",
        "option_a": "Increase the number of hidden layers to capture more complex patterns",
        "option_b": "Use cost-sensitive loss (Focal Loss) that assigns higher weight to the minority class",
        "option_c": "Downsample the majority class randomly to achieve 50-50 balance",
        "option_d": "Switch to an unsupervised anomaly detection algorithm",
        "correct_answer": "B",
        "explanation": "Cost-sensitive loss functions like Focal Loss down-weight easy examples (majority class) and focus learning on hard examples (minority class), directly addressing class imbalance. Downsampling (C) discards valuable data; increasing complexity (A) doesn't address the imbalance; unsupervised methods (D) lose labeled fraud signals.",
        "category": "Application",
        "quality_notes": "Tests understanding of advanced loss functions for severe class imbalance in production fraud systems"
    },
    {
        "question": "Your recommender system shows declining engagement metrics over time despite stable model accuracy. Investigation reveals that users' preferences have shifted significantly. What is the most effective strategy to address this model drift issue?",
        "option_a": "Increase the model's regularization parameter to prevent overfitting",
        "option_b": "Implement online learning or periodic retraining with recent user interaction data",
        "option_c": "Switch to a simpler model architecture to improve generalization",
        "option_d": "Reduce the learning rate to stabilize predictions",
        "correct_answer": "B",
        "explanation": "Model drift caused by distribution shift requires incorporating recent data to adapt to changing user preferences. Online learning or periodic retraining captures evolving patterns. Options A, C, D address overfitting/generalization but don't solve the temporal drift problem where the data distribution itself has changed.",
        "category": "Application",
        "quality_notes": "Tests understanding of production model drift, temporal distribution shift, and adaptive learning strategies"
    },
    {
        "question": "You're building a text classification model with a vocabulary of 100,000 words. The resulting feature space is extremely sparse and high-dimensional, causing memory issues and slow training. What is the most effective dimensionality reduction strategy?",
        "option_a": "Use pre-trained word embeddings (Word2Vec, GloVe) to map words to dense low-dimensional vectors",
        "option_b": "Apply PCA on the one-hot encoded vocabulary matrix",
        "option_c": "Remove all words that appear more than 1000 times",
        "option_d": "Increase the model's batch size to handle sparsity",
        "correct_answer": "A",
        "explanation": "Pre-trained embeddings convert sparse high-dimensional one-hot vectors into dense low-dimensional semantic representations (e.g., 300D), capturing semantic relationships. PCA (B) on sparse text is computationally infeasible and loses interpretability; removing frequent words (C) loses signal; batch size (D) doesn't reduce dimensionality.",
        "category": "Application",
        "quality_notes": "Tests understanding of NLP-specific dimensionality reduction and when embeddings outperform traditional methods"
    },
    {
        "question": "Your production model serving predictions has strict latency requirements (<50ms per request), but your ensemble of 10 deep neural networks takes 300ms. Accuracy cannot drop below 90% (current: 92%). What is the best optimization strategy?",
        "option_a": "Deploy only the single best-performing model from the ensemble",
        "option_b": "Use knowledge distillation to train a smaller student model that mimics the ensemble",
        "option_c": "Reduce the batch size to process requests faster",
        "option_d": "Remove all dropout layers to speed up inference",
        "correct_answer": "B",
        "explanation": "Knowledge distillation trains a compact student model to replicate the ensemble's soft predictions, maintaining high accuracy with lower latency. Option A risks accuracy drop; C increases latency (batching amortizes overhead); D doesn't significantly reduce inference time and dropout is inactive during inference anyway.",
        "category": "Application",
        "quality_notes": "Tests understanding of model compression, knowledge distillation, and latency-accuracy trade-offs in production systems"
    },
    {
        "question": "You're launching a new recommender system where 80% of users have no historical interaction data (cold start problem). What is the most effective strategy to provide relevant recommendations for these new users?",
        "option_a": "Wait until users accumulate at least 10 interactions before showing recommendations",
        "option_b": "Recommend the globally most popular items across all users",
        "option_c": "Use content-based filtering with user profile attributes (demographics, stated preferences) to make initial recommendations",
        "option_d": "Randomly recommend items to explore user preferences",
        "correct_answer": "C",
        "explanation": "Content-based filtering leverages available user attributes (demographics, explicit preferences) to generate personalized recommendations without interaction history. Option A creates poor user experience; B provides no personalization; D is inefficient compared to using available signals. Hybrid approaches combining B and C are also effective.",
        "category": "Application",
        "quality_notes": "Tests understanding of cold start problem and when to switch from collaborative to content-based filtering"
    },
    {
        "question": "Your time-series forecasting model shows high variance in predictions (large error bars) despite reasonable mean accuracy. You suspect the model is overfitting to training noise. What is the most appropriate regularization technique for sequential models like LSTMs?",
        "option_a": "Increase the learning rate to escape local minima",
        "option_b": "Apply dropout to recurrent connections (recurrent dropout) in addition to standard dropout",
        "option_c": "Remove the validation set and use all data for training",
        "option_d": "Increase the sequence length to capture more patterns",
        "correct_answer": "B",
        "explanation": "Recurrent dropout applies dropout to hidden state connections in LSTMs/GRUs, preventing overfitting while preserving memory across time steps. Standard dropout alone can disrupt temporal dependencies. Options A, C worsen overfitting; D increases model capacity and may worsen the problem.",
        "category": "Application",
        "quality_notes": "Tests understanding of sequence-specific regularization and when standard techniques must be adapted for temporal models"
    },
    {
        "question": "You're building a credit scoring model for loan approval. Regulators require explanations for loan rejections. Your gradient boosted tree model (XGBoost) achieves 88% accuracy, but a logistic regression baseline achieves 82%. What is the best approach to satisfy regulatory requirements without sacrificing too much performance?",
        "option_a": "Use the XGBoost model and provide feature importance scores as explanations",
        "option_b": "Deploy the logistic regression model since it provides interpretable coefficients",
        "option_c": "Use SHAP (SHapley Additive exPlanations) values to provide instance-level explanations for XGBoost predictions",
        "option_d": "Train a neural network with attention mechanisms to visualize decision-making",
        "correct_answer": "C",
        "explanation": "SHAP provides rigorous instance-level explanations for complex models like XGBoost, satisfying regulatory needs without sacrificing the 6% accuracy gain. Global feature importance (A) doesn't explain individual decisions; option B sacrifices performance; D adds complexity without guaranteed interpretability. SHAP is the industry standard for regulated ML.",
        "category": "Application",
        "quality_notes": "Tests understanding of model explainability in regulated domains and the accuracy-interpretability trade-off"
    },
    {
        "question": "Your image classification model trained on clean ImageNet data performs well in validation (92% accuracy) but fails in production (67% accuracy) where images contain label noise, occlusions, and diverse lighting. What is the most effective strategy to improve robustness?",
        "option_a": "Increase model capacity by adding more convolutional layers",
        "option_b": "Apply data augmentation (rotations, brightness/contrast changes, cutout) during training to simulate production conditions",
        "option_c": "Reduce the learning rate to prevent overfitting",
        "option_d": "Use a smaller dataset to train a simpler model",
        "correct_answer": "B",
        "explanation": "Data augmentation exposes the model to variations (noise, occlusions, lighting) it will encounter in production, improving robustness. This directly addresses the train-test distribution mismatch. Options A, C address overfitting (not the issue here); D worsens the problem by reducing training signal.",
        "category": "Application",
        "quality_notes": "Tests understanding of distribution shift, train-test mismatch, and how data augmentation improves real-world robustness"
    },
    {
        "question": "You're fine-tuning a large transformer model (BERT) for text classification, but training is unstable with loss spikes and divergence. You suspect gradient exploding issues. What is the most effective stabilization technique?",
        "option_a": "Increase the batch size to smooth out gradient estimates",
        "option_b": "Apply gradient clipping to cap gradient norms at a maximum threshold",
        "option_c": "Switch to SGD optimizer instead of Adam",
        "option_d": "Remove all normalization layers",
        "correct_answer": "B",
        "explanation": "Gradient clipping prevents exploding gradients by capping gradient norms, a standard technique for training deep transformers. Option A helps but doesn't prevent spikes; C loses Adam's adaptive learning benefits; D worsens instability (layer normalization stabilizes training). Gradient clipping is universally used in transformer training.",
        "category": "Application",
        "quality_notes": "Tests understanding of training stability issues in deep models and transformer-specific optimization techniques"
    },
    {
        "question": "Your A/B test shows a statistically significant 2% improvement in click-through rate (p=0.03) for the treatment group. However, the business team calculates that the operational cost of deploying the new model exceeds the revenue gain from the 2% lift. What is the most appropriate decision?",
        "option_a": "Deploy the model since statistical significance was achieved",
        "option_b": "Do not deploy the model, as statistical significance does not imply business value",
        "option_c": "Run the experiment longer to increase the effect size",
        "option_d": "Deploy to 50% of users to split the difference",
        "correct_answer": "B",
        "explanation": "Statistical significance (p<0.05) confirms the effect is real, but doesn't guarantee business value. If deployment costs exceed revenue gains, the change is not worth implementing. This tests understanding that statistical and practical significance are distinct, and ML decisions must consider ROI, not just statistical metrics.",
        "category": "Application",
        "quality_notes": "Tests understanding of the critical distinction between statistical significance and business value in production ML decisions"
    }
]


# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def get_few_shot_examples(category: str, count: int = 3) -> List[dict]:
    """
    Randomly select N examples from category for prompt injection.
    Rotates examples to prevent LLM overfitting to specific patterns.

    Args:
        category: 'Conceptual', 'Mathematical', or 'Application'
        count: Number of examples to return (default: 3)

    Returns:
        List of example dictionaries
    """
    examples_map = {
        'Conceptual': CONCEPTUAL_EXAMPLES,
        'Mathematical': MATHEMATICAL_EXAMPLES,
        'Application': APPLICATION_EXAMPLES
    }

    pool = examples_map.get(category, [])

    if not pool:
        raise ValueError(f"No examples found for category: {category}. User must provide examples first.")

    # Return random sample (or all if pool smaller than count)
    return random.sample(pool, min(count, len(pool)))


def validate_examples() -> bool:
    """
    Validate that all required examples are provided.

    Returns:
        True if all 30 examples exist (10 per category), False otherwise
    """
    required_per_category = 10

    checks = {
        'Conceptual': len(CONCEPTUAL_EXAMPLES) >= required_per_category,
        'Mathematical': len(MATHEMATICAL_EXAMPLES) >= required_per_category,
        'Application': len(APPLICATION_EXAMPLES) >= required_per_category
    }

    all_valid = all(checks.values())

    if not all_valid:
        print("❌ Few-shot examples incomplete!")
        for category, is_valid in checks.items():
            count = len(eval(f"{category.upper()}_EXAMPLES"))
            status = "✓" if is_valid else "✗"
            print(f"  {status} {category}: {count}/{required_per_category} examples")
        return False

    print("✅ All 30 few-shot examples provided!")
    return True
