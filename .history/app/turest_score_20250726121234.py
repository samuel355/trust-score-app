def calculate_trust_score(risk_level, stride_category):
    # Example weights for STRIDE categories
    stride_weights = {
        'Spoofing': 1.5,
        'Tampering': 1.4,
        'Repudiation': 1.3,
        'Information Disclosure': 1.2,
        'Denial of Service': 1.6,
        'Elevation of Privilege': 1.7,
        'Unknown': 1.0
    }
    weight = stride_weights.get(stride_category, 1.0)
    # Trust score: higher risk = lower trust (out of 100)
    trust_score = max(0, 100 - (risk_level * 15 * weight))
    # Require MFA if trust score below threshold
    mfa_required = trust_score < 60
    return trust_score, mfa_required
