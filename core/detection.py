# core/detection.py
import re


class DetectionEngine:
    def __init__(self):
        self.signatures = {
            "SQL_Injection": {
                "patterns": [
                    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
                    r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
                    r"SELECT\s+[\*\w]+\s+FROM",
                    r"UNION\s+(ALL\s+)?SELECT",
                    r"(DROP|ALTER|TRUNCATE)\s+TABLE",
                    r"INSERT\s+INTO\s+\w+",
                    r"OR\s+1\s*=\s*1",
                    r";\s*(EXEC|EXECUTE)\s*\(",
                ],
                "severity": "CRITICAL",
                "score": 90
            },
            "XSS_Attack": {
                "patterns": [
                    r"((\%3C)|<)((\%2F)|\/)*[a-z0-9\%]+((>\%3E)|>)",
                    r"<script[\s\S]*?>[\s\S]*?<\/script>",
                    r"on\w+\s*=\s*[\"']?\s*\w+\(",
                    r"javascript\s*:",
                    r"data\s*:\s*text\/html",
                    r"<iframe[\s\S]*?>",
                ],
                "severity": "HIGH",
                "score": 80
            },
            "Command_Injection": {
                "patterns": [
                    r"(;|\||`|&)\s*(ls|cat|whoami|id|pwd|wget|curl|bash|nc|sh|python|perl)",
                    r"\$\(.*\)",
                    r";\s*rm\s+-rf",
                    r"\/etc\/passwd",
                    r"\/etc\/shadow",
                    r"\|\s*bash",
                ],
                "severity": "CRITICAL",
                "score": 100
            },
            "Path_Traversal": {
                "patterns": [
                    r"(\.\.\/|\.\.\\)+",
                    r"etc\/passwd",
                    r"boot\.ini",
                    r"windows\/win\.ini",
                    r"%2e%2e%2f",
                ],
                "severity": "HIGH",
                "score": 85
            },
            "SSRF_Attack": {
                "patterns": [
                    r"http[s]?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0|169\.254)",
                    r"http[s]?:\/\/10\.\d+\.\d+\.\d+",
                    r"http[s]?:\/\/192\.168\.",
                    r"file:\/\/",
                    r"gopher:\/\/",
                ],
                "severity": "HIGH",
                "score": 85
            },
            "Log4Shell": {
                "patterns": [
                    r"\$\{jndi:",
                    r"\$\{lower:",
                    r"\$\{upper:",
                    r"jndi\s*:\s*(ldap|rmi|dns)",
                ],
                "severity": "CRITICAL",
                "score": 100
            },
            "XXE_Attack": {
                "patterns": [
                    r"<!ENTITY\s+\w+\s+SYSTEM",
                    r"<!DOCTYPE\s+\w+\s+\[",
                    r"SYSTEM\s+[\"']file://",
                ],
                "severity": "HIGH",
                "score": 80
            },
            "Brute_Force_Pattern": {
                "patterns": [
                    r"(admin|root|administrator|superuser)\s*[:=]\s*\S+",
                    r"password\s*[:=]\s*(123|pass|admin|root|qwerty)",
                    r"\.\.\/\.\.\/(etc|var|usr)",
                ],
                "severity": "MEDIUM",
                "score": 55
            }
        }

        # Honeypot trap keywords
        self.honeypot_triggers = [
            "admin_bypass", "root_secret", "master_key_v2",
            "debug_override", "internal_api_v0", "superadmin"
        ]

    def analyze_request(self, data):
        risk_score = 0
        detected_threats = []

        # Honeypot check — immediate CRITICAL if triggered
        for trap in self.honeypot_triggers:
            if trap in data.lower():
                return True, f"HONEYPOT TRIGGERED: {trap}", 100, "CRITICAL"

        # Signature scan — accumulate risk score per attack type
        for attack_type, info in self.signatures.items():
            for pattern in info["patterns"]:
                if re.search(pattern, data, re.IGNORECASE):
                    risk_score += info["score"]
                    detected_threats.append(attack_type)
                    break

        if risk_score > 0:
            if risk_score >= 100:
                severity = "CRITICAL"
            elif risk_score >= 80:
                severity = "HIGH"
            elif risk_score >= 50:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            threat_label = " + ".join(detected_threats)
            return True, f"{threat_label}", min(risk_score, 100), severity

        return False, "CLEAN", 0, "INFO"
