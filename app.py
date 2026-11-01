"""
IntelliConnect backend -- Flask REST API.

Run with:  python app.py
Serves on: http://127.0.0.1:5000

See README.md for setup, the full endpoint list, and which algorithm was
used for each feature and why.
"""
import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

from models import db, User, BillRecord, UsageRecord, ChatMessage, NetworkReport, ThreadState

from ml.intent import intent_classifier
from ml.sentiment import sentiment_score, negative_word_count, has_strong_frustration
from ml.escalation import escalation_model
from ml import network_monitor
from ml.bill_anomaly import explain_bill
from ml.recommender import recommend_plan
from ml.handoff_summary import build_handoff_summary
from ml import conversation_flow

from services import language as lang_service
from services import voice as voice_service
from services import visual as visual_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'intelliconnect.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# allow the Live Server frontend (any localhost port) to call this API
CORS(app, resources={r"/api/*": {"origins": "*"}})

with app.app_context():
    db.create_all()


# ---------------------------------------------------------------- helpers
def user_or_404(user_id):
    user = User.query.get(user_id)
    if not user:
        return None
    return user


# ---------------------------------------------------------------- root
@app.route("/")
def index():
    return jsonify({
        "service": "IntelliConnect backend",
        "status": "running",
        "endpoints": [
            "POST /api/auth/signup",
            "POST /api/auth/login",
            "POST /api/chat",
            "POST /api/network/report",
            "GET  /api/network/status/<pincode>",
            "POST /api/bill/explain",
            "GET  /api/bills/<user_id>",
            "POST /api/voice/transcribe",
            "POST /api/visual/diagnose",
            "GET  /api/recommend/<user_id>",
        ],
    })


# ---------------------------------------------------------------- auth
@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json(force=True)
    required = ["name", "email", "password", "phone"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "name, email, password and phone are required"}), 400

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(
        name=data["name"],
        email=data["email"].lower(),
        phone=data["phone"],
        plan=data.get("plan", "Prepaid - Basic"),
        pincode=data.get("pincode", "500001"),
        tenure_months=0,
        past_complaints=0,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return jsonify({"user": user.to_dict()}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data.get("email", "").lower()).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"user": user.to_dict()})


