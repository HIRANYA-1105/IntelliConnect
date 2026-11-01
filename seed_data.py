"""
Populates the database with a couple of demo users, bill history and usage
history so you can test /api/bill/explain, /api/recommend, etc. without
manually creating months of data first.

Run once with:  python seed_data.py
Safe to re-run -- it skips users that already exist.
"""
from app import app
from models import db, User, BillRecord, UsageRecord

DEMO_USERS = [
    {
        "name": "Ananya Rao", "email": "ananya@example.com", "password": "password123",
        "phone": "9876543210", "plan": "Prepaid - Unlimited", "pincode": "500001",
        "tenure_months": 14, "past_complaints": 2,
        "bills": [
            {"month": "2026-05", "amount": 299, "roaming_charge": 0, "data_addon_charge": 0, "late_fee": 0},
            {"month": "2026-06", "amount": 299, "roaming_charge": 0, "data_addon_charge": 0, "late_fee": 0},
            {"month": "2026-07", "amount": 310, "roaming_charge": 0, "data_addon_charge": 0, "late_fee": 0},
            {"month": "2026-08", "amount": 545, "roaming_charge": 180, "data_addon_charge": 49, "late_fee": 0, "plan_changed": False},
        ],
        "usage": [
            {"month": "2026-08", "data_used_gb": 68, "data_limit_gb": 60, "calls_minutes": 320, "sms_count": 12},
        ],
    },
    {
        "name": "Karthik Reddy", "email": "karthik@example.com", "password": "password123",
        "phone": "9123456780", "plan": "Prepaid - Basic", "pincode": "500034",
        "tenure_months": 2, "past_complaints": 0,
        "bills": [
            {"month": "2026-07", "amount": 199, "roaming_charge": 0, "data_addon_charge": 0, "late_fee": 0},
            {"month": "2026-08", "amount": 199, "roaming_charge": 0, "data_addon_charge": 0, "late_fee": 0},
        ],
        "usage": [
            {"month": "2026-08", "data_used_gb": 40, "data_limit_gb": 45, "calls_minutes": 150, "sms_count": 5},
        ],
    },
]


def seed():
    with app.app_context():
        for entry in DEMO_USERS:
            if User.query.filter_by(email=entry["email"]).first():
                print(f"skip (already exists): {entry['email']}")
                continue

            user = User(
                name=entry["name"], email=entry["email"], phone=entry["phone"],
                plan=entry["plan"], pincode=entry["pincode"],
                tenure_months=entry["tenure_months"], past_complaints=entry["past_complaints"],
            )
            user.set_password(entry["password"])
            db.session.add(user)
            db.session.flush()  # get user.id before commit

            for b in entry["bills"]:
                db.session.add(BillRecord(user_id=user.id, **b))
            for u in entry["usage"]:
                db.session.add(UsageRecord(user_id=user.id, **u))

            db.session.commit()
            print(f"created: {entry['email']} (id={user.id}, password={entry['password']})")


if __name__ == "__main__":
    seed()
