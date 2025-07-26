from enum import Enum
from typing import Dict, List, Tuple
from dataclasses import dataclass

class MFA_Level(Enum):
    """MFA authentication levels"""
    PASSWORD_ONLY = 1
    PASSWORD_OTP = 2
    PASSWORD_OTP_DEVICE = 3
    BLOCKED = 4

@dataclass
class AuthenticationPolicy:
    """Authentication policy configuration"""
    min_trust_score: int
    mfa_level: MFA_Level
    description: str

class AdaptiveMFA:
    """Adaptive Multi-Factor Authentication based on trust scores and STRIDE analysis"""
    
    def __init__(self):
        # Define authentication policies based on trust scores
        self.policies = [
            AuthenticationPolicy(80, MFA_Level.PASSWORD_ONLY, "High trust - Password only"),
            AuthenticationPolicy(60, MFA_Level.PASSWORD_OTP, "Medium trust - Password + OTP"),
            AuthenticationPolicy(40, MFA_Level.PASSWORD_OTP_DEVICE, "Low trust - Password + OTP + Device"),
            AuthenticationPolicy(0, MFA_Level.BLOCKED, "Very low trust - Access blocked")
        ]
        
        # STRIDE threat multipliers
        self.stride_multipliers = {
            'Spoofing': 1.5,      # Identity threats - require stronger auth
            'Tampering': 1.4,     # Data integrity threats
            'Repudiation': 1.3,   # Logging/audit threats
            'Information Disclosure': 1.2,  # Data exposure threats
            'Denial of Service': 1.1,       # Availability threats
            'Elevation of Privilege': 1.6,  # Authorization threats - highest risk
            'Unknown': 1.0        # Default multiplier
        }
    
    def calculate_adaptive_trust_score(self, base_trust_score: int, stride_category: str, risk_level: int) -> int:
        """Calculate adaptive trust score considering STRIDE threats"""
        # Apply STRIDE multiplier
        multiplier = self.stride_multipliers.get(stride_category, 1.0)
        
        # Adjust trust score based on STRIDE threat
        adjusted_score = base_trust_score * multiplier
        
        # Apply risk level penalty
        risk_penalty = (risk_level - 1) * 10  # Each risk level reduces score by 10
        adjusted_score -= risk_penalty
        
        # Ensure score is within bounds
        return max(0, min(100, int(adjusted_score)))
    
    def determine_mfa_requirement(self, trust_score: int, stride_category: str, risk_level: int) -> Dict:
        """Determine MFA requirements based on trust score and STRIDE analysis"""
        
        # Calculate adaptive trust score
        adaptive_score = self.calculate_adaptive_trust_score(trust_score, stride_category, risk_level)
        
        # Find appropriate policy
        selected_policy = None
        for policy in self.policies:
            if adaptive_score >= policy.min_trust_score:
                selected_policy = policy
                break
        
        if not selected_policy:
            selected_policy = self.policies[-1]  # Use blocked policy
        
        # Build response
        result = {
            'mfa_level': selected_policy.mfa_level.value,
            'mfa_level_name': selected_policy.mfa_level.name,
            'required_factors': self._get_required_factors(selected_policy.mfa_level),
            'trust_score': trust_score,
            'adaptive_trust_score': adaptive_score,
            'stride_category': stride_category,
            'risk_level': risk_level,
            'description': selected_policy.description,
            'access_granted': selected_policy.mfa_level != MFA_Level.BLOCKED,
            'reasoning': self._get_reasoning(trust_score, stride_category, risk_level, adaptive_score)
        }
        
        return result
    
    def _get_required_factors(self, mfa_level: MFA_Level) -> List[str]:
        """Get list of required authentication factors"""
        factors = {
            MFA_Level.PASSWORD_ONLY: ['password'],
            MFA_Level.PASSWORD_OTP: ['password', 'otp'],
            MFA_Level.PASSWORD_OTP_DEVICE: ['password', 'otp', 'device_fingerprint'],
            MFA_Level.BLOCKED: []
        }
        return factors.get(mfa_level, [])
    
    def _get_reasoning(self, trust_score: int, stride_category: str, risk_level: int, adaptive_score: int) -> str:
        """Generate human-readable reasoning for MFA decision"""
        reasoning = []
        
        # Base trust score reasoning
        if trust_score >= 80:
            reasoning.append("High base trust score")
        elif trust_score >= 60:
            reasoning.append("Medium base trust score")
        elif trust_score >= 40:
            reasoning.append("Low base trust score")
        else:
            reasoning.append("Very low base trust score")
        
        # STRIDE threat reasoning
        if stride_category != 'Unknown':
            reasoning.append(f"STRIDE threat detected: {stride_category}")
        
        # Risk level reasoning
        if risk_level > 3:
            reasoning.append(f"High risk level ({risk_level})")
        elif risk_level > 1:
            reasoning.append(f"Elevated risk level ({risk_level})")
        
        # Adaptive score reasoning
        if adaptive_score < trust_score:
            reasoning.append(f"Trust score reduced to {adaptive_score} due to threats")
        
        return "; ".join(reasoning)
    
    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))
    
    def validate_device_fingerprint(self, fingerprint: str, user_id: str) -> bool:
        """Validate device fingerprint (placeholder implementation)"""
        # In production, this would:
        # 1. Check against stored device fingerprints for the user
        # 2. Validate fingerprint authenticity
        # 3. Check for suspicious changes
        
        # For now, return True if fingerprint is provided
        return bool(fingerprint and len(fingerprint) > 10)
    
    def get_mfa_challenge(self, mfa_level: MFA_Level, user_id: str) -> Dict:
        """Generate MFA challenge based on required level"""
        challenge = {
            'mfa_level': mfa_level.value,
            'required_factors': self._get_required_factors(mfa_level),
            'challenge_id': f"challenge_{user_id}_{hash(str(mfa_level))}",
            'expires_in': 300  # 5 minutes
        }
        
        if mfa_level in [MFA_Level.PASSWORD_OTP, MFA_Level.PASSWORD_OTP_DEVICE]:
            challenge['otp'] = self.generate_otp()
            challenge['otp_message'] = f"Your OTP is: {challenge['otp']}"
        
        if mfa_level == MFA_Level.PASSWORD_OTP_DEVICE:
            challenge['device_fingerprint_required'] = True
            challenge['device_fingerprint_instructions'] = "Please provide device fingerprint"
        
        return challenge

# Global instance
adaptive_mfa = AdaptiveMFA() 