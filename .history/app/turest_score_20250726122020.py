def calculate_trust_score(risk_level, stride_category, telemetry_data=None):
    # Enhanced scoring with feature analysis
    base_score = 100 - (risk_level * 15)
    
    if telemetry_data:
        # Analyze feature patterns for additional scoring
        features = {k: v for k, v in telemetry_data.items() if k.startswith('feature_')}
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
