"""
4-stage resolution flow, reused for every intent.

  Stage 1 -- quick self-help fix, then "did that fix it?"
  Stage 2 -- one targeted question (pincode, amount, etc.)
  Stage 3 -- specific solution + realistic time estimate
  Stage 4 -- human agent (last step)

Extra rules: weak/unclear messages get a clarifying question,
and "yes, fixed" replies close the issue instead of escalating.
"""
import re
from ml import network_monitor
from ml.recommender import recommend_plan

INTENT_LABELS = {
    "billing": "Billing dispute",
    "network": "Network issue",
    "recharge": "Recharge issue",
    "plan_change": "Plan change",
    "sim": "SIM / device issue",
    "cancel": "Cancellation request",
    "general": "General inquiry",
}

# ---------------------------------------------------------------- helpers
_KEYWORDS = [
    ("recharge", r"recharg|top.?up|validity|not credited"),
    ("network", r"network|signal|internet|no data|slow|call drop|coverage|wifi|broadband|router"),
    ("billing", r"\bbill|overcharg|charged|refund|deducted"),
    ("sim", r"\be?sims?\b|activation"),
    ("plan_change", r"\bplan|upgrade|downgrade|cheaper"),
    ("cancel", r"cancel|port.?out|disconnect"),
]


def keyword_intent(text: str):
    """Safety net for when the classifier is unsure but the message
    clearly contains an issue keyword."""
    t = text.lower()
    for intent, pattern in _KEYWORDS:
        if re.search(pattern, t):
            return intent
    return None


def classify_reply(text: str) -> str:
    """Returns 'yes' (it's fixed / ok), 'no' (still broken) or 'other'."""
    t = text.lower().strip()
    words = set(re.findall(r"[a-z']+", t))
    no_phrases = ("not working", "still", "didn't", "didnt", "not fixed",
                  "no change", "not solved", "doesn't", "doesnt")
    if any(p in t for p in no_phrases) or words & {"no", "nope", "not", "nahi", "ledu", "kaledu", "avvaledu"}:
        return "no"
    if words & {"yes", "yeah", "yep", "ok", "okay", "fixed", "solved", "resolved",
                "sorted", "worked", "thanks", "thank", "ayindi", "bagundi"} or "working now" in t:
        return "yes"
    return "other"


def clarify_reply() -> str:
    return (
        "I want to make sure I help with the right thing. Is your issue about: "
        "1) network or no signal, 2) recharge not reflecting, 3) a wrong bill charge, "
        "4) SIM problem, 5) changing your plan, or 6) cancelling? Just reply in a few words."
    )


def resolved_reply() -> str:
    return "Great, glad that's sorted! If anything else comes up, just message me here."


def _plan_recommendation(user):
    from models import UsageRecord  # avoids circular import

    usage = UsageRecord.query.filter_by(user_id=user.id).order_by(UsageRecord.month.desc()).first()
    if usage:
        avg_daily_gb = usage.data_used_gb / 30
        usage_line = (
            f"you used about {usage.data_used_gb:.1f} GB and {usage.calls_minutes} call minutes "
            f"last month on your current {user.plan} plan"
        )
    else:
        avg_daily_gb = 1.0
        usage_line = (
            f"you're averaging around {avg_daily_gb * 30:.0f} GB of data a month "
            f"on your current {user.plan} plan"
        )
    rec = recommend_plan(avg_daily_gb=avg_daily_gb, price_sensitivity=0.5, current_plan=user.plan)
    return rec, usage_line


# ---------------------------------------------------------------- stage 1
STAGE1_FIX = {
    "network": "turn on Airplane Mode for 30 seconds and turn it off, then restart your phone or router and wait 2 minutes. Also check that your network mode is set to Auto (4G/5G).",
    "recharge": "wait 10 minutes (recharges can take a little time to reflect), then restart your phone and check your balance and validity again in the app.",
    "billing": "check the exact amount and date on the SMS/email receipt for the charge that looks wrong, so we can compare it against your plan.",
    "sim": "power off your phone, remove and re-insert the SIM card, then power back on.",
    "plan_change": "think about what matters most to you -- more data, a lower price, or unlimited calling -- so I can point you to the right plan.",
    "cancel": "tell me a bit about what's driving this, in case it's something we can actually fix instead.",
    "general": "share a few more details about what's happening.",
}


def stage1_reply(intent: str, user=None) -> str:
    if intent == "plan_change" and user is not None:
        rec, usage_line = _plan_recommendation(user)
        return (
            f"I checked your usage -- {usage_line}. Based on that, I'd recommend "
            f"**{rec['recommended_plan']}** (₹{rec['recommended_price']}, {rec['recommended_data_gb']} GB) "
            f"-- {rec['reason']} Want me to switch you to it, or would you like something cheaper or with even more data?"
        )
    fix = STAGE1_FIX.get(intent, STAGE1_FIX["general"])
    return f"Let's try this first: {fix} Did that fix it?"


