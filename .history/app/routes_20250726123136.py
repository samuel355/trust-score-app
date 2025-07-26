from flask import Blueprint, request, jsonify
from app.telemetry import map_to_stride
from app.utils import generate_synthetic_telemetry, load_sample_cicids2017_data
from datetime import datetime
from app.turest_score import calculate_trust_score
from app.models import db, TelemetryData, TrustScore

bp = Blueprint('routes', __name__)

@bp.route('/telemetry', methods=['POST'])
def ingest_telemetry():
    telemetry_data = request.get_json()
    stride_mapping = map_to_stride(telemetry_data)
    
    # Store telemetry data using SQLAlchemy
    telemetry_record = TelemetryData(
        vm_id=telemetry_data.get('vm_id'),
        timestamp=datetime.utcnow(),
        event_type=telemetry_data.get('event_type'),
        stride_category=stride_mapping['stride_category'],
        risk_level=stride_mapping['risk_level']
    )
    db.session.add(telemetry_record)
    
    # Calculate and store trust score
    trust_score, mfa_required = calculate_trust_score(stride_mapping['risk_level'], stride_mapping['stride_category'])
    trust_record = TrustScore(
        session_id=telemetry_data.get('session_id'),
        vm_id=telemetry_data.get('vm_id'),
        timestamp=datetime.utcnow(),
        trust_score=trust_score,
        mfa_required=mfa_required
    )
    db.session.add(trust_record)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@bp.route('/trust_score', methods=['GET'])
def get_trust_score():
    session_id = request.args.get('session_id')
    # Fetch the latest trust score for the session_id using SQLAlchemy
    trust_record = TrustScore.query.filter_by(session_id=session_id).order_by(TrustScore.timestamp.desc()).first()
    if trust_record:
        trust_score = trust_record.trust_score
        mfa_required = trust_record.mfa_required
    else:
        trust_score = None
        mfa_required = None
    return jsonify({'trust_score': trust_score, 'mfa_required': mfa_required})

@bp.route('/generate_synthetic_telemetry', methods=['POST'])
def generate_and_process_telemetry():
    # Generate synthetic telemetry
    synthetic_data = generate_synthetic_telemetry()
    # Process it through the telemetry endpoint
    stride_mapping = map_to_stride(synthetic_data)
    
    # Store telemetry data using SQLAlchemy
    telemetry_record = TelemetryData(
        vm_id=synthetic_data.get('vm_id'),
        timestamp=datetime.utcnow(),
        event_type=synthetic_data.get('event_type'),
        stride_category=stride_mapping['stride_category'],
        risk_level=stride_mapping['risk_level']
    )
    db.session.add(telemetry_record)
    
    # Calculate and store trust score
    trust_score, mfa_required = calculate_trust_score(stride_mapping['risk_level'], stride_mapping['stride_category'])
    trust_record = TrustScore(
        session_id=synthetic_data.get('session_id'),
        vm_id=synthetic_data.get('vm_id'),
        timestamp=datetime.utcnow(),
        trust_score=trust_score,
        mfa_required=mfa_required
    )
    db.session.add(trust_record)
    db.session.commit()
    
    return jsonify({'status': 'success', 'session_id': synthetic_data.get('session_id')})

@bp.route('/test_sample_data', methods=['POST'])
def test_sample_data():
    """Test endpoint using the sample CICIDS2017 JSON file"""
    # Load sample data
    sample_data = load_sample_cicids2017_data()
    if not sample_data:
        return jsonify({'error': 'Sample data file not found'}), 404
    
    # Process the sample data
    stride_mapping = map_to_stride(sample_data)
    
    # Store telemetry data using SQLAlchemy
    telemetry_record = TelemetryData(
        vm_id=sample_data.get('vm_id'),
        timestamp=datetime.utcnow(),
        event_type=sample_data.get('event_type'),
        stride_category=stride_mapping['stride_category'],
        risk_level=stride_mapping['risk_level']
    )
    db.session.add(telemetry_record)
    
    # Calculate and store trust score
    trust_score, mfa_required = calculate_trust_score(
        stride_mapping['risk_level'], 
        stride_mapping['stride_category'], 
        sample_data
    )
    trust_record = TrustScore(
        session_id=sample_data.get('session_id'),
        vm_id=sample_data.get('vm_id'),
        timestamp=datetime.utcnow(),
        trust_score=trust_score,
        mfa_required=mfa_required
    )
    db.session.add(trust_record)
    db.session.commit()
    
    return jsonify({
        'status': 'success', 
        'session_id': sample_data.get('session_id'),
        'stride_category': stride_mapping['stride_category'],
        'risk_level': stride_mapping['risk_level'],
        'trust_score': trust_score,
        'mfa_required': mfa_required
    })
