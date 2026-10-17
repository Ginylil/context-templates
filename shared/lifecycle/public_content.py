"""Shared redacted credential signatures; no Git, network or filesystem access."""
import re
from pathlib import Path

SIGNATURES = {
    'private-key': rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----',
    'aws-key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'github-token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'openai-token': rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}\b',
    'google-key': rb'\bAIza[A-Za-z0-9_-]{35}\b',
    'google-oauth-token': rb'\bya29\.[A-Za-z0-9_-]{20,}\b',
    'slack-token': rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
    'stripe-key': rb'\b(?:sk|rk)_live_[A-Za-z0-9]{20,}\b',
    'jwt': rb'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b',
    'credential-assignment': rb'''(?i)["']?(?:api[_-]?key|access[_-]?token|client[_-]?secret|secret[_-]?key|password|passwd|token)["']?\s*[:=]\s*["']([A-Za-z0-9_+./=-]{20,})["']''',
}
PATTERNS = {name: re.compile(pattern) for name, pattern in SIGNATURES.items()}
PRIVATE_SUFFIXES = {'.p8', '.p12', '.pfx', '.pem', '.key', '.jks', '.keystore', '.mobileprovision'}


def findings(data, name):
    result = []
    path = Path(name)
    if path.suffix.lower() in PRIVATE_SUFFIXES or (path.name.startswith('.env') and path.name not in ('.env.example', '.env.template')):
        result.append({'path': name, 'line': 0, 'rule': 'credential-file'})
    for rule, pattern in PATTERNS.items():
        for match in pattern.finditer(data):
            if rule == 'credential-assignment':
                value = match.group(1)
                if len(set(value)) < 8:
                    continue
            # Never return matched bytes or raw source lines, including fixtures.
            result.append({'path': name, 'line': data[:match.start()].count(b'\n') + 1, 'rule': rule})
    return result
