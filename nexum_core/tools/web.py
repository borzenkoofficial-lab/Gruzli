from __future__ import annotations
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

@dataclass
class WebResult:
    ok: bool
    url: str
    status: int | None
    content_type: str | None
    text: str = ""
    error: str | None = None

class NetworkPolicy:
    def __init__(self, mode: str = "research", max_bytes: int = 2_000_000, timeout: float = 15.0):
        self.mode = mode
        self.max_bytes = max_bytes
        self.timeout = timeout

    def check(self, url: str) -> None:
        if self.mode == "off":
            raise PermissionError("network access is disabled")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise PermissionError("only http/https URLs are allowed")
        host = parsed.hostname
        if host in {"localhost"}:
            raise PermissionError("local hosts are blocked")
        try:
            infos = socket.getaddrinfo(host, None)
        except OSError as exc:
            raise ConnectionError(f"DNS resolution failed: {host}") from exc
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                raise PermissionError(f"private/reserved network target blocked: {ip}")

class WebFetchTool:
    name = "web_fetch"
    description = "Fetch a public HTTP(S) webpage through Nexum's controlled network gateway."
    parameters = {
        "type":"object",
        "properties":{
            "url":{"type":"string"},
            "max_bytes":{"type":"integer","minimum":1024,"maximum":5000000},
        },
        "required":["url"],
        "additionalProperties":False,
    }
    def __init__(self, policy: NetworkPolicy | None = None):
        self.policy = policy or NetworkPolicy()

    def execute(self, url: str, max_bytes: int | None = None) -> dict:
        current = url
        for _ in range(4):
            self.policy.check(current)
            req = Request(current, headers={"User-Agent":"Nexum-Core/1.0 ResearchBot"})
            with urlopen(req, timeout=self.policy.timeout) as response:
                data = response.read(min(max_bytes or self.policy.max_bytes, self.policy.max_bytes))
                final_url = response.geturl()
                if final_url != current:
                    self.policy.check(final_url)
                return {
                    "url": final_url,
                    "status": getattr(response, "status", 200),
                    "content_type": response.headers.get("content-type"),
                    "text": data.decode("utf-8", errors="replace"),
                }
        raise RuntimeError("too many redirects")

    def schema(self): return {"name":self.name,"description":self.description,"parameters":self.parameters}