# ---------------------------------------------------------------- chat (core pipeline)
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    thread_id = data.get("thread_id") or str(uuid.uuid4())
    raw_message = (data.get("message") or "").strip()

    if not raw_message:
        return jsonify({"error": "message is required"}), 400

    user = user_or_404(user_id)
    if not user:
        return jsonify({"error": "unknown user_id"}), 404

    # --- 4. multilingual + code-mixed detection & translation ---
    lang_info = lang_service.detect_language(raw_message)
    english_text = lang_service.to_english(raw_message, lang_info["language"])

    # --- NLU intent detection ---
    intent_result = intent_classifier.predict(english_text)

    # --- conversation context for escalation features ---
    prior_user_turns = ChatMessage.query.filter_by(
        user_id=user.id, thread_id=thread_id, role="user"
    ).count()
    repeat_contacts = prior_user_turns  # this message will be turn N+1

    sentiment = sentiment_score(english_text)
    neg_words = negative_word_count(english_text)

    # --- 2 & 6. predictive escalation + explainability ---
    risk_info = escalation_model.predict(
        sentiment=sentiment,
        repeat_contacts=repeat_contacts,
        tenure_months=user.tenure_months,
        past_complaints=user.past_complaints,
        negative_words=neg_words,
    )

    # log the user's message
    db.session.add(ChatMessage(
        user_id=user.id, thread_id=thread_id, role="user", text=raw_message,
        intent=intent_result["intent"], confidence=intent_result["confidence"],
        risk_score=risk_info["risk_score"],
    ))
    db.session.commit()

    # --- 4-stage conversation flow: figure out whether this message
    # continues the issue already being worked on in this thread, or is a
    # brand-new issue (which restarts the flow at stage 1) ---
        # safety net: classifier unsure but message has a clear issue keyword
    if intent_result["confidence"] < 40:
        kw_intent = conversation_flow.keyword_intent(english_text)
        if kw_intent:
            intent_result = dict(intent_result, intent=kw_intent, confidence=60)

    state = ThreadState.query.get(thread_id)
    reply_kind = conversation_flow.classify_reply(english_text)

    # brand-new thread and still unsure what it's about -> ask, don't guess
    if state is None and intent_result["confidence"] < 40:
        return jsonify({
            "thread_id": thread_id,
            "reply": lang_service.from_english(conversation_flow.clarify_reply(), lang_info["language"]),
            "language": lang_info,
            "translated_input": english_text,
            "intent": "general",
            "intent_label": "Not sure yet",
            "confidence": intent_result["confidence"],
            "intent_distribution": intent_result["distribution"],
            "conversation_stage": 0,
            "risk_score": risk_info["risk_score"],
            "risk_level": risk_info["risk_level"],
            "risk_explanation": risk_info["explanation"],
            "proactive_network_alert": None,
            "bill_alert": None,
            "recommendation": None,
            "handoff_summary": None,
        })

    resolved = False
    if state is None:
        state = ThreadState(thread_id=thread_id, user_id=user.id)
        db.session.add(state)
        state.intent = intent_result["intent"]
        state.stage = 1
    else:
        confidently_different = (
            intent_result["intent"] != state.intent and intent_result["confidence"] >= 65
        )
        if confidently_different:
            state.intent = intent_result["intent"]
            state.stage = 1
        elif state.stage in (1, 3) and reply_kind == "yes" and state.intent not in ("plan_change", "cancel"):
            resolved = True  # customer says it's fixed
        elif (state.stage == 1 and reply_kind == "other"
              and intent_result["intent"] == state.intent and intent_result["confidence"] >= 65):
            pass  # customer just repeated the issue, stay on stage 1
        else:
            state.stage = min(state.stage + 1, 4)
    db.session.commit()

    active_intent = state.intent
    active_intent_label = conversation_flow.INTENT_LABELS.get(active_intent, active_intent)

    strong_frustration = has_strong_frustration(english_text)
    if risk_info["risk_level"] == "high" and strong_frustration:
        effective_stage = 4
    else:
        effective_stage = state.stage

    if resolved:
        reply_english = conversation_flow.resolved_reply()
        db.session.delete(state)
        db.session.commit()
    elif effective_stage == 1:
        reply_english = conversation_flow.stage1_reply(active_intent, user)
    elif effective_stage == 2:
        reply_english = conversation_flow.stage2_reply(active_intent, user)
    elif effective_stage == 3:
        reply_english = conversation_flow.stage3_reply(active_intent, user, raw_message)
    else:
        reply_english = conversation_flow.escalate_reply(active_intent)

    # --- auxiliary feature data, still returned for the insight panel ---
    proactive_alert = None
    if active_intent == "network":
        area_status = network_monitor.check_area_status(user.pincode)
        if area_status["status"] == "likely_outage":
            proactive_alert = area_status["message"]

    bill_alert = None
    if active_intent == "billing":
        bills = BillRecord.query.filter_by(user_id=user.id).order_by(BillRecord.month).all()
        if bills:
            bill_alert = explain_bill(bills[-1], bills[:-1])

    recommendation = None
    if active_intent == "plan_change":
        usage = UsageRecord.query.filter_by(user_id=user.id).order_by(UsageRecord.month.desc()).first()
        avg_daily_gb = (usage.data_used_gb / 30) if usage else 1.0
        recommendation = recommend_plan(avg_daily_gb=avg_daily_gb, price_sensitivity=0.5, current_plan=user.plan)

    handoff_summary = None
    if effective_stage == 4:
        thread_messages = ChatMessage.query.filter_by(user_id=user.id, thread_id=thread_id).all()
        handoff_summary = build_handoff_summary(user, thread_messages, active_intent_label, risk_info)

    # --- translate reply back to the customer's language if needed ---
    reply_final = lang_service.from_english(reply_english, lang_info["language"])

    db.session.add(ChatMessage(
        user_id=user.id, thread_id=thread_id, role="bot", text=reply_final,
        intent=active_intent, confidence=intent_result["confidence"],
        risk_score=risk_info["risk_score"],
    ))
    db.session.commit()

    return jsonify({
        "thread_id": thread_id,
        "reply": reply_final,
        "language": lang_info,
        "translated_input": english_text,
        "intent": active_intent,
        "intent_label": active_intent_label,
        "confidence": intent_result["confidence"],
        "intent_distribution": intent_result["distribution"],
        "conversation_stage": effective_stage,
        "risk_score": risk_info["risk_score"],
        "risk_level": risk_info["risk_level"],
        "risk_explanation": risk_info["explanation"],
        "proactive_network_alert": proactive_alert,
        "bill_alert": bill_alert,
        "recommendation": recommendation,
        "handoff_summary": handoff_summary,
    })


