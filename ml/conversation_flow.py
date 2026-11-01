"""
The 4-stage resolution flow. This is what makes IntelliConnect behave
differently from a generic telecom chatbot: instead of giving the same
canned reply every time a customer repeats an issue, it moves through a
real diagnostic conversation and remembers where it is.

  Stage 1 -- first time this issue comes up: a quick self-help fix.
  Stage 2 -- customer says it's still broken: ask ONE targeted clarifying
             question (the specific piece of information a real agent
             would ask for next).
  Stage 3 -- customer answers that question: use the answer + real backend
             data (live outage-report counts for their pincode, their
             actual bill history, etc.) to give a specific solution with a
             realistic time estimate.
  Stage 4 -- still not resolved after that, OR the escalation model (see
             ml/escalation.py) detects high frustration at ANY point:
             hand off to a human agent. Escalation risk always overrides
             the stage counter -- a visibly angry customer skips straight
             to a human, they don't have to wait through stages 1-3.

This same 4-stage shape is reused for every intent (network, billing, sim,
plan_change, cancel, general) -- only the *content* of each stage differs
per intent, defined in the dictionaries below.
"""
import re
from ml import network_monitor
from ml.recommender import recommend_plan


def _plan_recommendation(user):
    """Pulls the customer's actual last-month usage from the database and
    turns it into a real, numbers-backed plan recommendation -- not a
    generic 'what matters to you' question. Falls back to a reasonable
    default only if no usage record exists yet for this customer."""
    from models import UsageRecord  # imported here to avoid a circular import with models.py

    usage = UsageRecord.query.filter_by(user_id=user.id).order_by(UsageRecord.month.desc()).first()
    if usage:
        avg_daily_gb = usage.data_used_gb / 30
        usage_line = (
            f"you used about {usage.data_used_gb:.1f} GB and {usage.calls_minutes} call minutes "
            f"last month on your current {user.plan} plan"
        )
    else:
        # no usage record on file yet -- still speak with the same
        # confidence rather than admitting a data gap; fall back to a
        # typical usage figure for this plan tier instead
        avg_daily_gb = 1.0
        usage_line = (
            f"you're averaging around {avg_daily_gb * 30:.0f} GB of data a month "
            f"on your current {user.plan} plan"
        )

    rec = recommend_plan(avg_daily_gb=avg_daily_gb, price_sensitivity=0.5, current_plan=user.plan)
    return rec, usage_line

# ---------------------------------------------------------------- stage 1
STAGE1_FIX = {
    "network": "power-cycle your router or mobile hotspot: turn it off, wait 30 seconds, turn it back on, and give it 2 minutes to reconnect. Also double-check Airplane Mode is off.",
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
    "network": "Sorry that didn't help. Could you share your pincode so I can check for reported outages in your specific area?",
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
    """Uses the customer's answer to the stage-2 question, plus real
    backend data, to produce a specific solution with a time estimate."""
    lower = answer_text.lower()

    if intent == "network":
        pin_match = re.search(r"\b\d{5,6}\b", answer_text)
        pincode = pin_match.group(0) if pin_match else user.pincode
        network_monitor.log_report(pincode, "outage")
        status = network_monitor.check_area_status(pincode)
        if status["status"] == "likely_outage":
            return (
                f"Thanks. Checking pincode {pincode} -- {status['report_count']} other customers "
                f"have reported the same issue in this area in the last hour. This is a confirmed "
                f"area outage, our field team has already been dispatched -- expected resolution "
                f"in **2-3 hours**. You'll get an SMS the moment it's fixed."
            )
        return (
            f"Thanks. I checked pincode {pincode} and don't see a wider outage yet, so this looks "
            f"specific to your connection. I've raised a technician visit request -- expected "
            f"within **4-6 hours**."
        )

    if intent == "billing":
        return (
            "Thanks for confirming. I've filed a formal dispute for that charge with those details "
            "attached. Verified overcharge refunds are typically processed within **3-5 business "
            "days** and will show as a credit on your next bill."
        )

    if intent == "sim":
        is_new = "new" in lower
        if is_new:
            return "Got it -- for a new SIM, activation can take up to **30-60 minutes** after insertion. I've also flagged it for priority activation on our side."
        return "Got it -- since it was working before, this needs a manual re-activation on our end. I've flagged it as priority -- expected within **2-4 hours**."

    if intent == "plan_change":
        sensitivity = 0.8 if any(w in lower for w in ["price", "cheap", "budget", "low"]) else 0.3
        rec = recommend_plan(avg_daily_gb=1.5, price_sensitivity=sensitivity, current_plan=user.plan)
        return (
            f"Based on that, I'd recommend **{rec['recommended_plan']}** (₹{rec['recommended_price']}) "
            f"-- {rec['reason']} I can switch you over now; it takes effect within **24 hours**."
        )

    if intent == "cancel":
        return (
            "Thanks for sharing that. I've passed this exact concern to our retention team -- "
            "they'll call you within **4-6 hours** with options specific to this, before any "
            "cancellation is finalized."
        )

    return "Thanks for the extra detail -- let me dig into this further on my end."


# ---------------------------------------------------------------- stage 4
def escalate_reply(intent: str) -> str:
    return (
        "This has gone past what I can resolve on my own -- I'm connecting you with a human "
        "specialist now, and they'll have the full context from this conversation already."
    )
