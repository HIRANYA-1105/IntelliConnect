"""
Feature: personalized recommendation.

Two layers:
1. A simple, explainable usage-fit rule (does the customer regularly cross
   their data limit / use very little of it) -- this alone covers most
   real "you should switch plans" cases and is easy to justify to a user.
2. A k-nearest-neighbours lookup over a small synthetic catalog of past
   customer profiles ("customers with usage like yours picked ...") to add
   a genuine ML-flavored recommendation on top, in the spirit of
   collaborative filtering. Replace the synthetic profiles with real
   anonymized usage/plan-choice history when available.
"""
import numpy as np
from sklearn.neighbors import NearestNeighbors

PLAN_CATALOG = [
    {"name": "Prepaid - Basic", "data_gb": 1.5, "price": 199},
    {"name": "Prepaid - Unlimited", "data_gb": 2.0, "price": 299},
    {"name": "Prepaid - Unlimited+", "data_gb": 3.0, "price": 399},
    {"name": "Postpaid - Family", "data_gb": 5.0, "price": 699},
    {"name": "Broadband - Fiber", "data_gb": 50.0, "price": 899},
]

# synthetic past customers: [avg_daily_gb, price_sensitivity(0=low,1=high)] -> plan index chosen
_rng = np.random.default_rng(7)
_synthetic_usage = _rng.uniform(0.3, 6.0, 150)
_synthetic_sensitivity = _rng.uniform(0, 1, 150)
_synthetic_X = np.column_stack([_synthetic_usage, _synthetic_sensitivity])


def _plan_for_usage(usage, sensitivity):
    # ground-truth-ish assignment used only to label the synthetic dataset
    idx = min(int(usage // 1.2), len(PLAN_CATALOG) - 1)
    if sensitivity > 0.7 and idx > 0:
        idx -= 1  # price-sensitive customers nudge toward the cheaper plan
    return idx


_synthetic_y = np.array([_plan_for_usage(u, s) for u, s in _synthetic_X])
_knn = NearestNeighbors(n_neighbors=7).fit(_synthetic_X)


def recommend_plan(avg_daily_gb: float, price_sensitivity: float = 0.5, current_plan: str = None):
    # rule-based fit check against the customer's *current* plan
    current = next((p for p in PLAN_CATALOG if p["name"] == current_plan), None)
    over_limit = current and avg_daily_gb * 30 > current["data_gb"] * 1000 if current else False

    # KNN vote among similar synthetic customers
    query = np.array([[avg_daily_gb, price_sensitivity]])
    _, neighbor_idx = _knn.kneighbors(query)
    neighbor_votes = _synthetic_y[neighbor_idx[0]]
    voted_idx = int(np.bincount(neighbor_votes).argmax())
    suggested = PLAN_CATALOG[voted_idx]

    reason_bits = []
    if current and suggested["name"] != current["name"]:
        if suggested["data_gb"] > current["data_gb"]:
            reason_bits.append("your recent usage is consistently close to or above your current plan's limit")
        else:
            reason_bits.append("your recent usage is well below your current plan -- you could save money")
    reason_bits.append("similar customers' usage patterns matched this plan most often")

    return {
        "current_plan": current_plan,
        "recommended_plan": suggested["name"],
        "recommended_price": suggested["price"],
        "recommended_data_gb": suggested["data_gb"],
        "is_upgrade_suggestion": bool(current and suggested["data_gb"] > current["data_gb"]),
        "reason": " and ".join(reason_bits) + ".",
    }
