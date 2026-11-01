"""
Bonus feature: agent handoff summary.

When a conversation escalates, a human agent shouldn't have to re-read the
whole chat. This builds a short, structured summary (intent, risk reasons,
what's already been tried, bill/network context if relevant) so the handoff
is fast -- this is what makes escalation genuinely "explainable" to the
person who has to act on it, not just to the customer.
"""


def build_handoff_summary(user, thread_messages, intent_label, risk_info, extra_context=None):
    user_lines = [m.text for m in thread_messages if m.role == "user"]
    first_issue = user_lines[0] if user_lines else "(no message text captured)"
    last_issue = user_lines[-1] if user_lines else first_issue

    top_reasons = [f"{r['factor']} ({r['effect']} risk)" for r in risk_info["explanation"][:3]]

    lines = [
        f"Customer: {user.name} ({user.plan}, {user.tenure_months} months tenure)",
        f"Detected issue type: {intent_label}",
        f"Escalation risk: {risk_info['risk_score']}% ({risk_info['risk_level']})",
        f"Top risk factors: {', '.join(top_reasons)}",
        f"First message: \"{first_issue}\"",
    ]
    if last_issue != first_issue:
        lines.append(f"Most recent message: \"{last_issue}\"")
    lines.append(f"Messages exchanged before escalation: {len(user_lines)}")

    if extra_context:
        lines.append(f"Additional context: {extra_context}")

    return "\n".join(lines)
