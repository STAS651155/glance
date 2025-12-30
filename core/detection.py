"""
Detection utilities for Glance addon.
Handles heuristic analysis and pattern matching for suspicious requests.
"""

import re
from urllib.parse import urlparse

from core.config import (
    PATTERNS,
    SUSPICIOUS_URLS,
    SUSPICIOUS_PORT_RANGES,
    SUSPICIOUS_INDICATORS,
    SUSPICIOUS_HEADERS,
    MAX_POST_BODY_SIZE,
)


def is_suspicious_request(url: str, body: str) -> bool:
    """Check if a request is suspicious based on URL or content patterns."""
    for pattern in SUSPICIOUS_URLS:
        if pattern in url.lower():
            return True

    for pattern in PATTERNS.values():
        if re.search(pattern, body):
            return True

    return False


def check_heuristics(
    url: str,
    method: str,
    headers: dict,
    body: str,
    unknown_hosts: set,
) -> tuple[int, list[str]]:
    """Check for heuristic indicators of unknown C2 servers.

    Returns:
        Tuple of (score, reasons) where score is the suspicion level
        and reasons is a list of detection reasons.
    """
    score = 0
    reasons = []

    parsed = urlparse(url)
    host = parsed.netloc or parsed.hostname or "unknown"

    if host in unknown_hosts:
        if method in ["POST", "PUT"] and body:
            score += 2
            reasons.append(f"Unknown host receiving data: {host} ({method})")
        elif method in ["POST", "PUT"]:
            score += 1
            reasons.append(f"Unknown host with {method} request: {host}")

    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", host):
        score += 2
        reasons.append(f"Direct IP connection: {host}")

    if parsed.port and parsed.port in SUSPICIOUS_PORT_RANGES:
        score += 1
        reasons.append(f"Suspicious port: {parsed.port}")

    if method in ["POST", "PUT"] and body:
        body_size = len(body.encode("utf-8"))
        if body_size > MAX_POST_BODY_SIZE:
            score += 3
            reasons.append(
                f"Large data upload: {body_size} bytes (threshold: {MAX_POST_BODY_SIZE})"
            )

    score, reasons = _check_url_indicators(url, score, reasons)
    score, reasons = _check_suspicious_headers(headers, score, reasons)
    score, reasons = _check_base64_obfuscation(body, score, reasons)
    score, reasons = _check_user_agent(headers, host, unknown_hosts, score, reasons)
    score, reasons = _check_credential_fields(body, method, score, reasons)

    return score, reasons


def _check_url_indicators(url: str, score: int, reasons: list) -> tuple[int, list]:
    """Check for suspicious URL path indicators."""
    for indicator in SUSPICIOUS_INDICATORS:
        if indicator in url.lower():
            score += 1
            reasons.append(f"Suspicious URL pattern: {indicator}")
            break
    return score, reasons


def _check_suspicious_headers(
    headers: dict, score: int, reasons: list
) -> tuple[int, list]:
    """Check for suspicious HTTP headers."""
    for header_name in headers:
        if header_name.lower() in SUSPICIOUS_HEADERS:
            score += 2
            reasons.append(f"Suspicious header: {header_name}")
    return score, reasons


def _check_base64_obfuscation(body: str, score: int, reasons: list) -> tuple[int, list]:
    """Check for high ratio of base64 characters indicating obfuscation."""
    if body and len(body) > 100:
        base64_chars = sum(
            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
            for c in body
        )
        if base64_chars / len(body) > 0.8:
            score += 2
            reasons.append("High base64 content ratio (potential obfuscation)")
    return score, reasons


def _check_user_agent(
    headers: dict, host: str, unknown_hosts: set, score: int, reasons: list
) -> tuple[int, list]:
    """Check for unknown hosts with unusual user agents."""
    user_agent = headers.get("User-Agent", "").lower()
    if host in unknown_hosts:
        if not user_agent or "minecraft" not in user_agent:
            score += 1
            reasons.append(f"Unknown host with unusual User-Agent: {user_agent[:50]}")
    return score, reasons


def _check_credential_fields(
    body: str, method: str, score: int, reasons: list
) -> tuple[int, list]:
    """Check for credential-like fields in request body."""
    if body and method in ["POST", "PUT"]:
        credential_keywords = [
            "password",
            "token",
            "session",
            "cookie",
            "auth",
            "key",
            "secret",
        ]
        for keyword in credential_keywords:
            if keyword in body.lower():
                score += 2
                reasons.append(
                    f"Potential credential exfiltration: contains '{keyword}'"
                )
                break
    return score, reasons


def extract_tokens(text: str) -> dict:
    """Extract tokens and API keys from text."""
    found = {}
    for name, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            cleaned = [m[1] if isinstance(m, tuple) else m for m in matches]
            found[name] = list(set(cleaned))
    return found