# ---------------------------------------------------------------- stage 2
STAGE2_QUESTION = {
    "network": "Sorry that didn't help. Could you share your 6-digit pincode so I can check for reported outages in your area?",
    "recharge": "Sorry about that. Was the money deducted from your account, and what was the recharge amount?",
    "billing": "Got it. Could you confirm the exact amount you were charged and roughly when?",
    "sim": "Understood. Is this a brand-new SIM, or one that was working before and just stopped?",
    "plan_change": "No problem. Would you like more data, a lower monthly price, or unlimited calling?",
    "cancel": "I hear you. Is this mainly about price, network quality, or something else?",
    "general": "Could you tell me a little more so I can route this correctly?",
}


def stage2_reply(intent: str, user=None) -> str:
    if intent == "plan_change" and user is not None:
        rec, usage_line = _plan_recommendation(user)
        return (
            f"Here's the comparison: your current **{user.plan}** vs the recommended "
            f"**{rec['recommended_plan']}** (₹{rec['recommended_price']}, {rec['recommended_data_gb']} GB) "
            f"-- based on {usage_line}. Shall I go ahead and switch you over?"
        )
    return STAGE2_QUESTION.get(intent, STAGE2_QUESTION["general"])


# ---------------------------------------------------------------- stage 3
def stage3_reply(intent: str, user, answer_text: str) -> str:
    lower = answer_text.lower()

    if intent == "network":
        pin_match = re.search(r"\b\d{6}\b", answer_text)
        pincode = pin_match.group(0) if pin_match else user.pincode
        note = "" if pin_match else f" (I used the pincode on your account, {pincode})"
        network_monitor.log_report(pincode, "outage")
        status = network_monitor.check_area_status(pincode)
        if status["status"] == "likely_outage":
            return (
                f"Thanks{note}. Checking pincode {pincode} -- {status['report_count']} other customers "
                f"have reported the same issue in this area in the last hour. This is a confirmed "
                f"area outage and our field team has already been dispatched. Expected resolution "
                f"in **2-3 hours**. You'll get an SMS the moment it's fixed."
            )
        return (
            f"Thanks{note}. I checked pincode {pincode} and don't see a wider outage, so this looks "
            f"specific to your connection. I've raised a technician visit request, expected "
            f"within **4-6 hours**. If it starts working before that, just let me know."
        )

    if intent == "recharge":
        not_deducted = any(p in lower for p in ("not deducted", "no money", "not debited", "wasn't deducted", "was not deducted"))
        if not_deducted:
            return (
                "Thanks. Since no money was deducted, nothing is lost on your side. "
                "Please try the recharge again in a few minutes. If it fails again, tell me and I'll raise it."
            )
        return (
            "Thanks. I've logged this as a recharge-not-reflected case with those details. "
            "If the payment went through, the recharge is normally credited within **30-60 minutes**. "
            "If it can't be credited, the amount is automatically refunded in **3-5 business days**."
        )

    if intent == "billing":
        return (
            "Thanks for confirming. I've filed a formal dispute for that charge with those details "
            "attached. Verified overcharge refunds are typically processed within **3-5 business "
            "days** and will show as a credit on your next bill."
        )

    if intent == "sim":
        if "new" in lower:
            return "Got it. For a new SIM, activation can take up to **30-60 minutes** after insertion. I've also flagged it for priority activation on our side."
        return "Got it. Since it was working before, this needs a manual re-activation on our end. I've flagged it as priority, expected within **2-4 hours**."

    if intent == "plan_change":
        sensitivity = 0.8 if any(w in lower for w in ["price", "cheap", "budget", "low"]) else 0.3
        rec = recommend_plan(avg_daily_gb=1.5, price_sensitivity=sensitivity, current_plan=user.plan)
        return (
            f"Based on that, I'd recommend **{rec['recommended_plan']}** (₹{rec['recommended_price']}) "
            f"-- {rec['reason']} I can switch you over now; it takes effect within **24 hours**."
        )

    if intent == "cancel":
        return (
            "Thanks for sharing that. I've passed this exact concern to our retention team. "
            "They'll call you within **4-6 hours** with options specific to this, before any "
            "cancellation is finalized."
        )

    return "Thanks for the extra detail. Let me dig into this further on my end."


# ---------------------------------------------------------------- stage 4
def escalate_reply(intent: str) -> str:
    return (
        "I've tried the fixes I can do from my side, so I'm connecting you with a human "
        "specialist now. They'll have the full context from this conversation already."
    )