from flask import Blueprint, request, jsonify
from app.telemetry import map_to_stride
from app.utils import get_supabase_client
from datetime import datetime

bp = Blueprint('routes', __name__)

@bp.route('/telemetry', methods=['POST'])
def ingest_telemetry():
    telemetry_data = request.get_json()
    stride_mapping = map_to_stride(telemetry_data)
    supabase = get_supabase_client()
    # Compose the data to insert
    data = {
        'vm_id': telemetry_data.get('vm_id'),
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': telemetry_data.get('event_type'),
        'stride_category': stride_mapping['stride_category'],
        'risk_level': stride_mapping['risk_level'],
        # Add other telemetry fields as needed
    }
    supabase.table('TelemetryData').insert(data).execute()
    return jsonify({'status': 'success'})

@bp.route('/trust_score', methods=['GET'])
def get_trust_score():
    session_id = request.args.get('session_id')
    supabase = get_supabase_client()
    # Fetch the latest trust score for the session_id
    result = supabase.table('TrustScore').select('*').eq('session_id', session_id).order('timestamp', desc=True).limit(1).execute()
    if result.data:
        trust_score = result.data[0]['trust_score']
        mfa_required = result.data[0]['mfa_required']
    else:
        trust_score = None
        mfa_required = None
    return jsonify({'trust_score': trust_score, 'mfa_required': mfa_required})
