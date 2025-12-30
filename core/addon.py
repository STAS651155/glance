"""
mitmproxy addon for Glance.
Intercepts and analyzes HTTPS traffic for suspicious activity.
"""

import sys
from pathlib import Path

addon_dir = Path(__file__).parent
project_root = addon_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datetime import datetime  # noqa: E402
from collections import defaultdict  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

from mitmproxy import http, ctx  # noqa: E402
from core.config import (  # noqa: E402
    STRICT_MODE,
    IGNORE_HOSTS,
    LOG_ALL_CONNECTIONS,
    BEHAVIORAL_ANALYSIS,
    MAX_POST_BODY_SIZE,
    MAX_REQUEST_FREQUENCY,
)
from core.detection import (  # noqa: E402
    is_suspicious_request,
    check_heuristics,
    extract_tokens,
)
from core.reporting import (  # noqa: E402
    log_connection,
    log_bypassed_connection,
    log_suspicious_activity,
    save_blocked_report,
)


class GlanceAddon:
    """mitmproxy addon that intercepts suspicious requests."""

    def __init__(self):
        self.connection_log = []  # Track ALL connections
        self.request_frequency = defaultdict(list)  # Track request patterns
        self.unknown_hosts = set()  # Track unknown hosts contacted
        self.data_volumes = defaultdict(int)  # Track data exfiltration amounts

    def tls_clienthello(self, data):
        """Handle TLS client hello to bypass or block certain hosts."""
        client_hello = data.context.client.sni
        client_address = (
            data.context.client.peername[0]
            if data.context.client.peername
            else "unknown"
        )

        if not client_hello:
            ctx.log.warn(f"[!] IP-BASED CONNECTION (no SNI) from {client_address}")
            if LOG_ALL_CONNECTIONS:
                log_connection(
                    self.connection_log,
                    f"IP:{client_address}",
                    is_encrypted=False,
                    has_sni=False,
                )
            return

        if LOG_ALL_CONNECTIONS:
            log_connection(
                self.connection_log, client_hello, is_encrypted=True, has_sni=True
            )

        if client_hello:
            if STRICT_MODE:
                is_known_safe = any(
                    ignore_host in client_hello for ignore_host in IGNORE_HOSTS
                )
                if not is_known_safe:
                    ctx.log.warn(
                        f"[!] STRICT MODE: blocking {client_hello} (no trusted certificate)"
                    )
                    return

            for ignore_host in IGNORE_HOSTS:
                if ignore_host in client_hello:
                    ctx.log.info(f"[✓] ALLOWED (trusted): {client_hello}")
                    log_bypassed_connection(client_hello, is_trusted=True)
                    data.ignore_connection = True
                    return

            if BEHAVIORAL_ANALYSIS:
                self.unknown_hosts.add(client_hello)
                ctx.log.warn(f"[?] UNKNOWN HOST: {client_hello}")

    def request(self, flow: http.HTTPFlow) -> None:
        """Intercept and analyze HTTP requests."""
        request = flow.request
        url = request.pretty_url
        method = request.method
        headers = dict(request.headers)
        body = request.text or ""

        if LOG_ALL_CONNECTIONS:
            self._log_detailed_connection(method, url, headers, body)

        if BEHAVIORAL_ANALYSIS:
            self._track_request(url, method, body)

        is_known_suspicious = is_suspicious_request(url, body)
        heuristic_score, heuristic_reasons = check_heuristics(
            url, method, headers, body, self.unknown_hosts
        )

        behavioral_flags = self._check_behavioral_anomalies(url)

        if is_known_suspicious or (heuristic_score >= 2):
            reason = (
                "KNOWN MALWARE"
                if is_known_suspicious
                else f"HEURISTIC DETECTION (score={heuristic_score})"
            )
            ctx.log.error(f"[!!!] SUSPICIOUS REQUEST [{reason}]: {method} {url}")
            if heuristic_reasons:
                for r in heuristic_reasons:
                    ctx.log.warn(f"      - {r}")
            self._handle_suspicious(flow, method, url, headers, body, heuristic_reasons)
        elif heuristic_score > 0 or behavioral_flags:
            ctx.log.warn(
                f"[?] POTENTIALLY SUSPICIOUS: {method} {url} (score={heuristic_score})"
            )
            if heuristic_reasons:
                for r in heuristic_reasons:
                    ctx.log.info(f"    - {r}")
            log_suspicious_activity(
                method, url, headers, body, heuristic_score, heuristic_reasons
            )

    def _log_detailed_connection(self, method: str, url: str, headers: dict, body: str):
        """Log detailed connection information with headers and body."""
        from core.reporting import log_detailed_request

        log_detailed_request(method, url, headers, body)

    def _track_request(self, url: str, method: str, body: str):
        """Track request for behavioral analysis."""
        parsed = urlparse(url)
        host = parsed.netloc or parsed.hostname or "unknown"
        current_time = datetime.now()
        self.request_frequency[host].append(current_time)

        if method in ["POST", "PUT"]:
            self.data_volumes[host] += len(body.encode("utf-8")) if body else 0

    def _check_behavioral_anomalies(self, url: str) -> list[str]:
        """Check for behavioral anomalies indicating C2 communication."""
        flags = []
        parsed = urlparse(url)
        host = parsed.netloc or parsed.hostname or "unknown"

        if not BEHAVIORAL_ANALYSIS:
            return flags

        current_time = datetime.now()
        recent_requests = [
            t
            for t in self.request_frequency[host]
            if (current_time - t).total_seconds() < 60
        ]

        if len(recent_requests) > MAX_REQUEST_FREQUENCY:
            flags.append(
                f"High request frequency to {host}: {len(recent_requests)}/min"
            )

        if self.data_volumes[host] > MAX_POST_BODY_SIZE * 5:
            flags.append(
                f"Large data volume to {host}: {self.data_volumes[host]} bytes"
            )

        return flags

    def _handle_suspicious(
        self,
        flow: http.HTTPFlow,
        method: str,
        url: str,
        headers: dict,
        body: str,
        heuristic_reasons: list[str] | None = None,
    ):
        """Handle a suspicious request by logging and blocking it."""
        full_text = f"{url}\n{body}"
        found_tokens = extract_tokens(full_text)

        txt_name, json_name = save_blocked_report(
            method, url, headers, body, found_tokens, heuristic_reasons
        )
        ctx.log.info(f"[i] Report saved: {txt_name} + {json_name}")

        flow.response = http.Response.make(
            200,
            b'{"success": true, "message": "Request processed successfully"}',
            {"Content-Type": "application/json"},
        )
        ctx.log.error("[✓] MALICIOUS REQUEST BLOCKED - Your data is safe!")


addons = [GlanceAddon()]
