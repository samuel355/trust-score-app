from flask import Blueprint, request, jsonify
from app.telemetry import map_to_stride
from app.utils import get_supabase_client, generate_synthetic_telemetry, load_sample_cicids2017_data
from datetime import datetime
from app.turest_score import calculate_trust_score
from app.auth import require_auth, require_vm_agent

bp = Blueprint('routes', __name__)

@bp.route('/', methods=['GET'])
def root():
    """Root endpoint - Trust Engine API welcome"""
    return jsonify({
        'message': 'Trust Engine API is running!',
        'description': 'Adaptive, context-aware authentication for remote users',
        'endpoints': {
            'GET /': 'API information (this endpoint)',
            'GET /auth/login': 'Okta login for users',
            'POST /auth/vm-agent/login': 'VM agent login',
            'GET /auth/logout': 'Okta logout',
            'GET /auth/user': 'Get current user info',
            'POST /telemetry': 'Ingest telemetry data (VM agents)',
            'GET /trust_score': 'Get trust score for a session (users)',
            'POST /generate_synthetic_telemetry': 'Generate and process synthetic telemetry data (users)',
            'POST /test_sample_data': 'Test with sample CICIDS2017 data (users)'
        },
        'status': 'running'
    })

@bp.route('/telemetry', methods=['POST'])
@require_vm_agent
def ingest_telemetry():
    """Ingest telemetry data from VM agents"""
    telemetry_data = request.get_json()
    
    # Add VM agent context to telemetry
    telemetry_data['vm_agent_id'] = request.current_user.email
    telemetry_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
    
    stride_mapping = map_to_stride(telemetry_data)
    supabase = get_supabase_client()
    
    # Compose the data to insert
    data = {
        'vm_id': telemetry_data.get('vm_id'),
        'vm_agent_id': telemetry_data.get('vm_agent_id'),
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': telemetry_data.get('event_type'),
        'stride_category': stride_mapping['stride_category'],
        'risk_level': stride_mapping['risk_level'],
        'features': {k: v for k, v in telemetry_data.items() 
                    if k not in ['vm_id', 'vm_agent_id', 'event_type', 'timestamp', 'ingestion_timestamp']}
    }
    
    supabase.table('TelemetryData').insert(data).execute()
    
    # Calculate and store trust score
    trust_score, mfa_required = calculate_trust_score(
        stride_mapping['risk_level'], 
        stride_mapping['stride_category'],
        telemetry_data
    )
    
    trust_data = {
        'session_id': telemetry_data.get('session_id'),
        'vm_id': telemetry_data.get('vm_id'),
        'vm_agent_id': telemetry_data.get('vm_agent_id'),
        'timestamp': datetime.utcnow().isoformat(),
        'trust_score': trust_score,
        'mfa_required': mfa_required
    }
    
    supabase.table('TrustScore').insert(trust_data).execute()
    
    return jsonify({
        'status': 'success',
        'session_id': telemetry_data.get('session_id'),
        'stride_category': stride_mapping['stride_category'],
        'risk_level': stride_mapping['risk_level'],
        'trust_score': trust_score,
        'mfa_required': mfa_required
    })

@bp.route('/trust_score', methods=['GET'])
@require_auth
def get_trust_score():
    """Get trust score for a session (for regular users)"""
    session_id = request.args.get('session_id')
    supabase = get_supabase_client()
    
    # Fetch the latest trust score for the session_id
    result = supabase.table('TrustScore').select('*').eq('session_id', session_id).order('timestamp', desc=True).limit(1).execute()
    
    if result.data:
        trust_score = result.data[0]['trust_score']
        mfa_required = result.data[0]['mfa_required']
        vm_id = result.data[0]['vm_id']
    else:
        trust_score = None
        mfa_required = None
        vm_id = None
    
    return jsonify({
        'trust_score': trust_score, 
        'mfa_required': mfa_required,
        'vm_id': vm_id,
        'session_id': session_id
    })

