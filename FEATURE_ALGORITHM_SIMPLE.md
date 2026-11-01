# IntelliConnect — Feature Use & Algorithm (Simple English)

For each feature: **what it is used for**, **which algorithm is used**, and **why that algorithm, in simple words**.

---

### 1. Proactive Network Issue Detection
**Use:** Finds out that many people in the same area are facing network problems, and alerts them automatically — before they even complain.

**Algorithm:** Threshold Rule (counting reports)

**Why:** This is just a counting job — "how many people from this area reported an issue in the last hour." No prediction or learning is needed, just counting and comparing to a number. So a simple rule is enough, and it is easy to trust and explain.

---

### 2. Predictive Churn / Complaint Escalation (ML)
**Use:** Reads the customer's message and past history, and predicts if this complaint is likely to get worse and need a human agent — before it actually happens.

**Algorithm:** Logistic Regression

**Why:** This problem has a yes/no answer — "will this escalate or not." Logistic Regression is one of the simplest and most reliable algorithms for yes/no predictions. It also shows clearly which factor (anger in message, repeated contact, etc.) caused the risk to go up — so we can *explain* the prediction, not just give a number.

---

### 3. Bill Anomaly Explainer
**Use:** Checks if a customer's bill is unusually high compared to their normal bills, and explains exactly why (roaming charge, extra data, late fee, etc.).

**Algorithm:** Z-score (statistics), not machine learning

**Why:** This is a math comparison — "is this bill much higher than the usual average?" Statistics can answer this directly and the customer can check the numbers themselves. No need for a complex model when simple math gives a clear, trustworthy answer.

---

### 4. Multilingual + Code-Mixed Language Support
**Use:** Understands customers typing in English, Telugu, Hindi, or a mix of Telugu and English written in English letters (like "signal ledu naa phone lo").

**Algorithm:** Language detection rules + langdetect library

**Why:** Detecting a language is a pattern-matching problem — checking letters/words used. A ready-made tool (langdetect) already does this well for normal languages. We just added extra rules to catch mixed Telugu-English typing, which the ready-made tool misses.

---

### 5. Voice + Visual Troubleshooting
**Use:** Lets the customer speak their problem instead of typing, or send a photo of their router to check if it is faulty.

**Algorithm:** Google Speech Recognition (for voice) + Color analysis (for image)

**Why:** Converting speech to text and reading colors from a photo are not "prediction" problems — they need signal/image processing tools, not classification. We used ready-made, already-trained tools instead of building our own from scratch, because building a voice or image model needs huge amounts of training data we don't have.

---

### 6. Personalized Recommendation
**Use:** Suggests the best plan for a customer based on how much data/calls they actually use, like "customers similar to you picked this plan."

**Algorithm:** K-Nearest Neighbours (KNN)

**Why:** This is a "find similar people" problem. KNN's whole idea is to look at the closest matching customers and see what they chose — which is exactly what a recommendation needs. It also works well even with a small amount of data.

---

### 7. Explainable Escalation
**Use:** When a case is escalated to a human agent, this shows *why* it was escalated, in plain language (e.g. "customer sounded angry" + "contacted 3 times already").

**Algorithm:** Same Logistic Regression model as feature 2, plus a summary generator

**Why:** Because Logistic Regression's answer is built from adding up simple factors, we can show each factor's effect directly — no separate algorithm needed. We just present the same model's internal working in a way a human can read.

---

## One-line summary for each (quick revision)

| Feature | Algorithm | One-line reason |
|---|---|---|
| Network detection | Threshold rule | Just counting reports, no prediction needed |
| Escalation prediction | Logistic Regression | Simple yes/no prediction that can be explained |
| Bill anomaly | Z-score (statistics) | Bill comparison is math, not learning |
| Multilingual support | Rules + langdetect | Ready-made tool + extra rules for code-mixing |
| Voice troubleshooting | Speech Recognition API | Converts speech to text, not a prediction task |
| Visual troubleshooting | Color analysis | Reads LED color, not a prediction task |
| Recommendation | K-Nearest Neighbours | Finds similar customers, matches the problem exactly |
| Explainable escalation | Same Logistic Regression | Reuses feature 2's model, shown in plain language |
