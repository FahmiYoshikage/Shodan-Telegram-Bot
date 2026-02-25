"""
Beautiful output formatter for Telegram messages.
Formats Shodan results into clean, readable Telegram messages
using HTML parse mode for rich formatting.
"""

from config import EMOJI, MAX_RESULTS_PER_PAGE
from datetime import datetime


def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def header_box(title: str, subtitle: str = "") -> str:
    """Create a beautiful header box."""
    lines = [
        f"╔{'═' * 32}╗",
        f"║  {EMOJI['rocket']} <b>{escape_html(title)}</b>",
    ]
    if subtitle:
        lines.append(f"║  <i>{escape_html(subtitle)}</i>")
    lines.append(f"╚{'═' * 32}╝")
    return "\n".join(lines)


def section_header(title: str, emoji_key: str = "info") -> str:
    """Create a section header."""
    e = EMOJI.get(emoji_key, EMOJI["info"])
    return f"\n{e} <b>{escape_html(title)}</b>\n{'─' * 28}"


def key_value(key: str, value, emoji_key: str = "") -> str:
    """Format a key-value pair."""
    e = f"{EMOJI.get(emoji_key, '')} " if emoji_key else "  ◽ "
    v = escape_html(str(value)) if value else "<i>N/A</i>"
    return f"{e}<b>{escape_html(key)}:</b> {v}"


def mini_divider() -> str:
    return "┈" * 28


def format_number(n: int) -> str:
    """Format number with thousand separators."""
    return f"{n:,}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SEARCH RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_search_results(data: dict, page: int = 1) -> list[str]:
    """
    Format Shodan search results into Telegram messages.
    Returns a list of messages (to handle length limits).
    """
    if "error" in data:
        return [f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}"]

    messages = []
    matches = data.get("matches", [])
    total = data.get("total", 0)
    query = data.get("query", "")

    # Header message
    hdr = header_box("Hasil Pencarian Shodan", f"Query: {query}")
    hdr += f"\n\n{EMOJI['stats']} <b>Total ditemukan:</b> {format_number(total)} hasil"
    hdr += f"\n{EMOJI['info']} <b>Halaman:</b> {page} (menampilkan {len(matches)} hasil)"

    # Facets if available
    facets = data.get("facets", {})
    if facets:
        hdr += format_facets(facets)

    messages.append(hdr)

    # Individual results
    for i, match in enumerate(matches[:MAX_RESULTS_PER_PAGE], 1):
        msg = format_single_match(match, i + (page - 1) * MAX_RESULTS_PER_PAGE)
        messages.append(msg)

    if not matches:
        messages.append(f"\n{EMOJI['warning']} <i>Tidak ada hasil untuk query ini.</i>")

    return messages


def format_single_match(match: dict, index: int = 1) -> str:
    """Format a single search result match."""
    ip = match.get("ip_str", "N/A")
    port = match.get("port", "N/A")
    org = match.get("org", "N/A")
    isp = match.get("isp", "N/A")
    product = match.get("product", "")
    version = match.get("version", "")
    os_name = match.get("os", "")
    country = match.get("location", {}).get("country_name", "N/A")
    city = match.get("location", {}).get("city", "N/A")
    hostnames = match.get("hostnames", [])
    vulns = match.get("vulns", {})
    ssl_info = match.get("ssl", {})
    timestamp = match.get("timestamp", "")

    lines = [
        f"┌─── {EMOJI['host']} <b>Hasil #{index}</b> ───┐",
        "",
        key_value("IP", ip, "ip"),
        key_value("Port", port, "port"),
        key_value("Organisasi", org, "org"),
        key_value("ISP", isp, "isp"),
    ]

    if product:
        prod_str = f"{product} {version}".strip()
        lines.append(key_value("Product", prod_str, "product"))

    if os_name:
        lines.append(key_value("OS", os_name, "os"))

    lines.append(key_value("Negara", country, "country"))
    lines.append(key_value("Kota", city, "city"))

    if hostnames:
        lines.append(key_value("Hostname", ", ".join(hostnames[:3]), "dns"))

    # SSL Info
    if ssl_info:
        cert = ssl_info.get("cert", {})
        if cert:
            subject = cert.get("subject", {})
            cn = subject.get("CN", "")
            if cn:
                lines.append(key_value("SSL CN", cn, "ssl"))
            expires = cert.get("expires", "")
            if expires:
                lines.append(key_value("SSL Expires", expires, "time"))

    # Vulnerabilities
    if vulns:
        vuln_list = list(vulns.keys())[:5]
        lines.append(f"\n  {EMOJI['vuln']} <b>Vulnerabilities ({len(vulns)}):</b>")
        for v in vuln_list:
            lines.append(f"    {EMOJI['fire']} <code>{escape_html(v)}</code>")
        if len(vulns) > 5:
            lines.append(f"    <i>... dan {len(vulns) - 5} lainnya</i>")

    # Banner snippet
    banner = match.get("data", "")
    if banner:
        snippet = banner[:200].strip()
        lines.append(f"\n  {EMOJI['folder']} <b>Banner:</b>")
        lines.append(f"  <code>{escape_html(snippet)}</code>")

    if timestamp:
        lines.append(f"\n  {EMOJI['time']} <i>Last seen: {escape_html(timestamp[:19])}</i>")

    lines.append(f"\n└{'─' * 28}┘")

    return "\n".join(lines)


