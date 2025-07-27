from flask import Blueprint, request, jsonify
from app.telemetry import map_to_stride
from app.utils import get_supabase_client, generate_synthetic_telemetry, load_sample_cicids2017_data, get_elasticsearch_client, index_to_elasticsearch
from app.elasticsearch_integration import elasticsearch_integration
from app.wazuh_integration import wazuh_integration
from app.wazuh_simulation import wazuh_simulation
from datetime import datetime
from app.turest_score import calculate_trust_score
from app.auth import require_auth, require_vm_agent

bp = Blueprint('routes', __name__)

# --- Elasticsearch Indexing Docstring ---
"""
Elasticsearch Index Structure for Trust Engine (Kibana-ready):

1. telemetrydata index:
   - vm_id: str
   - vm_agent_id: str
   - timestamp: ISO8601 str
   - event_type: str
   - stride_category: str
   - risk_level: int
   - features: dict (all 62 features)

2. trustscore index:
   - session_id: str
   - vm_id: str
   - vm_agent_id: str
   - timestamp: ISO8601 str
   - trust_score: float
   - mfa_required: bool

3. wazuh_alerts index:
   - alert_id: str
   - agent_id: str
   - agent_name: str
   - timestamp: ISO8601 str
   - rule_id: str
   - rule_level: int
   - rule_description: str
   - stride_category: str
   - risk_level: int
   - trust_score: float
   - mfa_required: bool
   - raw_alert: dict (full Wazuh alert)
"""

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
            'POST /test_sample_data': 'Test with sample CICIDS2017 data (users)',
            'GET /wazuh/test-public': 'Test Wazuh connection (public)',
            'GET /wazuh/test': 'Test Wazuh connection (authenticated)',
            'GET /wazuh/agents': 'Get Wazuh agents',
            'GET /wazuh/alerts': 'Get Wazuh alerts',
            'POST /wazuh/process-alerts': 'Process Wazuh alerts as telemetry',
            'GET /wazuh/simulation/test': 'Test Wazuh simulation (public)',
            'GET /wazuh/simulation/agents': 'Get simulated Wazuh agents (public)',
            'GET /wazuh/simulation/alerts': 'Get simulated Wazuh alerts (public)',
            'POST /wazuh/simulation/process': 'Process simulated alerts as telemetry (public)'
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
    # Enhanced Elasticsearch indexing
    try:
        elasticsearch_integration.index_telemetry(data)
    except Exception as es_exc:
        print(f"[Elasticsearch] Telemetry indexing failed: {es_exc}")

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
    # Index trust score to Elasticsearch
    try:
        elasticsearch_integration.index_trust_score(trust_data)
    except Exception as es_exc:
        print(f"[Elasticsearch] TrustScore indexing failed: {es_exc}")

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

# Wazuh Integration Endpoints

@bp.route('/wazuh/test-public', methods=['GET'])
def test_wazuh_connection_public():
    """Test connection to Wazuh Docker instance (public endpoint for testing)"""
    try:
        result = wazuh_integration.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Wazuh test failed: {str(e)}'
        }), 500

@bp.route('/wazuh/test', methods=['GET'])
@require_auth
def test_wazuh_connection():
    """Test connection to Wazuh Docker instance"""
    try:
        result = wazuh_integration.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Wazuh test failed: {str(e)}'
        }), 500

@bp.route('/wazuh/agents', methods=['GET'])
@require_auth
def get_wazuh_agents():
    """Get list of Wazuh agents"""
    try:
        agents = wazuh_integration.get_agents()
        return jsonify({
            'status': 'success',
            'agents': agents,
            'count': len(agents)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get Wazuh agents: {str(e)}'
        }), 500

@bp.route('/wazuh/alerts', methods=['GET'])
@require_auth
def get_wazuh_alerts():
    """Get recent Wazuh alerts"""
    try:
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 50))

        alerts = wazuh_integration.get_alerts(agent_id=agent_id, limit=limit)
        return jsonify({
            'status': 'success',
            'alerts': alerts,
            'count': len(alerts)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get Wazuh alerts: {str(e)}'
        }), 500

