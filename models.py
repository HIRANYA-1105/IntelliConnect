"""
Database models for IntelliConnect.
SQLite file (intelliconnect.db) is created automatically on first run --
no separate database server needed.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15))
    plan = db.Column(db.String(80), default="Prepaid - Basic")
    pincode = db.Column(db.String(10), default="500001")
    tenure_months = db.Column(db.Integer, default=6)
    past_complaints = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "plan": self.plan,
            "pincode": self.pincode,
            "tenure_months": self.tenure_months,
        }


class BillRecord(db.Model):
    __tablename__ = "bill_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    month = db.Column(db.String(7))  # "2026-08"
    amount = db.Column(db.Float, nullable=False)
    roaming_charge = db.Column(db.Float, default=0)
    data_addon_charge = db.Column(db.Float, default=0)
    late_fee = db.Column(db.Float, default=0)
    plan_changed = db.Column(db.Boolean, default=False)


class UsageRecord(db.Model):
    __tablename__ = "usage_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    month = db.Column(db.String(7))
    data_used_gb = db.Column(db.Float, default=0)
    data_limit_gb = db.Column(db.Float, default=1.5)
    calls_minutes = db.Column(db.Integer, default=0)
    sms_count = db.Column(db.Integer, default=0)


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    thread_id = db.Column(db.String(40), nullable=False)
    role = db.Column(db.String(10))  # "user" | "bot"
    text = db.Column(db.Text)
    intent = db.Column(db.String(40))
    confidence = db.Column(db.Float)
    risk_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NetworkReport(db.Model):
    """Individual 'my network is down' pings, real or simulated, used for
    proactive area-level outage detection (feature 1)."""
    __tablename__ = "network_reports"

    id = db.Column(db.Integer, primary_key=True)
    pincode = db.Column(db.String(10), nullable=False)
    issue_type = db.Column(db.String(40), default="outage")
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)


class ThreadState(db.Model):
    """Tracks where each conversation thread is in the 4-stage resolution
    flow: 1) quick self-help fix, 2) clarifying question, 3) detailed
    solution using the customer's answer + real data, 4) escalate to a
    human. This is what lets the bot remember it already tried something,
    instead of repeating the same reply every time."""
    __tablename__ = "thread_states"

    thread_id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    intent = db.Column(db.String(40))
    stage = db.Column(db.Integer, default=1)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
