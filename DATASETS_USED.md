# IntelliConnect — Datasets Used (Source, Size, Type)

**Important to say honestly in viva:** No real telecom company shares its actual customer/complaint data publicly (it's private and protected). So for this prototype, datasets were either **self-created (synthetic)** to represent realistic patterns, or came from **existing pretrained open-source libraries**. This is completely normal and expected for a student/academic ML project — real datasets get plugged in later once the system is deployed with an actual telecom provider's data.

---

### 1. Network Issue Detection
**Dataset used:** None (no training data needed)
**Why:** This feature just counts live reports coming into the system in real time — it's a rule, not a trained model, so there's nothing to train on.

---

### 2. Predictive Churn / Escalation Prediction (ML)
**Dataset used:** 400 rows of **self-generated synthetic data**
**Source:** Created by me in `ml/escalation.py`, using Python's `numpy` to generate random values for 5 features (sentiment, repeat contacts, tenure, past complaints, negative words), then labeling each row escalate/not-escalate using a logical rule (angrier + more repeated contact + more complaints = more likely to escalate) plus random noise.
**Why synthetic:** Real historical "did this ticket escalate" data belongs to actual telecom companies and isn't publicly available. Synthetic data built from a known rule lets the model genuinely learn a pattern (not just memorize), which is the standard way to prototype this kind of model before real data exists.
**Upgrade path (mention this if she asks "why not real data"):** A well-known real dataset that could replace this is the **IBM Telco Customer Churn dataset** (publicly available on Kaggle, ~7,000 real customer records with a "Churn Yes/No" label) — I can swap this in without changing any other code, since the model just needs a table of features + a yes/no label.

---

### 3. Bill Anomaly Explainer
**Dataset used:** No separate training dataset — uses **each customer's own bill history**, stored in the app's database (`BillRecord` table).
**Source:** For demo purposes, `seed_data.py` creates 2 sample customers with a few months of bill history each (self-created sample data, realistic amounts based on typical Indian telecom pricing — e.g. ₹199, ₹299 plans).
**Why:** This feature works per-customer (comparing a customer's bill to *their own* average), so it doesn't need a big general dataset — it needs each real customer's actual billing history, which would come from the telecom's billing system in production.

---

### 4. Multilingual + Code-Mixed Language Support
**Dataset used:** The `langdetect` Python library's **built-in pretrained language-profile data**
**Source:** `langdetect` is an open-source library (a Python port of Google's language-detection library), pretrained on large multilingual text collections including Wikipedia text across 55+ languages. I did not train this myself — I used it as a ready-made tool.
**Additional custom data:** A small **self-created list of ~30 common romanized Telugu words** (like "naaku", "ledu", "undi", "kavali") written by me in `services/language.py`, used to catch Telugu-English code-mixed messages that `langdetect` alone would misclassify.

---

### 5. Voice Troubleshooting
**Dataset used:** None directly — uses **Google's Speech Recognition API** (via the `SpeechRecognition` Python library).
**Source:** Google trained this speech-to-text model on their own massive, proprietary audio dataset (not public). I only call their free API; no dataset was needed on my end.

---

### 6. Visual Troubleshooting
**Dataset used:** None — this is a rule-based color analysis, not a trained model.
**Source:** The color-to-diagnosis mapping (red = fault, green = OK, amber = no signal) is based on the **universal telecom/networking hardware convention** for LED indicator lights, not learned from data.
**Upgrade path:** A future version could train a CNN on a labeled dataset of real router-light photos (would need to be collected specifically, e.g. a few hundred photos per fault type) — noted as a next step in the code comments.

---

### 7. Explainable Escalation
**Dataset used:** Same synthetic dataset as Feature 2 (they share the same trained model) — no separate dataset.

---

### 8. Personalized Recommendation
**Dataset used:** 150 rows of **self-generated synthetic customer profiles**
**Source:** Created by me in `ml/recommender.py` using `numpy`, simulating customers with different daily data usage and price sensitivity, each assigned a plan based on a logical rule (heavier users → bigger plans; price-sensitive users → cheaper plans).
**Why synthetic:** Real "which plan did each customer end up choosing" data belongs to the telecom provider. Synthetic data lets the KNN algorithm demonstrate the recommendation logic correctly while real customer-choice data isn't available yet.

---

### 9. Intent Detection (NLU)
**Dataset used:** 85 **self-written labeled examples**
**Source:** Written by me in `data/intents_dataset.py` — sentences covering 6 categories (billing, network, plan_change, sim, cancel, general), including some in Telugu-English mixed phrasing, based on realistic customer queries a telecom support system would receive.
**Why self-written and not an existing dataset:** There's no publicly available labeled dataset specifically for *Indian telecom customer support intents* in code-mixed Telugu-English — so I wrote representative examples myself. For a stronger production version, this could be expanded using real anonymized chat transcripts once the system has live usage.

---

## Quick summary table

| # | Feature | Dataset | Real or Synthetic | Source |
|---|---------|---------|--------------------|--------|
| 1 | Network detection | None (live counting) | — | — |
| 2 | Escalation prediction | 400 rows | Synthetic | Self-generated (numpy + rule) |
| 3 | Bill anomaly | Customer's own bill history | Sample/demo data | Self-created in seed_data.py |
| 4 | Multilingual support | langdetect's built-in data + 30 custom words | Real (library) + self-created (word list) | Open-source library + self-written |
| 5 | Voice troubleshooting | None (uses external API) | — | Google's proprietary model |
| 6 | Visual troubleshooting | None (rule-based) | — | Industry LED color convention |
| 7 | Explainable escalation | Same as #2 | Synthetic | Self-generated |
| 8 | Recommendation | 150 rows | Synthetic | Self-generated (numpy + rule) |
| 9 | Intent detection | 85 examples | Self-written | Written by me |
