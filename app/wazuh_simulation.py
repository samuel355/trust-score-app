import json
import random
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class WazuhSimulation:
    """Simulate Wazuh alerts for testing Trust Engine integration"""
    
    def __init__(self):
        self.alert_id_counter = 1000
        self.agent_id_counter = 1
        
    def generate_simulated_agents(self) -> List[Dict]:
        """Generate simulated Wazuh agents"""
        agents = [
            {
                "id": "001",
                "name": "wazuh-agent-ubuntu",
                "ip": "192.168.1.100",
                "os": {
                    "name": "Ubuntu 20.04",
                    "version": "20.04.3 LTS"
                },
                "status": "active",
                "version": "4.12.0"
            },
            {
                "id": "002", 
                "name": "wazuh-agent-centos",
                "ip": "192.168.1.101",
                "os": {
                    "name": "CentOS 8",
                    "version": "8.5.2111"
                },
                "status": "active",
                "version": "4.12.0"
            }
        ]
        return agents
    
    def generate_simulated_alerts(self, agent_id: str = None, limit: int = 10) -> List[Dict]:
        """Generate simulated Wazuh alerts"""
        alerts = []
        
        # Sample alert types with different threat levels
        alert_types = [
            {
                "rule_id": "100001",
                "rule_level": 5,
                "rule_description": "SSH authentication failure",
                "full_log": "sshd[1234]: Failed password for user admin from 192.168.1.50",
                "stride_category": "Spoofing",
                "risk_level": 4
            },
            {
                "rule_id": "100002", 
                "rule_level": 7,
                "rule_description": "Multiple failed SSH login attempts",
                "full_log": "sshd[1234]: Failed password for user root from 192.168.1.51 port 22",
                "stride_category": "Spoofing",
                "risk_level": 5
            },
            {
                "rule_id": "100003",
                "rule_level": 4,
                "rule_description": "File modification detected",
                "full_log": "auditd[567]: SYSCALL arch=c000003e syscall=2 success=yes exit=3 a0=7fff12345678 a1=0 a2=1b6 a3=0 items=1 ppid=1234 pid=5678 auid=1000 uid=0 gid=0 euid=0 suid=0 fsuid=0 egid=0 sgid=0 fsgid=0 tty=pts0 ses=1 comm=\"touch\" exe=\"/usr/bin/touch\" key=\"file_modification\"",
                "stride_category": "Tampering",
                "risk_level": 3
            },
            {
                "rule_id": "100004",
                "rule_level": 6,
                "rule_description": "Suspicious network connection",
                "full_log": "kernel: [UFW BLOCK] IN=eth0 OUT= MAC=00:15:5d:01:ca:05:00:15:5d:01:ca:06:08:00 SRC=192.168.1.200 DST=192.168.1.100 LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=12345 DF PROTO=TCP SPT=12345 DPT=22 WINDOW=29200 RES=0x00 SYN URGP=0",
                "stride_category": "Information Disclosure",
                "risk_level": 3
            },
            {
                "rule_id": "100005",
                "rule_level": 8,
                "rule_description": "Privilege escalation attempt",
                "full_log": "sudo: pam_unix(sudo:auth): authentication failure; logname=admin uid=1000 euid=0 tty=/dev/pts/0 ruser=admin rhost= user=admin",
                "stride_category": "Elevation of Privilege",
                "risk_level": 5
            },
            {
                "rule_id": "100006",
                "rule_level": 3,
                "rule_description": "System resource exhaustion",
                "full_log": "kernel: Out of memory: Kill process 1234 (apache2) score 0 or sacrifice child",
                "stride_category": "Denial of Service",
                "risk_level": 2
            }
        ]
        
        # Generate alerts
        for i in range(limit):
            alert_type = random.choice(alert_types)
            timestamp = datetime.utcnow() - timedelta(minutes=random.randint(1, 60))
            
            alert = {
                "id": str(self.alert_id_counter + i),
                "timestamp": timestamp.isoformat(),
                "agent": {
                    "id": agent_id or "001",
                    "name": f"wazuh-agent-{random.choice(['ubuntu', 'centos'])}"
                },
                "rule": {
                    "id": alert_type["rule_id"],
                    "level": alert_type["rule_level"],
                    "description": alert_type["rule_description"]
                },
                "full_log": alert_type["full_log"],
                "location": f"/var/log/auth.log",
                "syscheck": {},
                "audit": {},
                "mitre": {
                    "technique": ["T1078", "T1021"],
                    "tactic": ["Initial Access", "Lateral Movement"]
                }
            }
            
            alerts.append(alert)
        
        return alerts
    
    def convert_simulated_alert_to_telemetry(self, alert: Dict) -> Dict:
        """Convert simulated Wazuh alert to Trust Engine telemetry format"""
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
                'wazuh_full_log': alert.get('full_log', ''),
                'wazuh_location': alert.get('location', ''),
                'wazuh_syscheck': alert.get('syscheck', {}),
                'wazuh_audit': alert.get('audit', {}),
                'wazuh_mitre': alert.get('mitre', {})
            }
            
            # Add CICIDS2017-style features based on alert content
            telemetry.update(self._extract_cicids_features_from_alert(alert))
            
            return telemetry
            
        except Exception as e:
            logger.error(f"Error converting simulated alert to telemetry: {str(e)}")
            return {}
    
    def _extract_cicids_features_from_alert(self, alert: Dict) -> Dict:
        """Extract CICIDS2017-style features from simulated alert"""
        features = {}
        
        try:
            # Extract network-related features from alert
            full_log = alert.get('full_log', '').lower()
            rule_level = alert.get('rule', {}).get('level', 0)
            
            # Flow Duration (simulated based on alert frequency)
            features['Flow Duration'] = random.uniform(0.1, 2.0)
            
            # Packet counts (extracted from log patterns)
            if 'packet' in full_log or 'tcp' in full_log:
                features['Total Fwd Packets'] = random.randint(5, 50)
                features['Total Backward Packets'] = random.randint(3, 25)
            else:
                features['Total Fwd Packets'] = 1
                features['Total Backward Packets'] = 1
            
            # Packet lengths
            features['Total Length of Fwd Packets'] = features['Total Fwd Packets'] * random.randint(32, 1500)
            features['Total Length of Bwd Packets'] = features['Total Backward Packets'] * random.randint(32, 1500)
            
            # Flow rates
            features['Flow Bytes/s'] = random.randint(500, 5000)
            features['Flow Packets/s'] = random.randint(5, 50)
            
            # IAT (Inter-Arrival Time) features
            features['Flow IAT Mean'] = random.uniform(0.01, 0.5)
            features['Flow IAT Std'] = random.uniform(0.005, 0.1)
            features['Flow IAT Max'] = random.uniform(0.1, 1.0)
            features['Flow IAT Min'] = random.uniform(0.001, 0.05)
            
            # Flag counts (based on alert type and rule level)
            if rule_level > 5:
                features['SYN Flag Count'] = 1
                features['ACK Flag Count'] = 1
                features['RST Flag Count'] = 1
            elif rule_level > 3:
                features['SYN Flag Count'] = 1
                features['ACK Flag Count'] = 1
                features['RST Flag Count'] = 0
            else:
                features['SYN Flag Count'] = 0
                features['ACK Flag Count'] = 0
                features['RST Flag Count'] = 0
            
            # Window sizes
            features['Init_Win_bytes_forward'] = random.randint(1024, 65535)
            features['Init_Win_bytes_backward'] = random.randint(1024, 65535)
            
            # Add more features based on alert content
            if 'ssh' in full_log or 'brute' in full_log:
                features['PSH Flag Count'] = 1
                features['URG Flag Count'] = 0
            else:
                features['PSH Flag Count'] = 0
                features['URG Flag Count'] = 0
            
            # Fill remaining CICIDS2017 features with realistic values
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
                    if 'Length' in feature or 'Size' in feature:
                        features[feature] = random.randint(32, 1500)
                    elif 'Count' in feature or 'Flags' in feature:
                        features[feature] = random.randint(0, 5)
                    elif 'Ratio' in feature:
                        features[feature] = random.uniform(0.1, 10.0)
                    elif 'Rate' in feature or 'Packets/s' in feature:
                        features[feature] = random.randint(1, 100)
                    else:
                        features[feature] = random.randint(0, 1000)
            
        except Exception as e:
            logger.error(f"Error extracting CICIDS features: {str(e)}")
        
        return features
    
    def test_connection(self) -> Dict:
        """Simulate successful Wazuh connection"""
        agents = self.generate_simulated_agents()
        alerts = self.generate_simulated_alerts(limit=5)
        
        return {
            'status': 'success',
            'message': 'Wazuh simulation connection successful',
            'agents_count': len(agents),
            'recent_alerts_count': len(alerts),
            'wazuh_url': 'https://localhost:55000 (simulated)',
            'simulation_mode': True
        }

# Global instance
wazuh_simulation = WazuhSimulation() 