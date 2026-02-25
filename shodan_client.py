"""
Shodan API wrapper — abstraction layer for all Shodan queries.
Handles search, host lookup, DNS, exploits, stats, and more.
"""

import shodan
import logging
from typing import Optional
from config import SHODAN_API_KEY

logger = logging.getLogger(__name__)


class ShodanClient:
    """Wraps the Shodan API with convenience methods."""

    def __init__(self):
        self.api = shodan.Shodan(SHODAN_API_KEY)
        self._info_cache: Optional[dict] = None

    # ─── Account ────────────────────────────────────────────

    def account_info(self) -> dict:
        """Get account profile + remaining credits."""
        if not self._info_cache:
            self._info_cache = self.api.info()
        return self._info_cache

    def api_info(self) -> dict:
        """Return scan/query credits left."""
        info = self.account_info()
        return {
            "scan_credits": info.get("scan_credits", 0),
            "query_credits": info.get("query_credits", 0),
            "plan": info.get("plan", "unknown"),
            "unlocked": info.get("unlocked", False),
            "unlocked_left": info.get("unlocked_left", 0),
        }

    # ─── Search ─────────────────────────────────────────────

    def search(self, query: str, page: int = 1, limit: int = 100, facets: str = "") -> dict:
        """
        Run a Shodan search query.
        Returns dict with 'matches' and 'total'.
        """
        try:
            facet_list = None
            if facets:
                facet_list = [
                    tuple(f.strip().split(":")) if ":" in f else (f.strip(), 10)
                    for f in facets.split(",")
                ]

            results = self.api.search(query, page=page, limit=limit, facets=facet_list)
            return {
                "matches": results.get("matches", []),
                "total": results.get("total", 0),
                "facets": results.get("facets", {}),
                "query": query,
                "page": page,
            }
        except shodan.APIError as e:
            logger.error(f"Shodan search error: {e}")
            return {"error": str(e), "query": query}

    def search_count(self, query: str, facets: str = "") -> dict:
        """Count results without using query credits (uses /shodan/host/count)."""
        try:
            facet_list = None
            if facets:
                facet_list = [
                    tuple(f.strip().split(":")) if ":" in f else (f.strip(), 10)
                    for f in facets.split(",")
                ]
            results = self.api.count(query, facets=facet_list)
            return {
                "total": results.get("total", 0),
                "facets": results.get("facets", {}),
                "query": query,
            }
        except shodan.APIError as e:
            logger.error(f"Shodan count error: {e}")
            return {"error": str(e), "query": query}

    # ─── Host ───────────────────────────────────────────────

    def host_info(self, ip: str, history: bool = False, minify: bool = False) -> dict:
        """Lookup a specific IP address."""
        try:
            return self.api.host(ip, history=history, minify=minify)
        except shodan.APIError as e:
            logger.error(f"Shodan host error: {e}")
            return {"error": str(e), "ip": ip}

    # ─── DNS ────────────────────────────────────────────────

    def dns_resolve(self, hostnames: list[str]) -> dict:
        """Resolve hostnames to IPs."""
        try:
            return self.api.dns.resolve(hostnames)
        except shodan.APIError as e:
            logger.error(f"Shodan DNS resolve error: {e}")
            return {"error": str(e)}

    def dns_reverse(self, ips: list[str]) -> dict:
        """Reverse DNS lookup."""
        try:
            return self.api.dns.reverse(ips)
        except shodan.APIError as e:
            logger.error(f"Shodan DNS reverse error: {e}")
            return {"error": str(e)}

    def dns_domain(self, domain: str) -> dict:
        """Get DNS records for a domain."""
        try:
            return self.api.dns.domain_info(domain)
        except Exception:
            # Fallback: some versions use different method names
            try:
                return self.api.get_domain(domain)
            except shodan.APIError as e:
                logger.error(f"Shodan domain error: {e}")
                return {"error": str(e)}

    # ─── Exploits ───────────────────────────────────────────

    def search_exploits(self, query: str, page: int = 1) -> dict:
        """Search for exploits."""
        try:
            results = self.api.exploits.search(query, page=page)
            return {
                "matches": results.get("matches", []),
                "total": results.get("total", 0),
                "query": query,
            }
        except shodan.APIError as e:
            logger.error(f"Shodan exploit search error: {e}")
            return {"error": str(e), "query": query}

    # ─── Scanning ───────────────────────────────────────────

    def scan_ip(self, ips: str) -> dict:
        """Request Shodan to scan an IP/network."""
        try:
            return self.api.scan(ips)
        except shodan.APIError as e:
            logger.error(f"Shodan scan error: {e}")
            return {"error": str(e)}

    def scan_status(self, scan_id: str) -> dict:
        """Check the status of a scan."""
        try:
            return self.api.scan_status(scan_id)
        except shodan.APIError as e:
            logger.error(f"Shodan scan status error: {e}")
            return {"error": str(e)}

    # ─── Protocols & Services ───────────────────────────────

    def protocols(self) -> dict:
        """List protocols Shodan can scan for."""
        try:
            return self.api.protocols()
        except shodan.APIError as e:
            logger.error(f"Shodan protocols error: {e}")
            return {"error": str(e)}

    def services(self) -> dict:
        """List common services/ports."""
        try:
            return self.api.services()
        except shodan.APIError as e:
            logger.error(f"Shodan services error: {e}")
            return {"error": str(e)}

    # ─── Honeypot detection ─────────────────────────────────

    def honeypot_score(self, ip: str) -> float:
        """Get honeypot score for an IP (0 = not honeypot, 1 = honeypot)."""
        try:
            return self.api.labs.honeyscore(ip)
        except shodan.APIError as e:
            logger.error(f"Shodan honeypot error: {e}")
            return -1.0


# Singleton instance
shodan_client = ShodanClient()
