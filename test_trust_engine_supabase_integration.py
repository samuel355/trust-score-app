#!/usr/bin/env python3
"""
Test Trust Engine's Supabase integration
"""

from app.utils import get_supabase_client
from app.telemetry import map_to_stride
from app.turest_score import calculate_trust_score
from app.wazuh_simulation import wazuh_simulation
from datetime import datetime

def test_trust_engine_integration():
    """Test the exact integration flow used by Trust Engine"""
    
    print("Testing Trust Engine's Supabase integration...")
    
    try:
        # Step 1: Get simulated alerts (like Trust Engine does)
        alerts = wazuh_simulation.generate_simulated_alerts(limit=1)
        print(f"✅ Generated {len(alerts)} simulated alerts")
        
        # Step 2: Process each alert (like Trust Engine does)
        for alert in alerts:
            print(f"\nProcessing alert: {alert.get('id')}")
            
            # Convert to telemetry
            telemetry = wazuh_simulation.convert_simulated_alert_to_telemetry(alert)
            print(f"✅ Converted to telemetry: {telemetry.get('event_type')}")
            
            # Process through STRIDE analysis
            stride_mapping = map_to_stride(telemetry)
            print(f"✅ STRIDE mapping: {stride_mapping['stride_category']} (risk: {stride_mapping['risk_level']})")
            
            # Calculate trust score
            trust_score, mfa_required = calculate_trust_score(
                stride_mapping['risk_level'],
                stride_mapping['stride_category'],
                telemetry
            )
            print(f"✅ Trust score: {trust_score}, MFA required: {mfa_required}")
            
            # Store in Supabase (like Trust Engine does)
            try:
                supabase = get_supabase_client()
                
                # Insert telemetry data
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
                
                result = supabase.table('TelemetryData').insert(telemetry_data).execute()
                print("✅ TelemetryData stored successfully")
                
                # Insert trust score
                trust_data = {
                    'session_id': telemetry.get('session_id'),
                    'vm_id': telemetry.get('vm_id'),
                    'vm_agent_id': 'wazuh-simulation-agent',
                    'timestamp': telemetry.get('timestamp'),
                    'trust_score': trust_score,
                    'mfa_required': mfa_required
                }
                
                result = supabase.table('TrustScore').insert(trust_data).execute()
                print("✅ TrustScore stored successfully")
                
                print("🎉 SUCCESS: Trust Engine integration working!")
                return True
                
            except Exception as e:
                print(f"❌ Supabase storage failed: {str(e)}")
                return False
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_trust_engine_integration() 