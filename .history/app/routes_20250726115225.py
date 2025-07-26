from flask import Blueprint, request, jsonify
from app.telemetry import map_to_stride
from app.trust_score import calculate_trust_score

bp = Blueprint('routes', __name__)

@bp.route('/telemetry', methods=['POST'])
def ingest_telemetry():
    telemetry_data = request.get_json()
    # ... Process telemetry data ...
    stride_mapping = map_to_stride(telemetry_data)
    # ... Store data in database (models.py)...
    return jsonify({'status': 'success'})

@bp.route('/trust_score', methods=['GET'])
def get_trust_score():
    session_id = request.args.get('session_id')
    # ... Retrieve trust score from database ...
    trust_score = calculate_trust_score(session_id)
    return jsonify({'trust_score': trust_score, 'mfa_required': trust_score > threshold})
