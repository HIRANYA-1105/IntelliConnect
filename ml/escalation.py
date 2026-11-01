"""
Feature: predictive churn / complaint escalation risk, with explainability.

A Logistic Regression model (deliberately -- it's a linear model, so its
coefficients can be read directly as feature attributions, which is what
powers feature 6, "explainable escalation"). Trained on a synthetic dataset
generated with a known rule + noise, standing in for real historical
support-ticket outcomes. Swap generate_synthetic_dataset() for a query
against your ticketing system once real labeled data exists.

Features used:
  sentiment        -1 (very negative) .. 1 (very positive)
  repeat_contacts   number of messages already sent in this conversation
  tenure_months     how long the customer has been with the operator
  past_complaints   number of prior complaints on the account
  negative_words    count of frustration-indicating words in this message
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = ["sentiment", "repeat_contacts", "tenure_months", "past_complaints", "negative_words"]

FEATURE_DISPLAY = {
    "sentiment": "Message tone",
    "repeat_contacts": "Repeated contact in this chat",
    "tenure_months": "Account tenure",
    "past_complaints": "Past complaint history",
    "negative_words": "Frustration language used",
}


def _generate_synthetic_dataset(n=400, seed=42):
    rng = np.random.default_rng(seed)

    sentiment = rng.uniform(-1, 1, n)
    repeat_contacts = rng.integers(0, 6, n)
    tenure_months = rng.integers(1, 61, n)
    past_complaints = rng.integers(0, 6, n)
    negative_words = rng.integers(0, 6, n)

    # ground-truth rule: escalates when sentiment is low, contact is repeated,
    # complaint history is high, and tenure is low (new, unhappy customers
    # escalate faster) -- plus noise, so the model has to actually learn it.
    linear = (
        -2.6 * sentiment
        + 0.55 * repeat_contacts
        + 0.5 * past_complaints
        + 0.45 * negative_words
        - 0.02 * tenure_months
        - 0.3
    )
    prob = 1 / (1 + np.exp(-linear))
    noise = rng.normal(0, 0.15, n)
    labels = (prob + noise > 0.5).astype(int)

    X = np.column_stack([sentiment, repeat_contacts, tenure_months, past_complaints, negative_words])
    return X, labels


class EscalationModel:
    def __init__(self):
        X, y = _generate_synthetic_dataset()
        self.scaler = StandardScaler().fit(X)
        X_scaled = self.scaler.transform(X)
        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(X_scaled, y)

    def predict(self, sentiment, repeat_contacts, tenure_months, past_complaints, negative_words):
        raw = np.array([[sentiment, repeat_contacts, tenure_months, past_complaints, negative_words]])
        scaled = self.scaler.transform(raw)

        risk_prob = float(self.model.predict_proba(scaled)[0][1])
        risk_score = round(risk_prob * 100, 1)

        if risk_score >= 70:
            level = "high"
        elif risk_score >= 40:
            level = "medium"
        else:
            level = "low"

        # explainability: each feature's (coefficient * scaled value) is its
        # contribution to the logit -- a standard, honest way to explain a
        # linear model's decision without needing a separate SHAP library.
        contributions = self.model.coef_[0] * scaled[0]
        ranked = sorted(
            zip(FEATURE_NAMES, contributions),
            key=lambda pair: abs(pair[1]),
            reverse=True,
        )

        explanation = []
        for name, contrib in ranked:
            direction = "increases" if contrib > 0 else "decreases"
            explanation.append({
                "factor": FEATURE_DISPLAY[name],
                "effect": direction,
                "weight": round(float(abs(contrib)), 3),
            })

        return {
            "risk_score": risk_score,
            "risk_level": level,
            "explanation": explanation,
        }


escalation_model = EscalationModel()