@bp.route('/generate_synthetic_telemetry', methods=['POST'])
@require_auth
def generate_and_process_telemetry():
    """Generate and process synthetic telemetry data (for testing)"""
    # Generate synthetic telemetry
    synthetic_data = generate_synthetic_telemetry()
    
    # Process it through the telemetry endpoint
    stride_mapping = map_to_stride(synthetic_data)
    supabase = get_supabase_client()
    
    # Store telemetry data
    telemetry_data = {
        'vm_id': synthetic_data.get('vm_id'),
        'vm_agent_id': 'synthetic-agent',
        'timestamp': synthetic_data.get('timestamp'),
        'event_type': synthetic_data.get('event_type'),
        'stride_category': stride_mapping['stride_category'],
        'risk_level': stride_mapping['risk_level'],
        # Store all 62 features as JSON
        'features': {k: v for k, v in synthetic_data.items() if k.startswith('feature_')}
    }
    
    supabase.table('TelemetryData').insert(telemetry_data).execute()
    
    # Calculate and store trust score
    trust_score, mfa_required = calculate_trust_score(
        stride_mapping['risk_level'], 
        stride_mapping['stride_category'],
        synthetic_data
    )
    
    trust_data = {
        'session_id': synthetic_data.get('session_id'),
        'vm_id': synthetic_data.get('vm_id'),
        'vm_agent_id': 'synthetic-agent',
        'timestamp': synthetic_data.get('timestamp'),
        'trust_score': trust_score,
        'mfa_required': mfa_required
    }
    
    supabase.table('TrustScore').insert(trust_data).execute()
    
    return jsonify({
        'status': 'success', 
        'session_id': synthetic_data.get('session_id'),
        'stride_category': stride_mapping['stride_category'],
        'risk_level': stride_mapping['risk_level'],
        'trust_score': trust_score,
        'mfa_required': mfa_required
    })

@bp.route('/test_sample_data', methods=['GET', 'POST'])
@require_auth
def test_sample_data():
    """Test endpoint using the sample CICIDS2017 JSON file"""
    # Load sample data
    sample_data = load_sample_cicids2017_data()
    if not sample_data:
        return jsonify({'error': 'Sample data file not found'}), 404
    
    # Process the sample data
    stride_mapping = map_to_stride(sample_data)
    
    # For GET requests, just return the processed data without storing in Supabase
    if request.method == 'GET':
        trust_score, mfa_required = calculate_trust_score(
            stride_mapping['risk_level'], 
            stride_mapping['stride_category'], 
            sample_data
        )
        return jsonify({
            'status': 'success (GET - no Supabase storage)', 
            'session_id': sample_data.get('session_id'),
            'stride_category': stride_mapping['stride_category'],
            'risk_level': stride_mapping['risk_level'],
            'trust_score': trust_score,
            'mfa_required': mfa_required,
            'message': 'Use POST method to store data in Supabase'
        })
    
    # For POST requests, store in Supabase
    supabase = get_supabase_client()
    
    # Store telemetry data
    telemetry_data = {
        'vm_id': sample_data.get('vm_id'),
        'vm_agent_id': 'test-agent',
        'timestamp': sample_data.get('timestamp'),
        'event_type': sample_data.get('event_type'),
        'stride_category': stride_mapping['stride_category'],
        'risk_level': stride_mapping['risk_level'],
        # Store all 62 features as JSON
        'features': {k: v for k, v in sample_data.items() if k not in ['session_id', 'vm_id', 'event_type', 'timestamp']}
    }
    
    supabase.table('TelemetryData').insert(telemetry_data).execute()
    
    # Calculate and store trust score
    trust_score, mfa_required = calculate_trust_score(
        stride_mapping['risk_level'], 
        stride_mapping['stride_category'], 
        sample_data
    )
    
    trust_data = {
        'session_id': sample_data.get('session_id'),
        'vm_id': sample_data.get('vm_id'),
        'vm_agent_id': 'test-agent',
        'timestamp': sample_data.get('timestamp'),
        'trust_score': trust_score,
        'mfa_required': mfa_required
    }
    
    supabase.table('TrustScore').insert(trust_data).execute()
    
    return jsonify({
        'status': 'success', 
        'session_id': sample_data.get('session_id'),
        'stride_category': stride_mapping['stride_category'],
        'risk_level': stride_mapping['risk_level'],
        'trust_score': trust_score,
        'mfa_required': mfa_required
    })
