"""
Feature: NLU intent detection.

A small, fast, fully-interpretable pipeline (TF-IDF -> Logistic Regression)
trained on data/intents_dataset.py at server startup. Good enough to
demonstrate real ML (not keyword-matching) for a project prototype; swap in
a transformer-based classifier (e.g. fine-tuned DistilBERT) later without
changing the predict() contract below.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from data.intents_dataset import INTENT_EXAMPLES

INTENT_LABELS = {
    "billing": "Billing dispute",
    "network": "Network outage",
    "plan_change": "Plan change",
    "sim": "SIM / device issue",
    "cancel": "Cancellation request",
    "general": "General inquiry",
}


class IntentClassifier:
    def __init__(self):
        texts = [t for t, _ in INTENT_EXAMPLES]
        labels = [l for _, l in INTENT_EXAMPLES]

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, lowercase=True)),
            ("clf", LogisticRegression(max_iter=1000, C=4.0)),
        ])
        self.pipeline.fit(texts, labels)
        self.classes_ = self.pipeline.named_steps["clf"].classes_

    def predict(self, text: str) -> dict:
        """Returns the predicted intent key, a human label, confidence (0-100),
        and the full probability distribution (useful for the insight panel)."""
        proba = self.pipeline.predict_proba([text])[0]
        best_idx = proba.argmax()
        intent_key = self.classes_[best_idx]
        confidence = round(float(proba[best_idx]) * 100, 1)

        distribution = {
            self.classes_[i]: round(float(p) * 100, 1) for i, p in enumerate(proba)
        }

        return {
            "intent": intent_key,
            "intent_label": INTENT_LABELS.get(intent_key, intent_key),
            "confidence": confidence,
            "distribution": distribution,
        }


# single shared instance, trained once when the module is imported
intent_classifier = IntentClassifier()