def format_facets(facets: dict) -> str:
    """Format facet data into a readable summary."""
    lines = [f"\n\n{'─' * 28}", f"{EMOJI['chart']} <b>Statistik Breakdown:</b>"]

    facet_labels = {
        "org": ("🏢", "Top Organisasi"),
        "port": ("🔌", "Top Port"),
        "product": ("📦", "Top Product"),
        "os": ("💻", "Top OS"),
        "country": ("🌍", "Top Negara"),
        "city": ("🏙️", "Top Kota"),
        "isp": ("📶", "Top ISP"),
        "domain": ("🌐", "Top Domain"),
        "asn": ("🔢", "Top ASN"),
        "vuln": ("🛡️", "Top CVE"),
    }

    for facet_name, values in facets.items():
        label_emoji, label_text = facet_labels.get(facet_name, ("📊", facet_name.title()))
        lines.append(f"\n{label_emoji} <b>{label_text}:</b>")
        for item in values[:8]:
            val = item.get("value", "N/A")
            count = item.get("count", 0)
            bar = progress_bar(count, values[0]["count"] if values else 1, width=10)
            lines.append(f"  {bar} <code>{escape_html(str(val))}</code> ({format_number(count)})")

    return "\n".join(lines)


def progress_bar(value: int, max_value: int, width: int = 10) -> str:
    """Create a text-based progress bar."""
    if max_value == 0:
        ratio = 0
    else:
        ratio = value / max_value
    filled = int(width * ratio)
    return "█" * filled + "░" * (width - filled)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HOST INFO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_host_info(data: dict) -> list[str]:
    """Format host lookup results."""
    if "error" in data:
        return [f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}"]

    ip = data.get("ip_str", "N/A")
    org = data.get("org", "N/A")
    isp = data.get("isp", "N/A")
    os_name = data.get("os", "N/A")
    country = data.get("country_name", "N/A")
    city = data.get("city", "N/A")
    hostnames = data.get("hostnames", [])
    ports = data.get("ports", [])
    vulns = data.get("vulns", [])
    last_update = data.get("last_update", "")
    asn = data.get("asn", "N/A")
    services = data.get("data", [])

    messages = []

    # Main info
    lines = [
        header_box(f"Host: {ip}", f"Informasi lengkap untuk {ip}"),
        "",
        section_header("Informasi Umum", "host"),
        key_value("IP Address", ip, "ip"),
        key_value("Organisasi", org, "org"),
        key_value("ISP", isp, "isp"),
        key_value("ASN", asn, "globe"),
        key_value("OS", os_name, "os"),
        key_value("Negara", country, "country"),
        key_value("Kota", city, "city"),
    ]

    if hostnames:
        lines.append(key_value("Hostnames", ", ".join(hostnames[:5]), "dns"))

    if last_update:
        lines.append(key_value("Last Update", last_update[:19], "time"))

    # Ports
    if ports:
        lines.append(section_header(f"Open Ports ({len(ports)})", "port"))
        port_str = ", ".join(str(p) for p in sorted(ports)[:30])
        lines.append(f"  <code>{escape_html(port_str)}</code>")

    # Vulnerabilities
    if vulns:
        lines.append(section_header(f"Vulnerabilities ({len(vulns)})", "vuln"))
        for v in vulns[:10]:
            lines.append(f"  {EMOJI['fire']} <code>{escape_html(v)}</code>")
        if len(vulns) > 10:
            lines.append(f"  <i>... dan {len(vulns) - 10} lainnya</i>")

    messages.append("\n".join(lines))

    # Services detail (separate messages)
    for svc in services[:8]:
        msg = format_service_detail(svc, ip)
        messages.append(msg)

    return messages


