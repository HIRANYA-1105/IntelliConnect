"""
Feature: bill anomaly explainer.

Statistical anomaly check (z-score of the current bill against the
customer's own trailing average) combined with rule-based root-cause
attribution across known charge components. This is intentionally a
transparent statistical method rather than a black-box model -- for a
"why was I charged this" explanation, customers (and evaluators) need to
trust the reasoning, not just a probability.
"""
import statistics


def explain_bill(current_bill, history):
    """
    current_bill: BillRecord for the month being explained
    history: list of previous BillRecord rows (most recent last), excluding current
    """
    if not history:
        return {
            "is_anomaly": False,
            "message": "This is your first bill on record, so there's no history to compare against yet.",
            "components": _components(current_bill),
        }

    amounts = [b.amount for b in history]
    mean = statistics.mean(amounts)
    stdev = statistics.pstdev(amounts) if len(amounts) > 1 else max(mean * 0.1, 1)
    stdev = stdev or 1  # avoid divide-by-zero when history is flat

    z_score = (current_bill.amount - mean) / stdev
    percent_change = ((current_bill.amount - mean) / mean) * 100 if mean else 0

    is_anomaly = z_score > 1.5 or percent_change > 25

    reasons = []
    if current_bill.roaming_charge and current_bill.roaming_charge > 0:
        reasons.append(f"₹{current_bill.roaming_charge:.0f} in roaming charges this month")
    if current_bill.data_addon_charge and current_bill.data_addon_charge > 0:
        reasons.append(f"₹{current_bill.data_addon_charge:.0f} for extra data add-ons")
    if current_bill.late_fee and current_bill.late_fee > 0:
        reasons.append(f"₹{current_bill.late_fee:.0f} late payment fee")
    if current_bill.plan_changed:
        reasons.append("a mid-cycle plan change, which is billed pro-rata")

    if is_anomaly and not reasons:
        reasons.append("higher-than-usual base usage this billing cycle")

    if is_anomaly:
        message = (
            f"Your bill of ₹{current_bill.amount:.0f} is about {percent_change:.0f}% "
            f"higher than your usual ₹{mean:.0f}. Main contributors: " + "; ".join(reasons) + "."
        )
    else:
        message = (
            f"Your bill of ₹{current_bill.amount:.0f} is close to your usual average of "
            f"₹{mean:.0f} -- nothing unusual here."
        )

    return {
        "is_anomaly": bool(is_anomaly),
        "z_score": round(z_score, 2),
        "percent_change": round(percent_change, 1),
        "average_bill": round(mean, 2),
        "message": message,
        "components": _components(current_bill),
    }


def _components(bill):
    return {
        "total": bill.amount,
        "roaming_charge": bill.roaming_charge or 0,
        "data_addon_charge": bill.data_addon_charge or 0,
        "late_fee": bill.late_fee or 0,
        "plan_changed": bool(bill.plan_changed),
    }
