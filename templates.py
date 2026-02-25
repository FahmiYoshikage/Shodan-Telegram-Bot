"""
Search templates — pre-built Shodan queries with fill-in-the-blank parameters.
Each template has:
  - name: display name
  - description: what it searches for
  - emoji: visual icon
  - query_template: Shodan query with {placeholders}
  - params: list of parameters the user must fill
  - category: grouping for menu
  - example: example filled query
  - facets: optional default facets
"""

from dataclasses import dataclass, field


@dataclass
class SearchParam:
    name: str
    description: str
    placeholder: str  # example value
    required: bool = True


@dataclass
class SearchTemplate:
    id: str
    name: str
    description: str
    emoji: str
    query_template: str
    params: list[SearchParam]
    category: str
    example: str
    facets: str = ""
    tags: list[str] = field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEMPLATE CATEGORIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CATEGORIES = {
    "network": {"name": "🌐 Network & Infrastructure", "order": 1},
    "web": {"name": "🌍 Web Servers & Apps", "order": 2},
    "iot": {"name": "📡 IoT & Cameras", "order": 3},
    "industrial": {"name": "🏭 ICS / SCADA", "order": 4},
    "database": {"name": "🗄️ Databases", "order": 5},
    "vuln": {"name": "🛡️ Vulnerabilities", "order": 6},
    "cloud": {"name": "☁️ Cloud Services", "order": 7},
    "country": {"name": "🗺️ By Country / Region", "order": 8},
    "custom": {"name": "⚙️ Custom / Raw Query", "order": 9},
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ALL SEARCH TEMPLATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEMPLATES: list[SearchTemplate] = [

    # ─── NETWORK & INFRASTRUCTURE ───────────────────────────

    SearchTemplate(
        id="net_provider",
        name="Cari Provider / ISP",
        description="Cari semua perangkat milik ISP / provider tertentu di suatu negara",
        emoji="📶",
        query_template='org:"{org}" country:"{country}"',
        params=[
            SearchParam("org", "Nama ISP/Provider", "Telkom Indonesia"),
            SearchParam("country", "Kode negara (2 huruf)", "ID"),
        ],
        category="network",
        example='org:"Telkom Indonesia" country:"ID"',
        tags=["isp", "provider", "telkom"],
    ),
    SearchTemplate(
        id="net_port_country",
        name="Port Terbuka di Negara",
        description="Cari perangkat dengan port tertentu terbuka di suatu negara",
        emoji="🔌",
        query_template='port:{port} country:"{country}"',
        params=[
            SearchParam("port", "Nomor port", "22"),
            SearchParam("country", "Kode negara (2 huruf)", "ID"),
        ],
        category="network",
        example='port:22 country:"ID"',
        tags=["port", "ssh", "open"],
    ),
    SearchTemplate(
        id="net_service_city",
        name="Service di Kota",
        description="Cari service tertentu di kota spesifik",
        emoji="🏙️",
        query_template='product:"{product}" city:"{city}" country:"{country}"',
        params=[
            SearchParam("product", "Nama service/product", "nginx"),
            SearchParam("city", "Nama kota", "Jakarta"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="network",
        example='product:"nginx" city:"Jakarta" country:"ID"',
        tags=["service", "city"],
    ),
    SearchTemplate(
        id="net_asn",
        name="Cari by ASN",
        description="Cari perangkat berdasarkan Autonomous System Number",
        emoji="🔢",
        query_template="asn:{asn}",
        params=[
            SearchParam("asn", "ASN number (contoh: AS17974)", "AS17974"),
        ],
        category="network",
        example="asn:AS17974",
        tags=["asn", "bgp"],
    ),
    SearchTemplate(
        id="net_subnet",
        name="Scan Subnet / CIDR",
        description="Cari perangkat dalam subnet tertentu",
        emoji="🔀",
        query_template="net:{cidr}",
        params=[
            SearchParam("cidr", "Subnet CIDR", "202.134.0.0/16"),
        ],
        category="network",
        example="net:202.134.0.0/16",
        tags=["subnet", "cidr", "network"],
    ),
    SearchTemplate(
        id="net_hostname",
        name="Cari Hostname",
        description="Cari perangkat berdasarkan hostname/domain",
        emoji="🏷️",
        query_template='hostname:"{hostname}"',
        params=[
            SearchParam("hostname", "Hostname atau domain", ".go.id"),
        ],
        category="network",
        example='hostname:".go.id"',
        tags=["hostname", "domain", "dns"],
    ),
    SearchTemplate(
        id="net_os_country",
        name="Cari OS di Negara",
        description="Cari perangkat dengan OS tertentu di negara tertentu",
        emoji="💻",
        query_template='os:"{os}" country:"{country}"',
        params=[
            SearchParam("os", "Nama operating system", "Windows 10"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="network",
        example='os:"Windows 10" country:"ID"',
        tags=["os", "windows", "linux"],
    ),

    # ─── WEB SERVERS & APPS ─────────────────────────────────

    SearchTemplate(
        id="web_server",
        name="Web Server di Negara",
        description="Cari web server (Apache/Nginx/IIS) di negara tertentu",
        emoji="🌍",
        query_template='http.server:"{server}" country:"{country}"',
        params=[
            SearchParam("server", "Nama web server", "Apache"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="web",
        example='http.server:"Apache" country:"ID"',
        tags=["web", "apache", "nginx", "iis"],
    ),
    SearchTemplate(
        id="web_title",
        name="Cari Web by Title",
        description="Cari website berdasarkan judul halaman",
        emoji="📄",
        query_template='http.title:"{title}"',
        params=[
            SearchParam("title", "Judul halaman web", "Dashboard"),
        ],
        category="web",
        example='http.title:"Dashboard"',
        tags=["title", "web", "html"],
    ),
    SearchTemplate(
        id="web_component",
        name="Cari Web Component",
        description="Cari website yang menggunakan teknologi tertentu",
        emoji="⚙️",
        query_template='http.component:"{component}" country:"{country}"',
        params=[
            SearchParam("component", "Nama teknologi (WordPress, jQuery, dll)", "WordPress"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="web",
        example='http.component:"WordPress" country:"ID"',
        tags=["wordpress", "component", "technology"],
    ),
    SearchTemplate(
        id="web_favicon",
        name="Cari by Favicon Hash",
        description="Cari website berdasarkan favicon hash (untuk identifikasi app)",
        emoji="🖼️",
        query_template="http.favicon.hash:{hash}",
        params=[
            SearchParam("hash", "Favicon hash number", "116323821"),
        ],
        category="web",
        example="http.favicon.hash:116323821",
        tags=["favicon", "hash", "fingerprint"],
    ),
    SearchTemplate(
        id="web_ssl_org",
        name="SSL Certificate by Org",
        description="Cari berdasarkan organisasi di SSL certificate",
        emoji="🔒",
        query_template='ssl.cert.subject.O:"{org}"',
        params=[
            SearchParam("org", "Nama organisasi di SSL cert", "Government of Indonesia"),
        ],
        category="web",
        example='ssl.cert.subject.O:"Government of Indonesia"',
        tags=["ssl", "certificate", "tls"],
    ),
    SearchTemplate(
        id="web_ssl_expired",
        name="SSL Expired di Negara",
        description="Cari website dengan SSL certificate yang sudah expired",
        emoji="🔓",
        query_template='ssl.cert.expired:true country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="web",
        example='ssl.cert.expired:true country:"ID"',
        tags=["ssl", "expired", "security"],
    ),
    SearchTemplate(
        id="web_http_status",
        name="HTTP Status Code",
        description="Cari web berdasarkan HTTP status code",
        emoji="📊",
        query_template='http.status:{status} country:"{country}"',
        params=[
            SearchParam("status", "HTTP status code", "200"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="web",
        example='http.status:200 country:"ID"',
        tags=["http", "status"],
    ),

    # ─── IoT & CAMERAS ─────────────────────────────────────

    SearchTemplate(
        id="iot_webcam",
        name="Webcam / IP Camera",
        description="Cari IP camera / webcam yang terekspos",
        emoji="📷",
        query_template='product:"{brand}" country:"{country}"',
        params=[
            SearchParam("brand", "Merk kamera (Hikvision, Dahua, dll)", "Hikvision"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="iot",
        example='product:"Hikvision" country:"ID"',
        tags=["camera", "webcam", "cctv", "hikvision"],
    ),
    SearchTemplate(
        id="iot_router",
        name="Router Admin Panel",
        description="Cari router admin panel yang terekspos",
        emoji="📡",
        query_template='http.title:"{router_type}" country:"{country}"',
        params=[
            SearchParam("router_type", "Tipe router (MikroTik, TP-Link)", "MikroTik"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="iot",
        example='http.title:"MikroTik" country:"ID"',
        tags=["router", "mikrotik", "admin"],
    ),
    SearchTemplate(
        id="iot_printer",
        name="Printer Terekspos",
        description="Cari printer yang terekspos ke internet",
        emoji="🖨️",
        query_template='port:9100 country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="iot",
        example='port:9100 country:"ID"',
        tags=["printer", "iot"],
    ),
    SearchTemplate(
        id="iot_mqtt",
        name="MQTT Broker",
        description="Cari MQTT broker (IoT messaging) yang terekspos",
        emoji="📨",
        query_template='product:"MQTT" country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="iot",
        example='product:"MQTT" country:"ID"',
        tags=["mqtt", "iot", "broker"],
    ),

    # ─── ICS / SCADA ────────────────────────────────────────

    SearchTemplate(
        id="ics_scada",
        name="SCADA / ICS Devices",
        description="Cari perangkat ICS/SCADA berdasarkan tag",
        emoji="🏭",
        query_template='tag:"{tag}" country:"{country}"',
        params=[
            SearchParam("tag", "Tag ICS (ics, scada)", "ics"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="industrial",
        example='tag:"ics" country:"ID"',
        tags=["scada", "ics", "industrial"],
    ),
    SearchTemplate(
        id="ics_modbus",
        name="Modbus Devices",
        description="Cari perangkat Modbus (ICS protocol)",
        emoji="⚡",
        query_template='port:502 country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="industrial",
        example='port:502 country:"ID"',
        tags=["modbus", "ics"],
    ),
    SearchTemplate(
        id="ics_plc",
        name="PLC Devices",
        description="Cari Programmable Logic Controller",
        emoji="🔧",
        query_template='product:"{plc_brand}" country:"{country}"',
        params=[
            SearchParam("plc_brand", "Merk PLC (Siemens, Allen-Bradley)", "Siemens"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="industrial",
        example='product:"Siemens" country:"ID"',
        tags=["plc", "siemens"],
    ),

    # ─── DATABASES ──────────────────────────────────────────

    SearchTemplate(
        id="db_mongodb",
        name="MongoDB Terekspos",
        description="Cari MongoDB database yang terekspos",
        emoji="🍃",
        query_template='product:"MongoDB" country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="database",
        example='product:"MongoDB" country:"ID"',
        tags=["mongodb", "nosql", "database"],
    ),
    SearchTemplate(
        id="db_elastic",
        name="Elasticsearch Terekspos",
        description="Cari Elasticsearch cluster yang terekspos",
        emoji="🔎",
        query_template='product:"Elastic" country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="database",
        example='product:"Elastic" country:"ID"',
        tags=["elasticsearch", "elastic", "database"],
    ),
    SearchTemplate(
        id="db_redis",
        name="Redis Terekspos",
        description="Cari Redis server yang terekspos",
        emoji="🔴",
        query_template='product:"Redis" country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="database",
        example='product:"Redis" country:"ID"',
        tags=["redis", "database", "cache"],
    ),
    SearchTemplate(
        id="db_mysql",
        name="MySQL Terekspos",
        description="Cari MySQL server yang terekspos",
        emoji="🐬",
        query_template='product:"MySQL" country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="database",
        example='product:"MySQL" country:"ID"',
        tags=["mysql", "database", "sql"],
    ),
    SearchTemplate(
        id="db_postgres",
        name="PostgreSQL Terekspos",
        description="Cari PostgreSQL server yang terekspos",
        emoji="🐘",
        query_template='product:"PostgreSQL" country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="database",
        example='product:"PostgreSQL" country:"ID"',
        tags=["postgres", "postgresql", "database"],
    ),

    # ─── VULNERABILITIES ────────────────────────────────────

    SearchTemplate(
        id="vuln_cve",
        name="Cari CVE Tertentu",
        description="Cari perangkat yang rentan terhadap CVE tertentu",
        emoji="🛡️",
        query_template='vuln:"{cve}"',
        params=[
            SearchParam("cve", "CVE ID", "CVE-2021-44228"),
        ],
        category="vuln",
        example='vuln:"CVE-2021-44228"',
        tags=["cve", "vulnerability"],
    ),
    SearchTemplate(
        id="vuln_cve_country",
        name="CVE di Negara",
        description="Cari perangkat rentan CVE tertentu di negara spesifik",
        emoji="🚨",
        query_template='vuln:"{cve}" country:"{country}"',
        params=[
            SearchParam("cve", "CVE ID", "CVE-2021-44228"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="vuln",
        example='vuln:"CVE-2021-44228" country:"ID"',
        tags=["cve", "vulnerability", "country"],
    ),
    SearchTemplate(
        id="vuln_has_vuln",
        name="Perangkat dgn Vulnerability",
        description="Cari semua perangkat yang punya vulnerability di negara tertentu",
        emoji="💥",
        query_template='has_vuln:true country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="vuln",
        example='has_vuln:true country:"ID"',
        tags=["vulnerability", "vuln"],
    ),
    SearchTemplate(
        id="vuln_default_pass",
        name="Default Password",
        description="Cari perangkat dengan password default",
        emoji="🔑",
        query_template='"default password" country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="vuln",
        example='"default password" country:"ID"',
        tags=["password", "default", "credential"],
    ),

    # ─── CLOUD ──────────────────────────────────────────────

    SearchTemplate(
        id="cloud_aws",
        name="AWS Services",
        description="Cari services yang berjalan di AWS",
        emoji="☁️",
        query_template='org:"Amazon" product:"{product}"',
        params=[
            SearchParam("product", "Nama product/service", "nginx"),
        ],
        category="cloud",
        example='org:"Amazon" product:"nginx"',
        tags=["aws", "amazon", "cloud"],
    ),
    SearchTemplate(
        id="cloud_gcp",
        name="Google Cloud Services",
        description="Cari services yang berjalan di Google Cloud",
        emoji="🌈",
        query_template='org:"Google Cloud" product:"{product}"',
        params=[
            SearchParam("product", "Nama product/service", "nginx"),
        ],
        category="cloud",
        example='org:"Google Cloud" product:"nginx"',
        tags=["gcp", "google", "cloud"],
    ),
    SearchTemplate(
        id="cloud_azure",
        name="Azure Services",
        description="Cari services yang berjalan di Microsoft Azure",
        emoji="🔷",
        query_template='org:"Microsoft Azure" product:"{product}"',
        params=[
            SearchParam("product", "Nama product/service", "nginx"),
        ],
        category="cloud",
        example='org:"Microsoft Azure" product:"nginx"',
        tags=["azure", "microsoft", "cloud"],
    ),
    SearchTemplate(
        id="cloud_digitalocean",
        name="DigitalOcean Droplets",
        description="Cari services di DigitalOcean",
        emoji="🌊",
        query_template='org:"DigitalOcean" country:"{country}"',
        params=[
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="cloud",
        example='org:"DigitalOcean" country:"ID"',
        tags=["digitalocean", "cloud"],
    ),

    # ─── BY COUNTRY / REGION ───────────────────────────────

    SearchTemplate(
        id="region_overview",
        name="Overview Negara",
        description="Lihat ringkasan semua service yang terekspos di suatu negara",
        emoji="🗺️",
        query_template='country:"{country}"',
        params=[
            SearchParam("country", "Kode negara (2 huruf)", "ID"),
        ],
        category="country",
        example='country:"ID"',
        facets="org:10,port:10,product:10,os:5",
        tags=["country", "overview", "stats"],
    ),
    SearchTemplate(
        id="region_city",
        name="Overview Kota",
        description="Lihat ringkasan perangkat terekspos di kota tertentu",
        emoji="🏙️",
        query_template='city:"{city}" country:"{country}"',
        params=[
            SearchParam("city", "Nama kota", "Jakarta"),
            SearchParam("country", "Kode negara", "ID"),
        ],
        category="country",
        example='city:"Jakarta" country:"ID"',
        facets="org:10,port:10,product:10",
        tags=["city", "overview"],
    ),
]


def get_template_by_id(template_id: str) -> SearchTemplate | None:
    """Get template by its unique ID."""
    for t in TEMPLATES:
        if t.id == template_id:
            return t
    return None


def get_templates_by_category(category: str) -> list[SearchTemplate]:
    """Get all templates in a category."""
    return [t for t in TEMPLATES if t.category == category]


def search_templates(keyword: str) -> list[SearchTemplate]:
    """Search templates by keyword in name, description, or tags."""
    keyword = keyword.lower()
    results = []
    for t in TEMPLATES:
        if (
            keyword in t.name.lower()
            or keyword in t.description.lower()
            or any(keyword in tag for tag in t.tags)
        ):
            results.append(t)
    return results


def build_query(template: SearchTemplate, values: dict[str, str]) -> str:
    """Build a Shodan query string from template + user values."""
    query = template.query_template
    for param in template.params:
        placeholder = "{" + param.name + "}"
        value = values.get(param.name, param.placeholder)
        query = query.replace(placeholder, value)
    return query
