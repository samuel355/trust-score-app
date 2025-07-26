def calculate_trust_score(risk_level, stride_category, telemetry_data=None):
    # Enhanced scoring with feature analysis
    base_score = 100 - (risk_level * 15)
    
    if telemetry_data:
        # Real CICIDS2017 feature names (same as in telemetry.py)
        real_feature_names = [
            'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
            'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
            'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
            'Fwd Packet Length Std', 'Bwd Packet Length Max', 'Bwd Packet Length Min',
            'Bwd Packet Length Mean', 'Bwd Packet Length Std', 'Flow Bytes/s',
            'Flow Packets/s', 'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Max',
            'Flow IAT Min', 'Fwd IAT Total', 'Fwd IAT Mean', 'Fwd IAT Std',
            'Fwd IAT Max', 'Fwd IAT Min', 'Bwd IAT Total', 'Bwd IAT Mean',
            'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min', 'Fwd PSH Flags',
            'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags', 'Fwd Header Length',
            'Bwd Header Length', 'Fwd Packets/s', 'Bwd Packets/s', 'Min Packet Length',
            'Max Packet Length', 'Packet Length Mean', 'Packet Length Std',
            'Packet Length Variance', 'FIN Flag Count', 'SYN Flag Count',
            'RST Flag Count', 'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count',
            'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio', 'Average Packet Size',
            'Avg Fwd Segment Size', 'Avg Bwd Segment Size', 'Fwd Header Length.1',
            'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk', 'Fwd Avg Bulk Rate',
            'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate',
            'Subflow Fwd Packets', 'Subflow Fwd Bytes', 'Subflow Bwd Packets',
            'Subflow Bwd Bytes', 'Init_Win_bytes_forward', 'Init_Win_bytes_backward',
            'act_data_pkt_fwd', 'min_seg_size_forward'
        ]
        
        # Extract real features from telemetry data
        features = {name: telemetry_data.get(name, 0) for name in real_feature_names}
        
        # Analyze feature patterns for additional scoring
        feature_variance = sum((v - sum(features.values())/len(features))**2 for v in features.values()) / len(features)
        
        # Adjust score based on feature variance (high variance = suspicious)
        if feature_variance > 1000:
            base_score -= 20
        elif feature_variance > 500:
            base_score -= 10
    else:
        # Fallback to original logic
        stride_weights = {
            'Spoofing': 1.5, 'Tampering': 1.4, 'Repudiation': 1.3,
            'Information Disclosure': 1.2, 'Denial of Service': 1.6,
            'Elevation of Privilege': 1.7, 'Unknown': 1.0
        }
        weight = stride_weights.get(stride_category, 1.0)
        base_score = max(0, 100 - (risk_level * 15 * weight))
    
    trust_score = max(0, min(100, base_score))
    mfa_required = trust_score < 60
    return trust_score, mfa_required
