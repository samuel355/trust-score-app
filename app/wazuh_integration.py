import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WazuhIntegration:
    """Wazuh integration for real-time log collection and alert processing"""

    def __init__(self):
        self.wazuh_url = Config.WAZUH_API_URL
        self.wazuh_username = Config.WAZUH_API_USERNAME
        self.wazuh_password = Config.WAZUH_API_PASSWORD
        self.session = requests.Session()
        self.auth_token = None

    def authenticate(self) -> bool:
        """Authenticate with Wazuh API"""
        try:
            auth_url = f"{self.wazuh_url}/security/user/authenticate"

            logger.info(f"Attempting Wazuh authentication with URL: {auth_url}")
            logger.info(f"Username: {self.wazuh_username}")
            logger.info(f"Password: {'*' * len(self.wazuh_password)}")

            # Use Basic Authentication with GET request (not POST with JSON)
            response = self.session.get(auth_url, auth=(self.wazuh_username, self.wazuh_password), verify=Config.WAZUH_SSL_VERIFY)

            if response.status_code == 200:
                self.auth_token = response.json()['data']['token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                logger.info("Successfully authenticated with Wazuh API")
                return True
            else:
                logger.error(f"Wazuh authentication failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Wazuh authentication error: {str(e)}")
            return False

    def get_agents(self) -> List[Dict]:
        """Get list of Wazuh agents"""
        try:
            if not self.auth_token:
                if not self.authenticate():
                    return []

            agents_url = f"{self.wazuh_url}/agents"
            response = self.session.get(agents_url, verify=Config.WAZUH_SSL_VERIFY)

            if response.status_code == 200:
                agents = response.json()['data']['affected_items']
                logger.info(f"Retrieved {len(agents)} Wazuh agents")
                return agents
            else:
                logger.error(f"Failed to get agents: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error getting agents: {str(e)}")
            return []

    def get_alerts(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent alerts from Wazuh"""
        try:
            if not self.auth_token:
                if not self.authenticate():
                    return []

            alerts_url = f"{self.wazuh_url}/alerts"
            params = {
                'limit': limit,
                'sort': '-timestamp'
            }

            if agent_id:
                params['agents'] = agent_id

            response = self.session.get(alerts_url, params=params, verify=Config.WAZUH_SSL_VERIFY)

            if response.status_code == 200:
                alerts = response.json()['data']['affected_items']
                logger.info(f"Retrieved {len(alerts)} alerts")
                return alerts
            else:
                logger.error(f"Failed to get alerts: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            return []

    def get_agent_logs(self, agent_id: str, limit: int = 100) -> List[Dict]:
        """Get logs from a specific agent"""
        try:
            if not self.auth_token:
                if not self.authenticate():
                    return []

            logs_url = f"{self.wazuh_url}/agents/{agent_id}/logs"
            params = {
                'limit': limit,
                'sort': '-timestamp'
            }

            response = self.session.get(logs_url, params=params, verify=Config.WAZUH_SSL_VERIFY)

            if response.status_code == 200:
                logs = response.json()['data']['affected_items']
                logger.info(f"Retrieved {len(logs)} logs from agent {agent_id}")
                return logs
            else:
                logger.error(f"Failed to get logs for agent {agent_id}: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error getting logs for agent {agent_id}: {str(e)}")
            return []

    def convert_wazuh_alert_to_telemetry(self, alert: Dict) -> Dict:
        """Convert Wazuh alert to Trust Engine telemetry format"""
        try:
            # Extract relevant fields from Wazuh alert
            telemetry = {
                'session_id': f"wazuh_{alert.get('id', 'unknown')}",
                'vm_id': f"agent_{alert.get('agent', {}).get('id', 'unknown')}",
                'event_type': 'wazuh_alert',
                'timestamp': alert.get('timestamp', datetime.utcnow().isoformat()),
                'wazuh_alert_id': alert.get('id'),
                'wazuh_rule_id': alert.get('rule', {}).get('id'),
                'wazuh_rule_level': alert.get('rule', {}).get('level'),
                'wazuh_rule_description': alert.get('rule', {}).get('description'),
                'wazuh_agent_name': alert.get('agent', {}).get('name'),
                'wazuh_agent_ip': alert.get('agent', {}).get('ip'),
                'wazuh_agent_os': alert.get('agent', {}).get('os', {}).get('name'),
                'wazuh_full_log': alert.get('full_log', ''),
                'wazuh_location': alert.get('location', ''),
                'wazuh_syscheck': alert.get('syscheck', {}),
                'wazuh_audit': alert.get('audit', {}),
                'wazuh_mitre': alert.get('rule', {}).get('mitre', {})
            }

            # Add CICIDS2017-style features based on alert content
            telemetry.update(self._extract_cicids_features(alert))

            return telemetry

        except Exception as e:
            logger.error(f"Error converting Wazuh alert to telemetry: {str(e)}")
            return {}

    def _extract_cicids_features(self, alert: Dict) -> Dict:
        """Extract CICIDS2017-style features from Wazuh alert"""
        features = {}

        try:
            # Extract network-related features from alert
            full_log = alert.get('full_log', '').lower()

            # Flow Duration (simulated based on alert frequency)
            features['Flow Duration'] = 0.1  # Default value

            # Packet counts (extracted from log patterns)
            if 'packet' in full_log:
                features['Total Fwd Packets'] = 10
                features['Total Backward Packets'] = 5
            else:
                features['Total Fwd Packets'] = 1
                features['Total Backward Packets'] = 1

            # Packet lengths
            features['Total Length of Fwd Packets'] = features['Total Fwd Packets'] * 64
            features['Total Length of Bwd Packets'] = features['Total Backward Packets'] * 64

            # Flow rates
            features['Flow Bytes/s'] = 1000
            features['Flow Packets/s'] = 10

            # IAT (Inter-Arrival Time) features
            features['Flow IAT Mean'] = 0.1
            features['Flow IAT Std'] = 0.05
            features['Flow IAT Max'] = 0.2
            features['Flow IAT Min'] = 0.01

            # Flag counts (based on alert type)
            rule_level = alert.get('rule', {}).get('level', 0)
            if rule_level > 10:
                features['SYN Flag Count'] = 1
                features['ACK Flag Count'] = 1
            else:
                features['SYN Flag Count'] = 0
                features['ACK Flag Count'] = 0

            # Window sizes
            features['Init_Win_bytes_forward'] = 65535
            features['Init_Win_bytes_backward'] = 65535

            # Add more features based on alert content
            if 'brute' in full_log or 'ssh' in full_log:
                features['RST Flag Count'] = 1
                features['PSH Flag Count'] = 1
            else:
                features['RST Flag Count'] = 0
                features['PSH Flag Count'] = 0

            # Fill remaining CICIDS2017 features with default values
            remaining_features = [
                'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
                'Fwd Packet Length Std', 'Bwd Packet Length Max', 'Bwd Packet Length Min',
                'Bwd Packet Length Mean', 'Bwd Packet Length Std', 'Fwd IAT Total',
                'Fwd IAT Mean', 'Fwd IAT Std', 'Fwd IAT Max', 'Fwd IAT Min',
                'Bwd IAT Total', 'Bwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Max',
                'Bwd IAT Min', 'Fwd PSH Flags', 'Bwd PSH Flags', 'Fwd URG Flags',
                'Bwd URG Flags', 'Fwd Header Length', 'Bwd Header Length',
                'Fwd Packets/s', 'Bwd Packets/s', 'Min Packet Length', 'Max Packet Length',
                'Packet Length Mean', 'Packet Length Std', 'Packet Length Variance',
                'FIN Flag Count', 'URG Flag Count', 'CWE Flag Count', 'ECE Flag Count',
                'Down/Up Ratio', 'Average Packet Size', 'Avg Fwd Segment Size',
                'Avg Bwd Segment Size', 'Fwd Header Length.1', 'Fwd Avg Bytes/Bulk',
                'Fwd Avg Packets/Bulk', 'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk',
                'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate', 'Subflow Fwd Packets',
                'Subflow Fwd Bytes', 'Subflow Bwd Packets', 'Subflow Bwd Bytes',
                'act_data_pkt_fwd', 'min_seg_size_forward'
            ]

            for feature in remaining_features:
                if feature not in features:
                    features[feature] = 0

        except Exception as e:
            logger.error(f"Error extracting CICIDS features: {str(e)}")

        return features

    def get_realtime_alerts(self, callback_func=None) -> None:
        """Get real-time alerts and process them"""
        try:
            if not self.auth_token:
                if not self.authenticate():
                    return

            # Get recent alerts
            alerts = self.get_alerts(limit=50)

            for alert in alerts:
                # Convert to telemetry format
                telemetry = self.convert_wazuh_alert_to_telemetry(alert)

                if telemetry and callback_func:
                    # Send to Trust Engine via callback
                    callback_func(telemetry)

                logger.info(f"Processed Wazuh alert {alert.get('id')} for agent {alert.get('agent', {}).get('name')}")

        except Exception as e:
            logger.error(f"Error in real-time alert processing: {str(e)}")

    def test_connection(self) -> Dict:
        """Test Wazuh API connection"""
        try:
            if self.authenticate():
                agents = self.get_agents()
                alerts = self.get_alerts(limit=5)

                return {
                    'status': 'success',
                    'message': 'Wazuh connection successful',
                    'agents_count': len(agents),
                    'recent_alerts_count': len(alerts),
                    'wazuh_url': self.wazuh_url
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Wazuh authentication failed',
                    'wazuh_url': self.wazuh_url
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Wazuh connection error: {str(e)}',
                'wazuh_url': self.wazuh_url
            }

# Global instance
wazuh_integration = WazuhIntegration()