# ---------------------------------------------------------------- network
@app.route("/api/network/report", methods=["POST"])
def network_report():
    data = request.get_json(force=True)
    pincode = data.get("pincode")
    if not pincode:
        return jsonify({"error": "pincode is required"}), 400
    network_monitor.log_report(pincode, data.get("issue_type", "outage"))
    return jsonify(network_monitor.check_area_status(pincode))


@app.route("/api/network/status/<pincode>", methods=["GET"])
def network_status(pincode):
    return jsonify(network_monitor.check_area_status(pincode))


# ---------------------------------------------------------------- billing
@app.route("/api/bill/explain", methods=["POST"])
def bill_explain():
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    user = user_or_404(user_id)
    if not user:
        return jsonify({"error": "unknown user_id"}), 404

    bills = BillRecord.query.filter_by(user_id=user.id).order_by(BillRecord.month).all()
    if not bills:
        return jsonify({"error": "no bill records for this user"}), 404

    current = bills[-1]
    history = bills[:-1]
    return jsonify(explain_bill(current, history))


@app.route("/api/bills/<int:user_id>", methods=["GET"])
def list_bills(user_id):
    bills = BillRecord.query.filter_by(user_id=user_id).order_by(BillRecord.month).all()
    return jsonify([
        {"month": b.month, "amount": b.amount, "roaming_charge": b.roaming_charge,
         "data_addon_charge": b.data_addon_charge, "late_fee": b.late_fee, "plan_changed": b.plan_changed}
        for b in bills
    ])


# ---------------------------------------------------------------- voice + visual
@app.route("/api/voice/transcribe", methods=["POST"])
def voice_transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "no audio file uploaded (expected form field 'audio')"}), 400
    result = voice_service.transcribe_audio(request.files["audio"])
    return jsonify(result)


@app.route("/api/visual/diagnose", methods=["POST"])
def visual_diagnose():
    if "image" not in request.files:
        return jsonify({"error": "no image uploaded (expected form field 'image')"}), 400
    result = visual_service.diagnose_image(request.files["image"])
    return jsonify(result)


# ---------------------------------------------------------------- recommendation
@app.route("/api/recommend/<int:user_id>", methods=["GET"])
def recommend(user_id):
    user = user_or_404(user_id)
    if not user:
        return jsonify({"error": "unknown user_id"}), 404

    usage = UsageRecord.query.filter_by(user_id=user.id).order_by(UsageRecord.month.desc()).first()
    avg_daily_gb = (usage.data_used_gb / 30) if usage else 1.0
    return jsonify(recommend_plan(avg_daily_gb=avg_daily_gb, price_sensitivity=0.5, current_plan=user.plan))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
