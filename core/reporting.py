"""
Logging utilities for Glance addon.
Handles connection logging and suspicious activity reporting.
"""

import json
import hashlib
from datetime import datetime

from core.config import EXPORT_FOLDER


def log_connection(
    connection_log: list, hostname: str, is_encrypted: bool = True, has_sni: bool = True
):
    """Log all connections for comprehensive tracking."""
    timestamp = datetime.now()
    connection_log.append(
        {
            "timestamp": timestamp,
            "hostname": hostname,
            "is_encrypted": is_encrypted,
            "has_sni": has_sni,
        }
    )

    log_file = EXPORT_FOLDER / "all_connections.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(
            f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {hostname} "
            f"(encrypted={is_encrypted}, sni={has_sni})\n"
        )


def log_detailed_request(method: str, url: str, headers: dict, body: str):
    """Log detailed request information with headers and body."""
    timestamp = datetime.now()
    log_file = EXPORT_FOLDER / "all_connections.log"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] REQUEST\n")
        f.write(f"{'=' * 60}\n")
        f.write(f"Method: {method}\n")
        f.write(f"URL: {url}\n")
        f.write("\n--- Headers ---\n")
        f.write(json.dumps(headers, indent=2, ensure_ascii=False))
        f.write("\n\n--- Body ---\n")
        if body:
            if len(body) > 10000:
                f.write(f"{body[:10000]}\n... [TRUNCATED - {len(body)} total bytes]\n")
            else:
                f.write(f"{body}\n")
        else:
            f.write("(empty)\n")
        f.write(f"{'=' * 60}\n\n")


def log_bypassed_connection(hostname: str, is_trusted: bool = False):
    """Log connections that bypass MITM interception."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = EXPORT_FOLDER / "bypassed_connections.log"

    with open(log_file, "a", encoding="utf-8") as f:
        if is_trusted:
            f.write(f"[{timestamp}] TRUSTED HOST BYPASSED: {hostname}\n")
            f.write("  [✓] Known legitimate Minecraft infrastructure\n\n")
        else:
            f.write(f"[{timestamp}] BYPASSED (NO MITM): {hostname}\n")
            f.write(
                "  [!] Connection bypassed without decryption - content not verified!\n"
            )
            f.write("  [i] Enable STRICT_MODE=True to block\n\n")


def log_suspicious_activity(
    method: str, url: str, headers: dict, body: str, score: int, reasons: list[str]
):
    """Log potentially suspicious activity for review."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    content_hash = hashlib.md5((url + body).encode()).hexdigest()[:8]
    base_name = f"{timestamp}_{content_hash}_potential"

    log_file = EXPORT_FOLDER / f"{base_name}.txt"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("GLANCE - POTENTIAL THREAT DETECTED\n")
        f.write("=" * 50 + "\n")
        f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Heuristic Score: {score}\n")
        f.write(f"Method: {method}\n")
        f.write(f"URL: {url}\n\n")

        f.write("Detection Reasons:\n")
        for reason in reasons:
            f.write(f"  - {reason}\n")
        f.write("\n")

        f.write("Headers:\n")
        f.write(json.dumps(headers, indent=2, ensure_ascii=False))
        f.write("\n\nRequest Body (first 1000 chars):\n")
        f.write(body[:1000] if body else "(empty)")


def save_blocked_report(
    method: str,
    url: str,
    headers: dict,
    body: str,
    found_tokens: dict,
    heuristic_reasons: list[str] | None = None,
) -> tuple[str, str]:
    """Save human-readable and machine-readable reports for blocked requests.

    Returns:
        Tuple of (txt_filename, json_filename)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    content_hash = hashlib.md5((url + body).encode()).hexdigest()[:8]
    base_name = f"{timestamp}_{content_hash}"

    txt_file = EXPORT_FOLDER / f"{base_name}_BLOCKED.txt"
    _write_txt_report(
        txt_file, method, url, headers, body, found_tokens, heuristic_reasons
    )

    json_file = EXPORT_FOLDER / f"{base_name}_intercept.json"
    _write_json_report(json_file, method, url, headers, body, found_tokens)

    return txt_file.name, json_file.name


def _write_txt_report(
    filepath,
    method: str,
    url: str,
    headers: dict,
    body: str,
    found_tokens: dict,
    heuristic_reasons: list[str] | None,
):
    """Write human-readable blocked request report."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("GLANCE - MALICIOUS REQUEST BLOCKED\n")
        f.write("=" * 50 + "\n")
        f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Method: {method}\n")
        f.write(f"URL: {url}\n")
        f.write(f"User-Agent: {headers.get('User-Agent', 'N/A')}\n\n")

        if found_tokens:
            f.write("[!!!] TOKENS/KEYS DETECTED:\n")
            for token_type, tokens in found_tokens.items():
                f.write(f"  - {token_type.upper()} ({len(tokens)}): \n")
                for token in tokens:
                    f.write(f"    > {token}\n")
            f.write("\n")

        if heuristic_reasons:
            f.write("[!] HEURISTIC DETECTION REASONS:\n")
            for reason in heuristic_reasons:
                f.write(f"  - {reason}\n")
            f.write("\n")

        f.write("Headers:\n")
        f.write(json.dumps(headers, indent=2, ensure_ascii=False))
        f.write("\n\nRequest Body:\n")
        f.write(body if body else "(empty)")


def _write_json_report(
    filepath, method: str, url: str, headers: dict, body: str, found_tokens: dict
):
    """Write machine-readable JSON report."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "url": url,
                "headers": headers,
                "body": body,
                "extracted_tokens": found_tokens,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
