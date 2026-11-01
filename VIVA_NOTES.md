# IntelliConnect — Algorithm Justification (Viva / Project Defense Notes)

## The one-line answer (say this first)

> "This project uses **different algorithms for different sub-problems**, because the six features solve six genuinely different *types* of problems — text classification, structured-data classification, similarity search, statistical anomaly detection, speech recognition, and image analysis. No single algorithm is designed to handle all of these well, so I matched each feature to the technique best suited for it — this is a standard ML engineering practice, not inconsistency."

If she asks for the full list, use the table below.

---

## Full algorithm list, feature by feature

### 1. Intent Detection (NLU) → **TF-IDF + Logistic Regression**
**What it does:** reads the customer's message and classifies it into billing / network / plan_change / sim / cancel / general.

**Why this and not the alternatives:**
- **vs. Naive Bayes** (the classic baseline for text): Naive Bayes assumes every word is independent of every other word, which hurts accuracy when phrases matter (e.g. "cancel my complaint" vs "cancel my account"). Logistic Regression doesn't make that assumption and gives better-calibrated confidence scores — which the UI directly displays as a percentage.
- **vs. SVM:** SVMs are also strong for text, but don't naturally output probabilities (they need extra calibration), and their decision boundary isn't as directly interpretable as LR's weights.
- **vs. a Deep Learning model (LSTM/BERT):** these need thousands of labeled examples and a GPU to train properly. My dataset has ~85 hand-labeled examples — a deep model would badly overfit on that little data. Logistic Regression is the right *scale* of model for this dataset size.

### 2. Predictive Escalation / Churn Risk → **Logistic Regression**
**What it does:** takes sentiment, repeat contacts, tenure, past complaints, and frustration-word count, and predicts the probability that a conversation will escalate.

**Why this and not the alternatives:**
- **vs. Random Forest / XGBoost:** these often score higher on raw accuracy, but they're "black box" models — you can't cleanly say *why* a specific case scored high risk. My project explicitly requires **feature 6, "explainable escalation"** — Logistic Regression's coefficients can be read directly as each factor's contribution to the risk score, which is exactly what the insight panel shows the user. I picked interpretability over a small accuracy gain, deliberately, because explainability was a stated requirement.
- **vs. a Neural Network:** same issue — more opaque, and needs far more data than the ~400 training rows used here.
- **vs. a single Decision Tree:** trees can also be "explained" via their splits, but a single tree is unstable (small data changes can flip the whole tree structure) and gives step-function probabilities rather than the smooth, calibrated probability curve Logistic Regression gives — which matters when you're displaying a 0-100% risk meter.

### 3. Bill Anomaly Explainer → **Statistical Z-score + rule-based attribution** (not a trained ML model at all)
**Why not ML here:** this specific feature needs to answer "why was I charged this," and a customer needs to be able to *verify* the answer, not just trust a black-box probability. Comparing this month's bill to the customer's own historical average (z-score) and then checking known charge components (roaming, data add-ons, late fees) is transparent and mathematically checkable — exactly the property you want for a billing dispute. Using an ML classifier here (e.g. Isolation Forest) would also need a lot more historical billing data per customer than is realistic to have this early.

### 4. Multilingual / Code-Mixed Language Detection → **Unicode-range + keyword rules, with `langdetect` as fallback**
**Why not a trained language classifier:** `langdetect` is already a mature, pretrained statistical model for standard languages (English, Hindi, Telugu, etc.) — retraining that from scratch would need a huge multilingual text corpus for no benefit. The gap it doesn't cover is **code-mixed** text (Telugu written in Latin script, e.g. "signal ledu naa phone lo") — no strong pretrained detector exists for that, so I added a lightweight rule layer (checking for common romanized Telugu words) specifically to catch that gap. This is a deliberate hybrid: pretrained model + a small custom rule for the one case it misses.

### 5. Voice + Visual Troubleshooting → **Google Speech Recognition API** (voice) + **Color-based image heuristic** (visual)
**Why not train custom models:**
- Speech recognition from scratch needs enormous labeled audio datasets and GPU training time that's out of scope for a project like this — using a mature, free, production-grade speech API is standard engineering practice (you don't reinvent a solved problem).
- For the visual check, a CNN *could* eventually classify router-light photos, but that needs hundreds of labeled photos across every fault type, which don't exist yet. I used the universal LED color convention instead (red = fault, green = OK, amber = no upstream signal) — deterministic, immediately correct, and the code is structured so a CNN can be swapped in later without changing the API.

### 6. Personalized Recommendation → **k-Nearest Neighbours (KNN)**
**Why this and not the alternatives:**
- **vs. Collaborative Filtering / Matrix Factorization:** these need a large user-item interaction history (thousands of customers × plan choices) to find meaningful patterns. With a small customer base, KNN over a handful of usage/preference features gives a genuine "customers similar to you chose this" recommendation without needing that scale of data.
- **vs. K-Means clustering:** clustering would group customers into broad segments, but doesn't directly answer "what should *this* customer do" as precisely as KNN's neighbor-voting does.

### 7. Proactive Network Issue Detection → **Rule-based threshold over live report counts**
**Why not ML:** detecting "several people in the same area just reported an outage" is a counting problem, not a pattern-learning problem — a threshold rule (e.g. 3+ reports from one pincode within an hour) is exactly what real telecom Network Operations Centers use as a first line of detection, before layering statistical anomaly detection over historical baselines (a natural future extension, noted in the code comments).

---

## If she pushes further: "why not just use one big model (like ChatGPT) for everything?"

> "A single large language model could technically generate plausible-sounding answers for all of these, but it would fail the project's core requirement of **explainability** — you can't point to *why* an LLM said what it said the way you can point to a logistic regression coefficient or a z-score. It would also need constant internet access and an API key, and its behavior wouldn't be verifiable or reproducible the way a locally-trained, inspectable model's is. So I used purpose-built, explainable techniques instead, and reserved the option to add an LLM layer later only for free-text reply generation, not for the underlying decisions."

## One-sentence summary to close with

> "In short: I used Logistic Regression as the shared algorithm everywhere the problem was genuinely a classification task (intent detection and escalation risk), KNN where the problem was similarity-based recommendation, and transparent statistical/rule-based methods wherever explainability and verifiability mattered more than raw predictive power (billing, network, voice, visual) — each choice was deliberate, not arbitrary."