@bp.route('/wazuh/process-alerts', methods=['POST'])
@require_auth
def process_wazuh_alerts():
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        limit = data.get('limit', 10)
        alerts = wazuh_integration.get_alerts(agent_id=agent_id, limit=limit)
        processed_count = 0
        telemetry_results = []
        for alert in alerts:
            telemetry = wazuh_integration.convert_wazuh_alert_to_telemetry(alert)
            if telemetry:
                stride_mapping = map_to_stride(telemetry)
                trust_score, mfa_required = calculate_trust_score(
                    stride_mapping['risk_level'],
                    stride_mapping['stride_category'],
                    telemetry
                )
                supabase = get_supabase_client()
                telemetry_data = {
                    'vm_id': telemetry.get('vm_id'),
                    'vm_agent_id': 'wazuh-agent',
                    'timestamp': telemetry.get('timestamp'),
                    'event_type': telemetry.get('event_type'),
                    'stride_category': stride_mapping['stride_category'],
                    'risk_level': stride_mapping['risk_level'],
                    'features': {k: v for k, v in telemetry.items()
                                if k not in ['vm_id', 'vm_agent_id', 'event_type', 'timestamp', 'session_id']}
                }
                supabase.table('TelemetryData').insert(telemetry_data).execute()
                try:
                    elasticsearch_integration.index_telemetry(telemetry_data)
                except Exception as es_exc:
                    print(f"[Elasticsearch] Telemetry indexing failed: {type(es_exc).__name__}: {es_exc}")
                trust_data = {
                    'session_id': telemetry.get('session_id'),
                    'vm_id': telemetry.get('vm_id'),
                    'vm_agent_id': 'wazuh-agent',
                    'timestamp': telemetry.get('timestamp'),
                    'trust_score': trust_score,
                    'mfa_required': mfa_required
                }
                supabase.table('TrustScore').insert(trust_data).execute()
                try:
                    elasticsearch_integration.index_trust_score(trust_data)
                except Exception as es_exc:
                    print(f"[Elasticsearch] TrustScore indexing failed: {type(es_exc).__name__}: {es_exc}")
                # --- Index Wazuh alert as a separate document ---
                wazuh_alert_doc = {
                    'alert_id': alert.get('id'),
                    'agent_id': alert.get('agent', {}).get('id'),
                    'agent_name': alert.get('agent', {}).get('name'),
                    'timestamp': alert.get('timestamp', telemetry.get('timestamp')),
                    'rule_id': alert.get('rule', {}).get('id'),
                    'rule_level': alert.get('rule', {}).get('level'),
                    'rule_description': alert.get('rule', {}).get('description'),
                    'stride_category': stride_mapping['stride_category'],
                    'risk_level': stride_mapping['risk_level'],
                    'trust_score': trust_score,
                    'mfa_required': mfa_required,
                    'raw_alert': alert
                }
                try:
                    elasticsearch_integration.index_wazuh_alert(wazuh_alert_doc)
                except Exception as es_exc:
                    print(f"[Elasticsearch] Wazuh alert indexing failed: {type(es_exc).__name__}: {es_exc}")
                telemetry_results.append({
                    'wazuh_alert_id': alert.get('id'),
                    'agent_name': alert.get('agent', {}).get('name'),
                    'rule_description': alert.get('rule', {}).get('description'),
                    'stride_category': stride_mapping['stride_category'],
                    'risk_level': stride_mapping['risk_level'],
                    'trust_score': trust_score,
                    'mfa_required': mfa_required
                })
                processed_count += 1
        return jsonify({
            'status': 'success',
            'message': f'Processed {processed_count} Wazuh alerts',
            'processed_count': processed_count,
            'results': telemetry_results
        })
    except Exception as e:
        print(f"[Elasticsearch] process_wazuh_alerts failed: {type(e).__name__}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to process Wazuh alerts: {str(e)}'
        }), 500

# Wazuh Simulation Endpoints (for testing without real Wazuh credentials)

@bp.route('/wazuh/simulation/test', methods=['GET'])
def test_wazuh_simulation():
    """Test Wazuh simulation (public endpoint for testing)"""
    try:
        result = wazuh_simulation.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Wazuh simulation test failed: {str(e)}'
        }), 500

