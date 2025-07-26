# ... Function to process telemetry data and map to STRIDE ...
def map_to_stride(telemetry_data):
    # Real CICIDS2017 feature names (replace with actual names from your dataset)
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
    
    # Simple heuristic: analyze feature patterns to determine threat
    avg_feature_value = sum(features.values()) / len(features)
    max_feature_value = max(features.values())
    
    # Determine STRIDE category based on feature patterns
    if avg_feature_value > 80:
        stride_category = 'Denial of Service'
        risk_level = 5
    elif max_feature_value > 90:
        stride_category = 'Elevation of Privilege'
        risk_level = 4
    elif telemetry_data.get('event_type') == 'login_failed':
        stride_category = 'Spoofing'
        risk_level = 3
    elif avg_feature_value > 60:
        stride_category = 'Information Disclosure'
        risk_level = 3
    else:
        stride_category = 'Unknown'
        risk_level = 1
    return {'stride_category': stride_category, 'risk_level': risk_level}
