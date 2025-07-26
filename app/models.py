from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TelemetryData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vm_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    event_type = db.Column(db.String(50))
    # ... other telemetry fields ...
    stride_category = db.Column(db.String(50))
    risk_level = db.Column(db.Integer)  # 1-5 (or similar)

class TrustScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), nullable=False)
    vm_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    trust_score = db.Column(db.Float, nullable=False)
    mfa_required = db.Column(db.Boolean, nullable=False)
    # ... other fields ...