@bp.route('/wazuh/simulation/agents', methods=['GET'])
def get_simulated_wazuh_agents():
    """Get simulated Wazuh agents (public endpoint for testing)"""
    try:
        agents = wazuh_simulation.generate_simulated_agents()
        return jsonify({
            'status': 'success',
            'agents': agents,
            'count': len(agents),
            'simulation_mode': True
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get simulated Wazuh agents: {str(e)}'
        }), 500

@bp.route('/wazuh/simulation/alerts', methods=['GET'])
def get_simulated_wazuh_alerts():
    """Get simulated Wazuh alerts (public endpoint for testing)"""
    try:
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 10))

        alerts = wazuh_simulation.generate_simulated_alerts(agent_id=agent_id, limit=limit)
        return jsonify({
            'status': 'success',
            'alerts': alerts,
            'count': len(alerts),
            'simulation_mode': True
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get simulated Wazuh alerts: {str(e)}'
        }), 500

@bp.route('/wazuh/simulation/process', methods=['POST'])
def process_simulated_wazuh_alerts():
    """Process simulated Wazuh alerts and convert to telemetry data (public endpoint for testing)"""
    try:
        data = request.get_json() or {}
        agent_id = data.get('agent_id')
        limit = data.get('limit', 5)

        # Get simulated alerts
        alerts = wazuh_simulation.generate_simulated_alerts(agent_id=agent_id, limit=limit)

        processed_count = 0
        telemetry_results = []

        for alert in alerts:
            # Convert simulated alert to telemetry format
            telemetry = wazuh_simulation.convert_simulated_alert_to_telemetry(alert)

            if telemetry:
                # Process through STRIDE analysis
                stride_mapping = map_to_stride(telemetry)

                # Calculate trust score
                trust_score, mfa_required = calculate_trust_score(
                    stride_mapping['risk_level'],
                    stride_mapping['stride_category'],
                    telemetry
                )

                # Try to store in Supabase (optional for testing)
                try:
                    supabase = get_supabase_client()

                    telemetry_data = {
                        'vm_id': telemetry.get('vm_id'),
                        'vm_agent_id': 'wazuh-simulation-agent',
                        'timestamp': telemetry.get('timestamp'),
                        'event_type': telemetry.get('event_type'),
                        'stride_category': stride_mapping['stride_category'],
                        'risk_level': stride_mapping['risk_level'],
                        'features': {k: v for k, v in telemetry.items()
                                    if k not in ['vm_id', 'vm_agent_id', 'event_type', 'timestamp', 'session_id']}
                    }

                    supabase.table('TelemetryData').insert(telemetry_data).execute()

                    trust_data = {
                        'session_id': telemetry.get('session_id'),
                        'vm_id': telemetry.get('vm_id'),
                        'vm_agent_id': 'wazuh-simulation-agent',
                        'timestamp': telemetry.get('timestamp'),
                        'trust_score': trust_score,
                        'mfa_required': mfa_required
                    }

                    supabase.table('TrustScore').insert(trust_data).execute()
                    storage_status = "stored in Supabase"
                except Exception as e:
                    storage_status = f"Supabase storage failed: {type(e).__name__}: {str(e)}"

                telemetry_results.append({
                    'wazuh_alert_id': alert.get('id'),
                    'agent_name': alert.get('agent', {}).get('name'),
                    'rule_description': alert.get('rule', {}).get('description'),
                    'rule_level': alert.get('rule', {}).get('level'),
                    'stride_category': stride_mapping['stride_category'],
                    'risk_level': stride_mapping['risk_level'],
                    'trust_score': trust_score,
                    'mfa_required': mfa_required,
                    'storage_status': storage_status,
                    'simulation_mode': True
                })

                processed_count += 1

        return jsonify({
            'status': 'success',
            'message': f'Processed {processed_count} simulated Wazuh alerts',
            'processed_count': processed_count,
            'results': telemetry_results,
            'simulation_mode': True
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to process simulated Wazuh alerts: {str(e)}'
        }), 500