def format_service_detail(svc: dict, ip: str) -> str:
    """Format a single service/port detail."""
    port = svc.get("port", "?")
    transport = svc.get("transport", "tcp")
    product = svc.get("product", "")
    version = svc.get("version", "")
    module = svc.get("_shodan", {}).get("module", "")
    banner = svc.get("data", "")
    ssl_info = svc.get("ssl", {})

    lines = [
        f"┌─── {EMOJI['port']} <b>Port {port}/{transport}</b> ───",
        "",
    ]

    if product:
        lines.append(key_value("Product", f"{product} {version}".strip(), "product"))
    if module:
        lines.append(key_value("Module", module, "gear"))

    # HTTP info
    http = svc.get("http", {})
    if http:
        title = http.get("title", "")
        status = http.get("status", "")
        server = http.get("server", "")
        if title:
            lines.append(key_value("Title", title[:80], "globe"))
        if status:
            lines.append(key_value("Status", status, "check"))
        if server:
            lines.append(key_value("Server", server, "host"))

    # SSL
    if ssl_info:
        cert = ssl_info.get("cert", {})
        if cert:
            cn = cert.get("subject", {}).get("CN", "")
            issuer = cert.get("issuer", {}).get("O", "")
            if cn:
                lines.append(key_value("SSL CN", cn, "ssl"))
            if issuer:
                lines.append(key_value("Issuer", issuer, "lock"))

    # Banner
    if banner:
        snippet = banner[:300].strip()
        lines.append(f"\n  {EMOJI['folder']} <b>Banner:</b>")
        lines.append(f"  <code>{escape_html(snippet)}</code>")

    lines.append(f"\n└{'─' * 28}┘")
    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DNS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_dns_resolve(data: dict) -> str:
    """Format DNS resolution results."""
    if "error" in data:
        return f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}"

    lines = [header_box("DNS Resolve"), ""]
    for hostname, ip in data.items():
        if hostname == "error":
            continue
        lines.append(f"  {EMOJI['dns']} <code>{escape_html(hostname)}</code>")
        lines.append(f"    {EMOJI['arrow']} <code>{escape_html(str(ip))}</code>")
    return "\n".join(lines)


def format_dns_reverse(data: dict) -> str:
    """Format reverse DNS results."""
    if "error" in data:
        return f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}"

    lines = [header_box("Reverse DNS"), ""]
    for ip, hostnames in data.items():
        if ip == "error":
            continue
        lines.append(f"  {EMOJI['ip']} <code>{escape_html(ip)}</code>")
        if isinstance(hostnames, list):
            for h in hostnames:
                lines.append(f"    {EMOJI['arrow']} <code>{escape_html(h)}</code>")
        else:
            lines.append(f"    {EMOJI['arrow']} <code>{escape_html(str(hostnames))}</code>")
    return "\n".join(lines)


def format_domain_info(data: dict) -> str:
    """Format domain info results."""
    if "error" in data:
        return f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}"

    domain = data.get("domain", "N/A")
    subdomains = data.get("subdomains", [])
    records = data.get("data", [])

    lines = [
        header_box(f"Domain: {domain}"),
        "",
        section_header("Subdomains", "dns"),
    ]

    for sub in subdomains[:20]:
        lines.append(f"  {EMOJI['dot']} <code>{escape_html(sub)}.{escape_html(domain)}</code>")
    if len(subdomains) > 20:
        lines.append(f"  <i>... dan {len(subdomains) - 20} lainnya</i>")

    if records:
        lines.append(section_header("DNS Records", "globe"))
        for rec in records[:15]:
            rtype = rec.get("type", "?")
            value = rec.get("value", "N/A")
            subdomain = rec.get("subdomain", "")
            prefix = f"{subdomain}." if subdomain else ""
            lines.append(
                f"  <b>{escape_html(rtype)}</b> "
                f"<code>{escape_html(prefix)}{escape_html(domain)}</code> "
                f"→ <code>{escape_html(value)}</code>"
            )

    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EXPLOITS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_exploits(data: dict) -> list[str]:
    """Format exploit search results."""
    if "error" in data:
        return [f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}"]

    matches = data.get("matches", [])
    total = data.get("total", 0)
    query = data.get("query", "")

    messages = []

    hdr = header_box("Exploit Search", f"Query: {query}")
    hdr += f"\n\n{EMOJI['stats']} <b>Total:</b> {format_number(total)} exploits found"
    messages.append(hdr)

    for i, exp in enumerate(matches[:10], 1):
        desc = exp.get("description", "N/A")[:300]
        source = exp.get("source", "N/A")
        exp_id = exp.get("id", "N/A")
        cve_list = exp.get("cve", [])
        exp_type = exp.get("type", "N/A")

        lines = [
            f"┌─── {EMOJI['exploit']} <b>Exploit #{i}</b> ───",
            key_value("ID", exp_id, "key"),
            key_value("Source", source, "link"),
            key_value("Type", exp_type, "tag"),
        ]
        if cve_list:
            lines.append(key_value("CVE", ", ".join(cve_list[:5]), "vuln"))
        lines.append(f"\n  {EMOJI['info']} <b>Description:</b>")
        lines.append(f"  <i>{escape_html(desc)}</i>")
        lines.append(f"└{'─' * 28}┘")
        messages.append("\n".join(lines))

    if not matches:
        messages.append(f"{EMOJI['warning']} <i>Tidak ada exploit ditemukan.</i>")

    return messages


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACCOUNT INFO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_api_info(info: dict) -> str:
    """Format API account info."""
    lines = [
        header_box("Shodan Account Info"),
        "",
        key_value("Plan", info.get("plan", "?"), "star"),
        key_value("Query Credits", format_number(info.get("query_credits", 0)), "search"),
        key_value("Scan Credits", format_number(info.get("scan_credits", 0)), "ip"),
        key_value("Unlocked", "Ya ✅" if info.get("unlocked") else "Tidak", "lock"),
        key_value("Unlocked Left", format_number(info.get("unlocked_left", 0)), "key"),
    ]
    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCAN RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_scan_result(data: dict) -> str:
    """Format scan submission result."""
    if "error" in data:
        return f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}"

    scan_id = data.get("id", "N/A")
    count = data.get("count", 0)
    credits_left = data.get("credits_left", 0)

    lines = [
        header_box("Scan Submitted"),
        "",
        key_value("Scan ID", scan_id, "key"),
        key_value("IPs to scan", count, "ip"),
        key_value("Credits left", credits_left, "stats"),
        f"\n{EMOJI['info']} <i>Gunakan /scanstatus {scan_id} untuk cek progress</i>",
    ]
    return "\n".join(lines)


def format_scan_status(data: dict) -> str:
    """Format scan status result."""
    if "error" in data:
        return f"{EMOJI['error']} <b>Error:</b> {escape_html(data['error'])}"

    status = data.get("status", "unknown")
    scan_id = data.get("id", "N/A")

    status_emoji = {
        "DONE": EMOJI["success"],
        "SUBMITTING": "⏳",
        "QUEUE": "📋",
    }.get(status, "❓")

    lines = [
        header_box("Scan Status"),
        "",
        key_value("Scan ID", scan_id, "key"),
        f"  {status_emoji} <b>Status:</b> {escape_html(status)}",
    ]
    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HONEYPOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_honeypot_score(ip: str, score: float) -> str:
    """Format honeypot detection result."""
    if score < 0:
        return f"{EMOJI['error']} Tidak bisa mengecek honeypot score untuk <code>{escape_html(ip)}</code>"

    if score >= 0.8:
        verdict = f"{EMOJI['honeypot']} <b>Kemungkinan besar HONEYPOT</b>"
    elif score >= 0.5:
        verdict = f"{EMOJI['warning']} <b>Mungkin honeypot</b>"
    else:
        verdict = f"{EMOJI['success']} <b>Kemungkinan bukan honeypot</b>"

    bar = progress_bar(int(score * 10), 10, width=10)
    lines = [
        header_box("Honeypot Detection", f"IP: {ip}"),
        "",
        key_value("IP", ip, "ip"),
        f"  {EMOJI['honeypot']} <b>Score:</b> {score:.2f} / 1.00",
        f"  {bar}",
        f"\n  {verdict}",
    ]
    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HELP / WELCOME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_welcome() -> str:
    """Format welcome/help message."""
    return f"""
╔{'═' * 34}╗
║  {EMOJI['rocket']} <b>Shodan Telegram Bot</b>
║  <i>Powered by Shodan Academic Plus</i>
╚{'═' * 34}╝

{EMOJI['wave']} <b>Selamat datang!</b>
Bot ini mempermudah penggunaan Shodan
langsung dari Telegram dengan template
pencarian yang siap pakai.

{'─' * 30}
{EMOJI['search']} <b>PERINTAH UTAMA:</b>

  /search <code>[query]</code>
  Pencarian langsung dengan query Shodan

  /templates atau /t
  Lihat semua template pencarian siap pakai

  /host <code>[IP]</code>
  Lookup detail lengkap sebuah IP

  /count <code>[query]</code>
  Hitung hasil tanpa pakai credits

{'─' * 30}
{EMOJI['dns']} <b>DNS & DOMAIN:</b>

  /dns <code>[hostname]</code>
  Resolve hostname ke IP

  /rdns <code>[IP]</code>
  Reverse DNS lookup

  /domain <code>[domain]</code>
  Info DNS records sebuah domain

{'─' * 30}
{EMOJI['exploit']} <b>EXPLOIT & VULN:</b>

  /exploit <code>[query]</code>
  Cari exploit berdasarkan keyword

  /honeypot <code>[IP]</code>
  Cek apakah IP itu honeypot

{'─' * 30}
{EMOJI['ip']} <b>SCANNING:</b>

  /scan <code>[IP/CIDR]</code>
  Request scan Shodan untuk IP/network

  /scanstatus <code>[scan_id]</code>
  Cek status scan yang sedang berjalan

{'─' * 30}
{EMOJI['gear']} <b>LAINNYA:</b>

  /info — Cek status akun & credits
  /filters — Daftar filter Shodan
  /help — Tampilkan bantuan ini

{'─' * 30}
{EMOJI['star']} <b>TIPS:</b>
Gunakan /templates untuk pencarian
cepat dengan template siap pakai!
Tinggal pilih, isi parameter, selesai! ✨
"""


def format_filters_help() -> str:
    """Format Shodan filters reference."""
    return f"""
{EMOJI['search']} <b>SHODAN FILTER REFERENCE</b>
{'═' * 30}

{EMOJI['globe']} <b>Lokasi:</b>
  <code>country:"ID"</code> — Kode negara
  <code>city:"Jakarta"</code> — Kota
  <code>region:"West Java"</code> — Provinsi/Region

{EMOJI['org']} <b>Organisasi:</b>
  <code>org:"Telkom"</code> — Nama organisasi
  <code>isp:"Telkomsel"</code> — Nama ISP
  <code>asn:AS17974</code> — ASN number
  <code>net:202.134.0.0/16</code> — Subnet CIDR

{EMOJI['port']} <b>Service:</b>
  <code>port:22</code> — Nomor port
  <code>product:"nginx"</code> — Nama product
  <code>version:"1.19"</code> — Versi product
  <code>os:"Windows"</code> — Operating system

{EMOJI['globe']} <b>HTTP:</b>
  <code>http.title:"Login"</code> — Title halaman
  <code>http.server:"Apache"</code> — Web server
  <code>http.status:200</code> — HTTP status
  <code>http.component:"jQuery"</code> — Web tech
  <code>http.favicon.hash:NNN</code> — Favicon hash

{EMOJI['ssl']} <b>SSL/TLS:</b>
  <code>ssl.cert.subject.CN:"*.example.com"</code>
  <code>ssl.cert.subject.O:"Org Name"</code>
  <code>ssl.cert.expired:true</code>
  <code>has_ssl:true</code>

{EMOJI['vuln']} <b>Vulnerability:</b>
  <code>vuln:"CVE-2021-44228"</code> — CVE spesifik
  <code>has_vuln:true</code> — Punya vulnerability
  <code>tag:"ics"</code> — Tag ICS/SCADA

{EMOJI['dns']} <b>DNS:</b>
  <code>hostname:".go.id"</code> — Hostname
  <code>has_screenshot:true</code> — Ada screenshot

{EMOJI['info']} <b>Others:</b>
  <code>before:"01/01/2024"</code> — Sebelum tanggal
  <code>after:"01/01/2024"</code> — Setelah tanggal
  <code>"keyword"</code> — Cari di banner

{EMOJI['star']} <b>Kombinasi:</b>
  Gabungkan filter dengan spasi:
  <code>product:"nginx" country:"ID" port:443</code>
"""
