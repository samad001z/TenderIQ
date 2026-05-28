"""Generate 7 realistic bid PDF sets for the demo tender (CPPP/SI/NEPAP-B/2026-27/001).

Each persona produces:
  • {slug}_technical.pdf — ~25-page bound bid document with all statutory
    annexures laid out as they appear in a real GeM/CPPP submission:
    GST REG-06, PAN/ITR, CA-certified turnover statement, ISO 9001/27001
    certificates (with cert no. + UKAS/NABCB accreditation refs), CMMI
    appraisal letter, PPP-MII self-certification, CVC Integrity Pact in full,
    EMD bank receipt, OEM/MAF letters from Dell/Cisco/Microsoft, BIS licence
    details, non-blacklisting affidavit on stamp-paper format, Power of
    Attorney, signatory declaration.
  • {slug}_financial.pdf — 3-page priced BoQ.

Personas (drive every Phase-5 decision path):
  A — StellarTech            : eligible · compliant · QCBS ≈ 91 · 85% of est → AWARD
  B — Velocity Systems       : tech PASS but OEM/MAF MISSING → DISAGREEMENT
  C — BudgetBuild Co         : abnormally low (52%) · MII Class-II · BIS missing → REJECT
  D — ShadowBuild Co         : clone of BudgetBuild → DUPLICATE FLAG
  E — MeridianTech           : eligible · priced ~73% — cartel cluster member
  F — OrbitInfra             : eligible · priced ~74% — cartel cluster member
  G — NexusBuild             : eligible · priced ~74% — cartel cluster member
  (E + F + G land within ~1.5% of each other → triggers cartel integrity flag)

Run:  uv run python scripts/generate_synthetic_bids.py
"""
from __future__ import annotations

import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable, KeepTogether, PageBreak

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent.parent.parent / "tests" / "synthetic_bids"
OUT.mkdir(parents=True, exist_ok=True)


# --- Register a Unicode-aware TTF so the Rupee glyph (₹, U+20B9) survives PDF text
# extraction. Reportlab's built-in Type-1 Helvetica has no ₹ → it gets mapped to "I",
# which then poisons every citation. Arial (Windows) and DejaVu (Linux) both include ₹.
FONT_R, FONT_B, FONT_I = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
_TTF_CANDIDATES = (
    [("Arial", r"C:\Windows\Fonts\arial.ttf"),
     ("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"),
     ("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf")]
    if platform.system() == "Windows"
    else [("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
          ("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
          ("DejaVu-Italic", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf")]
)
_present = [(n, p) for n, p in _TTF_CANDIDATES if Path(p).exists()]
if len(_present) >= 3:
    for n, p in _present:
        pdfmetrics.registerFont(TTFont(n, p))
    fam = _present[0][0]
    pdfmetrics.registerFontFamily(fam, normal=fam, bold=f"{fam}-Bold", italic=f"{fam}-Italic")
    FONT_R, FONT_B, FONT_I = fam, f"{fam}-Bold", f"{fam}-Italic"


# ---------------------------------------------------------------------------
# Persona — every "fact" is a stable, citable sentence agents quote verbatim.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Persona:
    slug: str
    org_name: str
    bidder_email: str
    contact_name: str
    # Statutory IDs — real-looking formats (15-digit GSTIN, 10-char PAN)
    gstin: str
    pan: str
    cin: str
    registered_office: str
    incorporated_year: int
    # Eligibility
    turnover_inr_cr: float          # avg annual turnover (₹ crore)
    years_experience: int
    past_projects: tuple[tuple[str, str, str, str], ...]
    # (client, scope, value_cr, period)
    # Technical
    technical_summary: str
    methodology: str
    team_strength: int
    pmp_certified_leads: int
    # Compliance
    mii_class: str                  # "I" / "II"
    mii_local_content_pct: int
    integrity_pact_signed: bool
    emd_utr: str
    emd_bank: str
    oem_present: bool
    bis_iso_present: bool
    # ISO / CMMI certificate numbers (rendered on cert pages)
    iso_9001_cert_no: str
    iso_27001_cert_no: str
    cmmi_appraisal_id: str
    bis_licence_no: str
    # Financial
    quoted_total_inr: int
    pct_of_estimate: int


PERSONAS: list[Persona] = [
    Persona(
        slug="stellartech",
        org_name="StellarTech Pvt Ltd",
        bidder_email="bidder.stellartech@tenderiq.test",
        contact_name="Anjali Rao",
        gstin="27AABCS9415F1ZQ",
        pan="AABCS9415F",
        cin="U72200MH2014PTC257118",
        registered_office="StellarTech Tower, 14 Senapati Bapat Road, Pune 411053, Maharashtra",
        incorporated_year=2014,
        turnover_inr_cr=62.0,
        years_experience=12,
        past_projects=(
            ("Central Board of Indirect Taxes & Customs (CBIC), Govt. of India",
             "National Tax Analytics Modernization — data lake, anomaly engine, dashboards for 1,400 GST officers",
             "74", "2023-25"),
            ("Government of Maharashtra, Industries Dept.",
             "State e-Procurement Portal — full SI lifecycle, migration of 14,000 suppliers",
             "38", "2021-23"),
            ("Ministry of Consumer Affairs, Food & Public Distribution",
             "Centralized Consumer Grievance Platform — 2nd-prize Digital India Award 2022",
             "19", "2020-22"),
        ),
        technical_summary=(
            "Our proposed solution is a cloud-native, microservices-based analytics platform "
            "deployed on MeghRaj-compliant infrastructure with active-active replication across "
            "Mumbai and Bhubaneswar regions. The architecture comprises 11 loosely-coupled "
            "services (ingestion, normalization, classification, anomaly-detection, dashboarding, "
            "audit, RBAC, retention, search, notifications, reporting) communicating over an event "
            "bus, with PostgreSQL + Apache Iceberg as primary stores and OpenSearch as the "
            "exploration layer. All inter-service calls are mTLS-secured and every request is "
            "tagged with a correlation id captured in the audit trail."
        ),
        methodology=(
            "We follow CMMI-L5 SDLC with parallel discovery, design, build and pilot tracks. "
            "Discovery completes in 6 weeks (ministry workshops, AS-IS mapping, ICD freeze); "
            "Build runs 22 weeks across 4 sprints of 5 weeks each, with end-of-sprint UAT by a "
            "designated counterpart team; Pilot covers 3 sample CPSEs for 8 weeks before go-live; "
            "Hypercare extends 12 weeks post go-live with on-site engineers. The complete WBS, "
            "RACI, and risk register are attached at Annexure-III."
        ),
        team_strength=18,
        pmp_certified_leads=5,
        mii_class="I",
        mii_local_content_pct=62,
        integrity_pact_signed=True,
        emd_utr="HDFCN26052800447118",
        emd_bank="HDFC Bank, Senapati Bapat Road branch, Pune",
        oem_present=True,
        bis_iso_present=True,
        iso_9001_cert_no="IN-QMS-2022-114782",
        iso_27001_cert_no="IN-ISMS-2024-027113",
        cmmi_appraisal_id="CMMI-A-2024-IN-1142",
        bis_licence_no="CM/L-1247211",
        quoted_total_inr=72_250_000,
        pct_of_estimate=85,
    ),
    Persona(
        slug="velocity",
        org_name="Velocity Systems",
        bidder_email="bidder.velocity@tenderiq.test",
        contact_name="Rohan Mehta",
        gstin="27AABCV2287H1ZD",
        pan="AABCV2287H",
        cin="U72200MH2017PTC301992",
        registered_office="Velocity House, Plot 88, Hinjewadi Phase 2, Pune 411057, Maharashtra",
        incorporated_year=2017,
        turnover_inr_cr=48.0,
        years_experience=9,
        past_projects=(
            ("Ministry of Ports, Shipping & Waterways",
             "Logistics Visibility Platform — real-time AIS ingestion + dashboards",
             "52", "2022-24"),
            ("Goods & Services Tax Network (GSTN)",
             "GST Returns Reconciliation Service — 3.4 billion line items processed",
             "27", "2020-22"),
            ("Surat Municipal Corporation",
             "Smart Cities Integrated Command Centre",
             "21", "2019-21"),
        ),
        technical_summary=(
            "Velocity proposes a Kubernetes-native, microservices-first analytics fabric "
            "delivered as 14 independently-deployable services across two GoI-empanelled "
            "cloud regions. The platform features a domain-driven event bus (NATS JetStream), "
            "polyglot persistence (PostgreSQL for OLTP, ClickHouse for OLAP, Redis for hot "
            "lookups), and an ML-assisted anomaly engine (XGBoost + isolation forests) tuned "
            "on three years of historical e-procurement transactions. Every public API is "
            "versioned (v1, v2) and contract-tested with Pact in the CI pipeline."
        ),
        methodology=(
            "We follow a hybrid Agile-V approach. Sprint 0 (4 weeks) covers requirements "
            "elaboration, ICD freeze and infrastructure baselining. Build is divided into 5 "
            "sprints of 4 weeks; each sprint ends with a counterpart-led UAT cycle, a "
            "DAST/SAST run (Burp Pro + Semgrep), and a load-test gate (target: 3000 RPS at "
            "p95 < 350 ms). Cutover is staged across three CPSEs over 6 weeks; on-site "
            "hypercare runs 10 weeks. End-to-end traceability is maintained in Jira + Confluence."
        ),
        team_strength=16,
        pmp_certified_leads=4,
        mii_class="I",
        mii_local_content_pct=58,
        integrity_pact_signed=True,
        emd_utr="ICICN26052800552210",
        emd_bank="ICICI Bank, Hinjewadi branch, Pune",
        oem_present=False,            # ← deliberate flaw: OEM authorization MISSING
        bis_iso_present=True,
        iso_9001_cert_no="IN-QMS-2021-098212",
        iso_27001_cert_no="IN-ISMS-2023-019007",
        cmmi_appraisal_id="CMMI-A-2024-IN-0991",
        bis_licence_no="CM/L-1187442",
        quoted_total_inr=68_000_000,  # 80% of estimate
        pct_of_estimate=80,
    ),
    # ShadowBuild — a proxy / shell submission cloning BudgetBuild's bid with only
    # the legal name + email changed. Duplicate detector flags both for human review.
    Persona(
        slug="shadowbuild",
        org_name="ShadowBuild Co",
        bidder_email="bidder.shadowbuild@tenderiq.test",
        contact_name="Suresh Patil",  # same signatory as BudgetBuild — proxy smoking gun
        gstin="27AABCS4081L1ZP",
        pan="AABCS4081L",
        cin="U72200MH2020PTC312044",
        registered_office="3rd Floor, Plot 47, MIDC Bhosari, Pune 411026, Maharashtra",
        incorporated_year=2020,
        turnover_inr_cr=18.0,
        years_experience=6,
        past_projects=(
            ("District Collectorate, Solapur",
             "District Records Digitisation — 1.1 lakh records scanned & indexed",
             "4.2", "2023"),
            ("Rural Development Dept., Govt. of Maharashtra",
             "Panchayat Accounting Rollout — partial scope",
             "2.8", "2022"),
        ),
        technical_summary=(
            "BudgetBuild will deliver the analytics platform using proven web technologies. "
            "We propose a three-tier architecture (frontend, application server, database) "
            "hosted on Linux VMs with daily backups. The system will provide dashboards and "
            "downloadable reports for procurement officers."
        ),
        methodology=(
            "We will follow a Waterfall methodology with monthly status reviews. Project "
            "phases: Requirements → Design → Build → Testing → Deployment. Detailed plans "
            "will be furnished after award."
        ),
        team_strength=4,
        pmp_certified_leads=0,
        mii_class="II",
        mii_local_content_pct=35,
        integrity_pact_signed=True,
        emd_utr="SBIN26052800881009",  # ← identical UTR — smoking-gun duplicate
        emd_bank="State Bank of India, Bhosari MIDC branch, Pune",
        oem_present=True,
        bis_iso_present=False,
        iso_9001_cert_no="IN-QMS-2023-201882",
        iso_27001_cert_no="",
        cmmi_appraisal_id="",
        bis_licence_no="",
        quoted_total_inr=44_200_000,  # identical price → textbook duplicate
        pct_of_estimate=52,
    ),
    Persona(
        slug="budgetbuild",
        org_name="BudgetBuild Co",
        bidder_email="bidder.budgetbuild@tenderiq.test",
        contact_name="Suresh Patil",
        gstin="27AABCB7720K1ZR",
        pan="AABCB7720K",
        cin="U72200MH2020PTC308221",
        registered_office="Shop 12, Sai Plaza, Bhosari MIDC, Pune 411026, Maharashtra",
        incorporated_year=2020,
        turnover_inr_cr=18.0,
        years_experience=6,
        past_projects=(
            ("District Collectorate, Solapur",
             "District Records Digitisation — 1.1 lakh records scanned & indexed",
             "4.2", "2023"),
            ("Rural Development Dept., Govt. of Maharashtra",
             "Panchayat Accounting Rollout — partial scope",
             "2.8", "2022"),
        ),
        technical_summary=(
            "BudgetBuild will deliver the analytics platform using proven web technologies. "
            "We propose a three-tier architecture (frontend, application server, database) "
            "hosted on Linux VMs with daily backups. The system will provide dashboards and "
            "downloadable reports for procurement officers."
        ),
        methodology=(
            "We will follow a Waterfall methodology with monthly status reviews. Project "
            "phases: Requirements → Design → Build → Testing → Deployment. Detailed plans "
            "will be furnished after award."
        ),
        team_strength=4,
        pmp_certified_leads=0,
        mii_class="II",                # Class-II — fails MII Class-I requirement
        mii_local_content_pct=35,
        integrity_pact_signed=True,
        emd_utr="SBIN26052800881009",
        emd_bank="State Bank of India, Bhosari MIDC branch, Pune",
        oem_present=True,
        bis_iso_present=False,         # ← deliberate flaw: BIS / ISO 27001 MISSING
        iso_9001_cert_no="IN-QMS-2023-201881",
        iso_27001_cert_no="",
        cmmi_appraisal_id="",
        bis_licence_no="",
        quoted_total_inr=44_200_000,   # 52% — abnormally low (>20% below)
        pct_of_estimate=52,
    ),
    # ----- Cartel cluster — Meridian + Orbit + Nexus quote within ~1.5% of each
    # other (~73-74% of estimate). The risk_agent's cartel rule (3+ bids within
    # 2 percentage-point band) should flag all three for integrity review.
    Persona(
        slug="meridian",
        org_name="MeridianTech Solutions Pvt Ltd",
        bidder_email="bidder.meridian@tenderiq.test",
        contact_name="Kavita Joshi",
        gstin="29AABCM5519G1ZF",
        pan="AABCM5519G",
        cin="U72200KA2015PTC289117",
        registered_office="MeridianTech Campus, EPIP Zone, Whitefield, Bengaluru 560066, Karnataka",
        incorporated_year=2015,
        turnover_inr_cr=54.0,
        years_experience=10,
        past_projects=(
            ("National Informatics Centre (NIC)",
             "Cloud Migration & Modernization — 38 mission-mode applications",
             "61", "2022-24"),
            ("Karnataka State Council for Science & Technology",
             "Statewide GIS Decision-Support Platform",
             "29", "2020-22"),
            ("Indian Council of Medical Research (ICMR)",
             "Multi-centric Clinical-Trial Data Platform",
             "23", "2019-21"),
        ),
        technical_summary=(
            "MeridianTech proposes a service-mesh-anchored microservices platform on Istio + "
            "Kubernetes with 13 services spanning ingestion, classification, anomaly, audit and "
            "presentation layers. Persistence is split: TimescaleDB for time-series, PostgreSQL "
            "for OLTP, MinIO with S3-API for object store. Every request carries an OpenTelemetry "
            "trace propagated end-to-end; SLO dashboards (latency, error rate, saturation) ship "
            "preconfigured in Grafana."
        ),
        methodology=(
            "Hybrid Scrum-of-Scrums across 3 feature teams. Each team runs 3-week sprints with "
            "demo days and joint review. Cross-team integration sprints every 6 weeks. UAT in 4 "
            "stages — unit acceptance, integration acceptance, security acceptance (CERT-In "
            "empanelled vendor), and ministry acceptance. PIR (post-implementation review) at "
            "T+45 days post go-live."
        ),
        team_strength=20,
        pmp_certified_leads=6,
        mii_class="I",
        mii_local_content_pct=55,
        integrity_pact_signed=True,
        emd_utr="AXISN26052800771203",
        emd_bank="Axis Bank, Whitefield branch, Bengaluru",
        oem_present=True,
        bis_iso_present=True,
        iso_9001_cert_no="IN-QMS-2022-145331",
        iso_27001_cert_no="IN-ISMS-2024-031709",
        cmmi_appraisal_id="CMMI-A-2024-IN-1187",
        bis_licence_no="CM/L-1342099",
        quoted_total_inr=62_100_000,   # 73.0% of est
        pct_of_estimate=73,
    ),
    Persona(
        slug="orbit",
        org_name="Orbit Infra Pvt Ltd",
        bidder_email="bidder.orbit@tenderiq.test",
        contact_name="Vikram Singh",
        gstin="07AABCO8812R1ZJ",
        pan="AABCO8812R",
        cin="U72200DL2014PTC272003",
        registered_office="Orbit House, 12-A Nehru Place, New Delhi 110019",
        incorporated_year=2014,
        turnover_inr_cr=57.0,
        years_experience=11,
        past_projects=(
            ("Department of Telecommunications, Govt. of India",
             "Spectrum Audit Platform — pan-India operator data ingestion",
             "66", "2022-24"),
            ("Bureau of Indian Standards (BIS)",
             "Mark Compliance Tracker — 220+ laboratories integrated",
             "33", "2021-23"),
            ("Indian Railway Finance Corporation",
             "Treasury Reconciliation Platform",
             "24", "2019-21"),
        ),
        technical_summary=(
            "Orbit Infra proposes a layered, event-driven analytics platform on Red Hat OpenShift "
            "with 12 microservices, Kafka as the canonical event backbone, and a CDC pipeline "
            "(Debezium) feeding both OLAP (Apache Druid) and the search index (Elasticsearch). "
            "Identity is federated via the procuring entity's existing Active Directory through "
            "Keycloak as the IAM hub; every action is captured in an immutable audit log."
        ),
        methodology=(
            "We follow SAFe 6.0 with two Agile Release Trains (ART). PI planning every 10 weeks. "
            "Each ART runs 5 iterations of 2 weeks. Continuous Integration via GitLab CI; "
            "Continuous Delivery via Argo CD with progressive (canary) rollouts. Cyber security "
            "audit by a CERT-In empanelled vendor in iteration 8 of every PI."
        ),
        team_strength=22,
        pmp_certified_leads=7,
        mii_class="I",
        mii_local_content_pct=53,
        integrity_pact_signed=True,
        emd_utr="HDFCN26052800883112",
        emd_bank="HDFC Bank, Nehru Place branch, New Delhi",
        oem_present=True,
        bis_iso_present=True,
        iso_9001_cert_no="IN-QMS-2021-128009",
        iso_27001_cert_no="IN-ISMS-2023-022114",
        cmmi_appraisal_id="CMMI-A-2024-IN-1006",
        bis_licence_no="CM/L-1218883",
        quoted_total_inr=62_700_000,   # 73.7% of est
        pct_of_estimate=74,
    ),
    Persona(
        slug="nexus",
        org_name="NexusBuild Technologies Pvt Ltd",
        bidder_email="bidder.nexus@tenderiq.test",
        contact_name="Priya Subramanian",
        gstin="33AABCN1190M1ZV",
        pan="AABCN1190M",
        cin="U72200TN2016PTC312045",
        registered_office="Nexus Tower, OMR Sholinganallur, Chennai 600119, Tamil Nadu",
        incorporated_year=2016,
        turnover_inr_cr=49.0,
        years_experience=9,
        past_projects=(
            ("Income Tax Department, Govt. of India",
             "Project Insight — Compliance & Risk Analytics Programme",
             "58", "2022-24"),
            ("Tamil Nadu e-Governance Agency",
             "Statewide Land Records Modernisation Platform",
             "31", "2020-22"),
            ("National Stock Exchange Indices Ltd",
             "Market-Surveillance Analytics Refresh",
             "18", "2019-21"),
        ),
        technical_summary=(
            "NexusBuild offers a containerised microservices platform on Amazon EKS (with a "
            "private GoI-empanelled cloud landing zone) comprising 13 services. The data plane "
            "uses Aurora PostgreSQL (OLTP), Apache Pinot (OLAP) and Apache Flink for stream "
            "processing. Observability via Prometheus + Tempo + Loki; secrets via HashiCorp "
            "Vault; service identity via SPIRE / SPIFFE."
        ),
        methodology=(
            "Disciplined Agile Delivery (DAD) with 3 inception sprints (4 weeks total), 8 "
            "construction sprints (3 weeks each), and a transition / hardening sprint. Quality "
            "gates: SAST in every CI run, DAST nightly, IAST during integration testing, "
            "performance test at the end of each construction sprint. Production readiness "
            "review (PRR) at sprint 11."
        ),
        team_strength=17,
        pmp_certified_leads=5,
        mii_class="I",
        mii_local_content_pct=51,
        integrity_pact_signed=True,
        emd_utr="ICICN26052800997410",
        emd_bank="ICICI Bank, Sholinganallur branch, Chennai",
        oem_present=True,
        bis_iso_present=True,
        iso_9001_cert_no="IN-QMS-2022-167091",
        iso_27001_cert_no="IN-ISMS-2024-034017",
        cmmi_appraisal_id="CMMI-A-2024-IN-1233",
        bis_licence_no="CM/L-1291144",
        quoted_total_inr=63_000_000,   # 74.1% of est
        pct_of_estimate=74,
    ),
]


# ---------------------------------------------------------------------------
# Render helpers — Platypus flowables shared across page builders.
# ---------------------------------------------------------------------------
GOLD = colors.HexColor("#B8941E")
INK = colors.HexColor("#0B0D0F")
SUBINK = colors.HexColor("#1C2024")
MUTED = colors.HexColor("#5E646B")
PAPER = colors.HexColor("#F6F2E3")
PAPER_DK = colors.HexColor("#E8E2CF")
LINE = colors.HexColor("#A0A6AE")
LINE_LT = colors.HexColor("#C0C6CE")
RED = colors.HexColor("#B0341A")


def _styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=FONT_B,
                             fontSize=18, leading=22, spaceAfter=6, textColor=INK),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=FONT_B,
                             fontSize=13, leading=17, spaceBefore=8, spaceAfter=4, textColor=INK),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName=FONT_B,
                             fontSize=11, leading=15, spaceBefore=6, spaceAfter=3, textColor=INK),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=FONT_R,
                               fontSize=10.5, leading=15, spaceAfter=4, textColor=SUBINK),
        "label": ParagraphStyle("label", parent=base["BodyText"], fontName=FONT_B,
                                fontSize=10, leading=13, textColor=INK),
        "muted": ParagraphStyle("muted", parent=base["BodyText"], fontName=FONT_I,
                                fontSize=9.5, leading=13, textColor=MUTED),
        "warn": ParagraphStyle("warn", parent=base["BodyText"], fontName=FONT_B,
                               fontSize=11, leading=15, textColor=RED),
        "center": ParagraphStyle("center", parent=base["BodyText"], fontName=FONT_R,
                                 fontSize=10.5, leading=15, alignment=1, textColor=SUBINK),
        "center_b": ParagraphStyle("center_b", parent=base["BodyText"], fontName=FONT_B,
                                   fontSize=14, leading=18, alignment=1, textColor=INK),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName=FONT_R,
                                fontSize=9, leading=12, textColor=MUTED),
    }


def _kv(label: str, value: str) -> Table:
    t = Table([[label, value]], colWidths=[5.4 * cm, 11.0 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), FONT_B),
        ("FONTNAME", (1, 0), (1, 0), FONT_R),
        ("FONTSIZE", (0, 0), (-1, -1), 10.5),
        ("TEXTCOLOR", (0, 0), (0, 0), INK),
        ("TEXTCOLOR", (1, 0), (1, 0), SUBINK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _inr(amount: int) -> str:
    n = str(amount)[::-1]
    parts = [n[:3]]
    rest = n[3:]
    while rest:
        parts.append(rest[:2])
        rest = rest[2:]
    grouped = ",".join(parts)[::-1]
    return f"₹{grouped}"


def _cert_banner(title: str, subtitle: str | None = None) -> list:
    """Title banner used at the top of every formal certificate page."""
    s = _styles()
    out: list = []
    bar = Table([[Paragraph(f"<font color='#B8941E'><b>{title}</b></font>", s["center_b"])]],
                colWidths=[16.4 * cm])
    bar.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.5, GOLD),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF7E6")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    out.append(bar)
    if subtitle:
        out.append(Spacer(1, 4))
        out.append(Paragraph(subtitle, s["center"]))
    out.append(Spacer(1, 12))
    return out


def _gov_header(line1: str, line2: str) -> list:
    """Government-of-India style two-line header used on form-style certificate pages."""
    s = _styles()
    out: list = []
    out.append(Paragraph(f"<b>{line1}</b>", s["center_b"]))
    out.append(Paragraph(line2, s["center"]))
    out.append(Spacer(1, 4))
    out.append(HRFlowable(width="100%", thickness=0.8, color=GOLD))
    out.append(Spacer(1, 10))
    return out


def _sig_block(name: str, role: str, place: str = "Pune", date: str = "27-May-2026") -> list:
    s = _styles()
    return [
        Spacer(1, 22),
        Paragraph("[Signature & company seal affixed in original]", s["muted"]),
        Spacer(1, 6),
        _kv("Name:", name),
        _kv("Designation:", role),
        _kv("Place / Date:", f"{place} / {date}"),
    ]


# ---------------------------------------------------------------------------
# Page builders — each returns flowables for ONE page (caller adds PageBreak).
# ---------------------------------------------------------------------------
def page_cover(p: Persona) -> list:
    s = _styles()
    return [
        Paragraph("BID DOCUMENT — TECHNICAL PROPOSAL", s["h1"]),
        Paragraph("Selection of System Integrator — National e-Procurement Analytics "
                  "Platform (Package B)", s["h2"]),
        Spacer(1, 12),
        _kv("Tender Reference:", "CPPP/SI/NEPAP-B/2026-27/001"),
        _kv("Procuring Entity:", "Ministry of Electronics & IT, Government of India"),
        _kv("Bidder:", p.org_name),
        _kv("CIN:", p.cin),
        _kv("Authorised Signatory:", p.contact_name),
        _kv("Submission Date:", "27-May-2026"),
        _kv("Quoted Price (this bid):",
            f"{_inr(p.quoted_total_inr)} (approx. {p.pct_of_estimate}% of the estimated value)"),
        Spacer(1, 18),
        Paragraph("EXECUTIVE SUMMARY", s["h2"]),
        Paragraph(
            f"{p.org_name}, with audited annual turnover of ₹{p.turnover_inr_cr:.0f} crore "
            f"and {p.years_experience} years of demonstrable experience in delivering large-scale "
            f"system-integration engagements for the Government of India, is pleased to submit "
            f"this bid in response to the captioned tender. Our proposal is fully compliant with "
            f"the GFR 2017 framework, the PPP-MII Order (DPIIT P-45021/2/2017-PP), and the CVC "
            f"Integrity Pact regime.",
            s["body"]),
    ]


def page_index() -> list:
    s = _styles()
    flow: list = [Paragraph("INDEX OF ENCLOSED DOCUMENTS", s["h1"]),
                  Paragraph("Pages referenced below are within this technical proposal PDF.",
                            s["muted"])]
    items: list[tuple[str, str]] = [
        ("Cover & Executive Summary", "p.1"),
        ("Index of Enclosed Documents (this page)", "p.2"),
        ("Bidder Profile & Statutory IDs", "p.3"),
        ("GST Registration Certificate (Form GST REG-06)", "p.4"),
        ("PAN & Income-Tax Return Acknowledgement", "p.5"),
        ("CA-certified Annual Turnover Statement", "p.6"),
        ("Past Performance — Project 1", "p.7"),
        ("Past Performance — Project 2", "p.8"),
        ("Past Performance — Project 3", "p.9"),
        ("ISO 9001:2015 Certificate", "p.10"),
        ("ISO/IEC 27001:2022 Certificate", "p.11"),
        ("CMMI-DEV Level 5 Appraisal Letter", "p.12"),
        ("Technical Approach — Solution Architecture", "p.13"),
        ("Technical Approach — Methodology & Plan", "p.14"),
        ("Team & Key Personnel", "p.15"),
        ("PPP-MII Class-I Self-Certification", "p.16"),
        ("CVC Integrity Pact (signed)", "p.17"),
        ("Earnest Money Deposit (EMD) — Bank Receipt", "p.18"),
        ("OEM Authorization — Dell Technologies", "p.19"),
        ("OEM Authorization — Cisco Systems", "p.20"),
        ("OEM Authorization — Microsoft India", "p.21"),
        ("BIS / ISI Licence Particulars", "p.22"),
        ("Affidavit of Non-Blacklisting", "p.23"),
        ("Power of Attorney for Authorised Signatory", "p.24"),
        ("Declarations & Authorised Signature", "p.25"),
    ]
    rows = [["S.No.", "Annexure", "Page"]] + [[str(i), n, pg] for i, (n, pg) in enumerate(items, 1)]
    t = Table(rows, colWidths=[1.2 * cm, 12.0 * cm, 4.0 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_R),
        ("FONTNAME", (0, 0), (-1, 0), FONT_B),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), PAPER_DK),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE_LT),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    flow.append(t)
    return flow


def page_profile(p: Persona) -> list:
    s = _styles()
    return [
        Paragraph("BIDDER PROFILE & STATUTORY IDENTIFIERS", s["h1"]),
        _kv("Registered name:", p.org_name),
        _kv("CIN:", p.cin),
        _kv("PAN:", p.pan),
        _kv("GSTIN:", p.gstin),
        _kv("Registered office:", p.registered_office),
        _kv("Incorporated:", f"FY {p.incorporated_year}-{(p.incorporated_year + 1) % 100:02d}"),
        _kv("Years in business:", f"{p.years_experience} years"),
        _kv("Audited annual turnover (FY 2023-24):", f"₹{p.turnover_inr_cr:.2f} crore"),
        _kv("MSE status:", "No"),
        _kv("Authorised signatory:", f"{p.contact_name}, Director"),
        Spacer(1, 10),
        Paragraph(
            f"{p.org_name} is a Government-empanelled system integrator. Our entire delivery "
            f"workforce is on-roll, and all key personnel have undergone background verification "
            f"through a CERT-In empanelled agency. The firm has filed all statutory returns up "
            f"to AY 2024-25 and has no overdue tax liability.",
            s["body"]),
    ]


def page_gstin(p: Persona) -> list:
    s = _styles()
    flow = _gov_header(
        "GOVERNMENT OF INDIA — GOODS AND SERVICES TAX",
        "Form GST REG-06 — Registration Certificate (Rule 10(1) of the CGST Rules, 2017)",
    )
    flow.append(_kv("Registration Number (GSTIN):", p.gstin))
    flow.append(_kv("Legal name of business:", p.org_name))
    flow.append(_kv("Trade name, if any:", p.org_name))
    flow.append(_kv("Constitution of business:", "Private Limited Company"))
    flow.append(_kv("Address of principal place of business:", p.registered_office))
    flow.append(_kv("Date of liability:", f"01-Apr-{p.incorporated_year}"))
    flow.append(_kv("Date of validity:", "Not applicable (regular tax-payer)"))
    flow.append(_kv("Type of registration:", "Regular"))
    flow.append(_kv("Particulars of approving authority:",
                    "Asst. Commissioner of State Tax, Pune-II Division"))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        "This is a system-generated certificate and does not require physical signature. "
        "It is downloaded from the GST common portal (www.gst.gov.in) on 26-May-2026.",
        s["muted"]))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        "We hereby produce a true copy of the GST REG-06 issued to the firm. The certificate is "
        "currently active and has not been suspended, cancelled or surrendered.",
        s["body"]))
    flow.extend(_sig_block(p.contact_name, "Director"))
    return flow


def page_pan_itr(p: Persona) -> list:
    s = _styles()
    flow = _gov_header(
        "INCOME TAX DEPARTMENT — GOVERNMENT OF INDIA",
        "Permanent Account Number (PAN) & Latest ITR Acknowledgement (ITR-V)",
    )
    flow.append(Paragraph("PAN PARTICULARS", s["h3"]))
    flow.append(_kv("Permanent Account Number (PAN):", p.pan))
    flow.append(_kv("Name of the assessee:", p.org_name))
    flow.append(_kv("Date of allotment:", f"15-May-{p.incorporated_year}"))
    flow.append(_kv("Status:", "Company (resident)"))
    flow.append(Spacer(1, 10))
    flow.append(Paragraph("LATEST RETURN — ITR-V (AY 2024-25)", s["h3"]))
    flow.append(_kv("Acknowledgement number:", f"{p.pan[:5]}{p.incorporated_year}1729{p.pan[5:]}"))
    flow.append(_kv("ITR form used:", "ITR-6"))
    flow.append(_kv("Filed under section:", "139(1) — return on or before due date"))
    flow.append(_kv("Date of filing:", "29-Oct-2024"))
    flow.append(_kv("Mode of verification:", "Digital Signature Certificate (DSC) — Class-III"))
    flow.append(_kv("Total income returned (₹):",
                    f"{int(p.turnover_inr_cr * 1_00_00_000 * 0.12):,}"))
    flow.append(_kv("Tax paid (₹):", f"{int(p.turnover_inr_cr * 1_00_00_000 * 0.12 * 0.25):,}"))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "The return has been e-verified and stands accepted on the income-tax portal. There are "
        "no outstanding scrutiny proceedings or tax demands against the firm as on the date of "
        "bid submission.",
        s["body"]))
    return flow


def page_turnover(p: Persona) -> list:
    s = _styles()
    flow: list = [
        Paragraph("ANNUAL TURNOVER — CA-CERTIFIED STATEMENT", s["h1"]),
        Paragraph(
            "Certified by M/s Joshi & Bhandari, Chartered Accountants — Firm Reg. No. 109817W "
            "(ICAI). UDIN: 24109817BKAVQR8842.", s["muted"]),
        Spacer(1, 8),
    ]
    fy_turnover = [
        ("2021-22", round(p.turnover_inr_cr * 0.82, 2)),
        ("2022-23", round(p.turnover_inr_cr * 0.93, 2)),
        ("2023-24", p.turnover_inr_cr),
    ]
    avg = sum(v for _, v in fy_turnover) / 3
    rows = [["Financial Year", "Audited Turnover (₹ crore)", "PBT (₹ crore)"]]
    for fy, val in fy_turnover:
        rows.append([fy, f"₹{val:.2f}", f"₹{round(val * 0.14, 2):.2f}"])
    rows.append(["Three-year average", f"₹{avg:.2f}", f"₹{round(avg * 0.14, 2):.2f}"])
    t = Table(rows, colWidths=[5.2 * cm, 5.6 * cm, 5.6 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_R),
        ("FONTNAME", (0, 0), (-1, 0), FONT_B),
        ("FONTNAME", (0, -1), (-1, -1), FONT_B),
        ("BACKGROUND", (0, 0), (-1, 0), PAPER_DK),
        ("BACKGROUND", (0, -1), (-1, -1), PAPER),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE_LT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        f"We confirm that the audited annual turnover for FY 2023-24 stood at "
        f"₹{p.turnover_inr_cr:.2f} crore, with a three-year average of ₹{avg:.2f} crore. "
        f"This satisfies the tender's minimum-turnover requirement of ₹15 crore per annum and "
        f"the three-FY average requirement of ₹15 crore.",
        s["body"]))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        f"Continuous operating experience as a system integrator: {p.years_experience} years "
        f"(exceeding the tender's minimum of five years).",
        s["body"]))
    flow.append(Spacer(1, 20))
    flow.append(Paragraph(
        "For Joshi & Bhandari, Chartered Accountants<br/>"
        "(Sd/-) CA. Priya Joshi, Partner — M.No. 117009", s["body"]))
    return flow


def page_past_project(p: Persona, idx: int) -> list:
    s = _styles()
    client, scope, value_cr, period = p.past_projects[idx]
    flow = [
        Paragraph(f"PAST PERFORMANCE — PROJECT {idx + 1}", s["h1"]),
        Paragraph(
            "Completion / Experience Certificate enclosed at this page is a true copy of the "
            "original issued by the client's competent authority.", s["muted"]),
        Spacer(1, 8),
        _kv("Client:", client),
        _kv("Scope of work:", scope),
        _kv("Order/contract value:", f"₹{value_cr} crore "
                                     f"(exceeds the ₹3 crore tender minimum)"),
        _kv("Period of execution:", period),
        _kv("Delivery status:", "Completed and accepted by client"),
        _kv("Performance rating (client):", "Satisfactory / Exceeds expectations"),
        Spacer(1, 14),
    ]
    flow += _cert_banner(
        "EXPERIENCE / COMPLETION CERTIFICATE",
        f"Issued by {client.split(',')[0]} on the firm's letterhead, dated 18-Apr-2025",
    )
    flow.append(Paragraph(
        f"This is to certify that <b>{p.org_name}</b> has successfully executed the project "
        f"<i>{scope.split('—')[0].strip()}</i> for this Office during the period {period}, with "
        f"a contract value of ₹{value_cr} crore. The work has been completed in accordance with "
        f"the agreed scope, timelines and quality requirements. There are no pending "
        f"liquidated-damages, penalty or arbitration proceedings against the firm in relation "
        f"to this engagement.", s["body"]))
    flow.append(Spacer(1, 18))
    flow.append(Paragraph("(Sd/-) Authorised Signatory, Project Authority", s["body"]))
    flow.append(Paragraph("Designation: Deputy Secretary / Director (project owner)", s["muted"]))
    return flow


def page_iso_9001(p: Persona) -> list:
    s = _styles()
    flow = _cert_banner(
        "CERTIFICATE OF REGISTRATION",
        "Quality Management System — ISO 9001:2015",
    )
    flow.append(Paragraph(
        f"This is to certify that the Quality Management System of",
        s["center"]))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(f"<b>{p.org_name}</b>", s["center_b"]))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(p.registered_office, s["center"]))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        "has been assessed and registered against the requirements of <b>ISO 9001:2015</b> for "
        "the following scope: <i>Design, development, deployment and support of enterprise "
        "software systems and managed services for public-sector clients.</i>",
        s["body"]))
    flow.append(Spacer(1, 10))
    flow.append(_kv("Certificate No.:", p.iso_9001_cert_no))
    flow.append(_kv("Date of initial registration:", "15-Aug-2018"))
    flow.append(_kv("Date of current issue:", "14-Aug-2024"))
    flow.append(_kv("Date of expiry:", "14-Aug-2027"))
    flow.append(_kv("Surveillance audit due:", "14-Aug-2026"))
    flow.append(_kv("Issuing Body:", "BSI (India) Pvt. Ltd."))
    flow.append(_kv("Accreditation:", "NABCB (Reg. QM-019) / UKAS (Reg. 0086)"))
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(
        "Validity of this certificate is subject to the firm maintaining its QMS to the "
        "required standard, which will be monitored by surveillance audits at agreed intervals. "
        "Issued under the authority of the BSI Director of Certification.", s["muted"]))
    return flow


def page_iso_27001(p: Persona) -> list:
    s = _styles()
    if not p.iso_27001_cert_no:
        flow = _cert_banner(
            "ISO/IEC 27001:2022 — NOT APPLICABLE",
            "The firm does not presently hold an ISO/IEC 27001 certification.",
        )
        flow.append(Paragraph(
            "ISO/IEC 27001:2022 (Information Security Management System) certification is "
            "currently UNDER PROCESS and is NOT enclosed with this bid. We undertake to obtain "
            "the certification within ninety (90) days of the contract award.",
            s["warn"]))
        flow.append(Spacer(1, 10))
        flow.append(Paragraph(
            "We acknowledge that the tender mandates ISO 27001 certification as a pre-condition "
            "for technical responsiveness. The bidder may be required to clarify or remediate "
            "this omission during evaluation.", s["body"]))
        return flow
    flow = _cert_banner(
        "CERTIFICATE OF REGISTRATION",
        "Information Security Management System — ISO/IEC 27001:2022",
    )
    flow.append(Paragraph("This is to certify that the Information Security Management System of",
                          s["center"]))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(f"<b>{p.org_name}</b>", s["center_b"]))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(p.registered_office, s["center"]))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        "has been assessed against the requirements of <b>ISO/IEC 27001:2022</b> for the "
        "following Statement of Applicability scope: <i>Confidentiality, integrity and "
        "availability controls covering software design, development, hosting and managed "
        "services delivery for Government clients</i>.", s["body"]))
    flow.append(Spacer(1, 10))
    flow.append(_kv("Certificate No.:", p.iso_27001_cert_no))
    flow.append(_kv("Date of initial registration:", "02-Mar-2021"))
    flow.append(_kv("Date of current issue:", "02-Mar-2024"))
    flow.append(_kv("Date of expiry:", "02-Mar-2027"))
    flow.append(_kv("Surveillance audit due:", "02-Mar-2026"))
    flow.append(_kv("Issuing Body:", "TÜV SÜD South Asia Pvt. Ltd."))
    flow.append(_kv("Accreditation:", "NABCB (Reg. IS-008) / IAS / UKAS"))
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(
        "This certificate is the property of the issuing body and shall be returned upon "
        "request. Authenticity may be verified at the issuing body's online registry.", s["muted"]))
    return flow


def page_cmmi(p: Persona) -> list:
    s = _styles()
    if not p.cmmi_appraisal_id:
        flow = _cert_banner(
            "CMMI APPRAISAL — NOT APPLICABLE",
            "The firm does not presently hold a CMMI-DEV Level 5 appraisal.",
        )
        flow.append(Paragraph(
            "CMMI-DEV Level 5 appraisal certificate: NOT ENCLOSED. The firm holds CMMI-DEV "
            "Level 3 only and acknowledges that this falls short of the tender's Level 5 "
            "requirement.", s["warn"]))
        return flow
    flow = _cert_banner(
        "CMMI INSTITUTE / ISACA — APPRAISAL DISCLOSURE STATEMENT",
        "Capability Maturity Model Integration for Development (CMMI-DEV) — Maturity Level 5",
    )
    flow.append(Paragraph(
        f"The Lead Appraiser hereby confirms that an SCAMPI Class-A Appraisal against CMMI-DEV "
        f"V2.0 was conducted at the firm <b>{p.org_name}</b> and resulted in the award of "
        f"<b>Maturity Level 5 (Optimizing)</b>.", s["body"]))
    flow.append(Spacer(1, 10))
    flow.append(_kv("Appraisal ID (PARS):", p.cmmi_appraisal_id))
    flow.append(_kv("Appraisal type:", "SCAMPI Class A (Benchmark)"))
    flow.append(_kv("Model & version:", "CMMI-DEV, V2.0"))
    flow.append(_kv("Maturity Level awarded:", "Level 5 — Optimizing"))
    flow.append(_kv("Lead Appraiser:", "Mr. Rajiv Subramanian (Certified Lead Appraiser #2117)"))
    flow.append(_kv("Sponsoring organization:", p.org_name))
    flow.append(_kv("Date of appraisal completion:", "11-Oct-2024"))
    flow.append(_kv("Validity (3-year cycle):", "until 11-Oct-2027"))
    flow.append(_kv("Re-appraisal due:", "before 11-Oct-2027"))
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(
        "The appraisal results were submitted to the CMMI Institute's Published Appraisal "
        "Results Site (PARS) and may be verified at https://cmmiinstitute.com/pars by searching "
        f"the Appraisal ID above.", s["muted"]))
    return flow


def page_tech_arch(p: Persona) -> list:
    s = _styles()
    return [
        Paragraph("TECHNICAL APPROACH — SOLUTION ARCHITECTURE", s["h1"]),
        Paragraph(p.technical_summary, s["body"]),
        Spacer(1, 8),
        Paragraph(
            "Reference architecture diagrams (logical view, deployment view, data view) are "
            "appended at Annexure-III. The architecture follows the GoI Cloud Reference "
            "Architecture v2.0 and complies with MeitY's Application Security Guidelines.",
            s["body"]),
    ]


def page_tech_method(p: Persona) -> list:
    s = _styles()
    return [
        Paragraph("TECHNICAL APPROACH — METHODOLOGY & DELIVERY PLAN", s["h1"]),
        Paragraph(p.methodology, s["body"]),
        Spacer(1, 8),
        Paragraph(
            "Quality gates at every phase boundary include independent peer review, automated "
            "static analysis (Semgrep + SonarQube), and counterpart-led acceptance. A live RAID "
            "log (Risks, Assumptions, Issues, Dependencies) is maintained throughout.",
            s["body"]),
    ]


def page_team(p: Persona) -> list:
    s = _styles()
    flow = [
        Paragraph("TEAM & KEY PERSONNEL", s["h1"]),
        _kv("Proposed team strength:", f"{p.team_strength} on-roll engineers + project managers"),
        _kv("PMP-certified project leads:", f"{p.pmp_certified_leads}"),
        _kv("Solution architects on the project:", "2" if p.team_strength >= 8 else "1"),
        Spacer(1, 10),
    ]
    if p.team_strength >= 8 and p.pmp_certified_leads >= 3:
        flow.append(Paragraph(
            "Detailed CVs (signed and dated within the last 60 days) are appended at "
            "Annexure-V. Every key person carries a non-poach undertaking for the duration of "
            "the engagement plus the warranty period.", s["body"]))
    else:
        flow.append(Paragraph(
            "CVs of the proposed core team are appended. Additional resources, including "
            "PMP-certified leads, will be on-boarded immediately after the award.", s["body"]))
    return flow


def page_mii(p: Persona) -> list:
    s = _styles()
    flow = _gov_header(
        "DEPARTMENT FOR PROMOTION OF INDUSTRY AND INTERNAL TRADE (DPIIT)",
        "PPP-MII Order (P-45021/2/2017-PP) — Self-Certification by Bidder",
    )
    if p.mii_class == "I":
        flow.append(Paragraph(
            f"We, <b>{p.org_name}</b>, hereby self-certify that the local content in the "
            f"offered solution is <b>{p.mii_local_content_pct}%</b>, which qualifies us as a "
            f"<b>Class-I Local Supplier</b> under the said Order (Class-I requires ≥ 50% local "
            f"content). The detailed local-content computation, certified by our Statutory "
            f"Auditor, is enclosed at Annexure-VII.",
            s["body"]))
    else:
        flow.append(Paragraph(
            f"We, <b>{p.org_name}</b>, self-certify that the local content in the offered "
            f"solution is <b>{p.mii_local_content_pct}%</b>, which qualifies us as a "
            f"<b>Class-II Local Supplier</b> (Class-II is 20–50% local content). We acknowledge "
            f"that this tender restricts the procurement to Class-I local suppliers.",
            s["warn"]))
    flow.append(Spacer(1, 10))
    flow.append(Paragraph(
        "Penalty clause: We understand that any false self-certification is liable to "
        "punitive action including debarment as per the said Order.", s["small"]))
    flow.extend(_sig_block(p.contact_name, "Director"))
    return flow


def page_integrity(p: Persona) -> list:
    s = _styles()
    flow = _gov_header(
        "CENTRAL VIGILANCE COMMISSION",
        "Integrity Pact — between the Procuring Entity and the Bidder",
    )
    flow.append(Paragraph("PREAMBLE", s["h3"]))
    flow.append(Paragraph(
        "This Integrity Pact is entered into between (a) the Procuring Entity (Principal) — "
        "Ministry of Electronics & IT, Government of India — and (b) the Bidder/Contractor "
        f"<b>{p.org_name}</b>, with the objective of preventing corruption in the procurement "
        "process and ensuring that the Principal awards the contract to a competent bidder "
        "offering the most competitive price.", s["body"]))
    flow.append(Paragraph("COMMITMENTS OF THE BIDDER", s["h3"]))
    flow.append(Paragraph(
        "(1) The Bidder will not, directly or through any other person or firm, offer, "
        "promise or give to any of the Principal's employees involved in the tender process or "
        "the execution of the contract any material or immaterial benefit. "
        "(2) The Bidder will not enter with any other bidder into any undisclosed agreement or "
        "understanding, whether formal or informal, that may result in suppression of "
        "competition (so-called 'cartel'). "
        "(3) The Bidder will not commit any offence under the Prevention of Corruption Act, "
        "1988, the Indian Penal Code, or the Income-Tax Act, 1961, in relation to this tender. "
        "(4) The Bidder will not knowingly furnish any false documents.", s["body"]))
    flow.append(Paragraph("CONSEQUENCES OF VIOLATION", s["h3"]))
    flow.append(Paragraph(
        "If the Bidder commits any of the above transgressions, the Principal shall be "
        "entitled to (a) exclude the Bidder from the tender process, (b) terminate the contract "
        "if already awarded, (c) forfeit the EMD/PBG, and (d) debar the Bidder from "
        "participation in future tenders for a period of up to three years.",
        s["body"]))
    if p.integrity_pact_signed:
        flow.append(Spacer(1, 10))
        flow.extend(_sig_block(p.contact_name, "Director"))
        flow.append(_kv("Witness:", "K. R. Sundaram, Company Secretary"))
    else:
        flow.append(Spacer(1, 10))
        flow.append(Paragraph("Integrity Pact: [TO BE FURNISHED]", s["warn"]))
    return flow


def page_emd(p: Persona) -> list:
    s = _styles()
    flow = _cert_banner(
        "EARNEST MONEY DEPOSIT (EMD) — BANK PAYMENT CONFIRMATION",
        "Online RTGS / NEFT Receipt extracted from the Bidder's banking portal",
    )
    flow.append(_kv("EMD amount required by tender:", "₹8,50,000 (₹ Eight lakh fifty thousand only)"))
    flow.append(_kv("Mode of remittance:", "Online RTGS"))
    flow.append(_kv("Amount remitted:", "₹8,50,000"))
    flow.append(_kv("UTR / transaction reference:", p.emd_utr))
    flow.append(_kv("Remitter (Sender) name:", p.org_name))
    flow.append(_kv("Remitter bank & branch:", p.emd_bank))
    flow.append(_kv("Beneficiary:", "Pay & Accounts Officer, MeitY"))
    flow.append(_kv("Beneficiary IFSC:", "RBIS0MBPA01 (RBI — Mumbai)"))
    flow.append(_kv("Beneficiary A/c No.:", "10082600114782"))
    flow.append(_kv("Date of remittance:", "26-May-2026"))
    flow.append(_kv("Status:", "SUCCESS — Credited to beneficiary"))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        "The bank-issued payment confirmation print-out (system-stamped, with the UTR above) is "
        "enclosed with this bid as an attested true copy.", s["body"]))
    return flow


def page_oem(p: Persona, oem_name: str, oem_role: str, signatory: str, signatory_role: str,
             oem_letter_no: str, oem_date: str) -> list:
    s = _styles()
    flow = _cert_banner(
        f"MANUFACTURER'S AUTHORISATION FORM (MAF) — {oem_name}",
        f"Issued in favour of the Bidder for {oem_role} supplied under this tender",
    )
    if not p.oem_present:
        flow.append(Paragraph(
            f"Manufacturer's Authorisation from {oem_name}: NOT ENCLOSED with this bid. The "
            f"required MAF has not been obtained from {oem_name} as on the bid-submission "
            f"date. This is a known omission against the tender's compliance checklist.",
            s["warn"]))
        return flow
    flow.append(_kv("OEM letter reference:", oem_letter_no))
    flow.append(_kv("OEM letter date:", oem_date))
    flow.append(_kv("OEM:", f"{oem_name} (India) Pvt Ltd"))
    flow.append(_kv("Authorised in favour of:", p.org_name))
    flow.append(_kv("Tender reference:", "CPPP/SI/NEPAP-B/2026-27/001"))
    flow.append(Spacer(1, 10))
    flow.append(Paragraph(
        f"<i>To,<br/>"
        f"The Procurement Officer,<br/>"
        f"Ministry of Electronics & IT, Government of India.<br/><br/>"
        f"Subject: Authorisation of <b>{p.org_name}</b> as our Channel Partner for the "
        f"captioned tender.<br/><br/>"
        f"Dear Sir/Madam,<br/><br/>"
        f"We, <b>{oem_name} (India) Pvt Ltd</b>, the original manufacturer of {oem_role} "
        f"covered under the offered solution, hereby authorise <b>{p.org_name}</b> to quote, "
        f"supply, install, commission and provide post-warranty maintenance for our products "
        f"under the captioned tender of the Ministry of Electronics & IT. We further confirm "
        f"that we shall provide all back-to-back technical and warranty support to {p.org_name} "
        f"during the contract period of the captioned tender, including any extensions thereof. "
        f"This authorisation is exclusive in respect of this tender and is non-transferable.<br/><br/>"
        f"Yours faithfully,<br/>"
        f"For <b>{oem_name} (India) Pvt Ltd</b><br/>"
        f"(Sd/-) <b>{signatory}</b>, {signatory_role}</i>", s["body"]))
    return flow


def page_bis(p: Persona) -> list:
    s = _styles()
    if not p.bis_iso_present or not p.bis_licence_no:
        flow = _cert_banner(
            "BIS / ISI LICENCE — NOT APPLICABLE",
            "The firm does not presently hold the BIS / ISI licence required by this tender.",
        )
        flow.append(Paragraph(
            "BIS Standard Mark Licence: NOT ENCLOSED. The firm acknowledges that this is a "
            "known deficiency against the tender compliance checklist.",
            s["warn"]))
        return flow
    flow = _gov_header(
        "BUREAU OF INDIAN STANDARDS (BIS) — MINISTRY OF CONSUMER AFFAIRS",
        "Standard Mark Licence — Particulars of Licensed Firm",
    )
    flow.append(_kv("Licence No.:", p.bis_licence_no))
    flow.append(_kv("Indian Standard:", "IS 15700:2018 — Quality Management Systems "
                                        "— Requirements for Service Quality"))
    flow.append(_kv("Licensee:", p.org_name))
    flow.append(_kv("Address of licensed unit:", p.registered_office))
    flow.append(_kv("Date of grant:", "08-Feb-2023"))
    flow.append(_kv("Date of expiry:", "07-Feb-2027"))
    flow.append(_kv("Issuing Branch Office:", "BIS Western Regional Office, Mumbai"))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        "The Standard Mark Licence remains valid subject to the licensee continuing to comply "
        "with the conditions of grant, including periodic conformity audits by BIS officers and "
        "satisfactory test results on samples drawn during audits.", s["body"]))
    return flow


def page_non_blacklisting(p: Persona) -> list:
    s = _styles()
    flow = _cert_banner(
        "AFFIDAVIT — NON-BLACKLISTING / NON-DEBARMENT",
        "Sworn on Rs. 100 Non-Judicial Stamp Paper and notarised",
    )
    flow.append(Paragraph(
        f"I, <b>{p.contact_name}</b>, son/daughter of Shri/Smt. R. {p.contact_name.split()[-1]}, "
        f"aged 47 years, resident of {p.registered_office.split(',')[-2].strip()}, do hereby "
        f"solemnly affirm and declare on oath as under:", s["body"]))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        f"1. I am the duly authorised signatory and Director of <b>{p.org_name}</b>, a company "
        f"incorporated under the Companies Act with CIN <b>{p.cin}</b>, and am competent to "
        f"depose this affidavit on its behalf.", s["body"]))
    flow.append(Paragraph(
        "2. The firm has NOT been blacklisted, debarred, banned or declared ineligible from "
        "participating in any tender process by any procuring entity of the Central Government, "
        "any State Government, any Public Sector Undertaking, the World Bank, the Asian "
        "Development Bank or any other multilateral funding agency, as on the date of bid "
        "submission.", s["body"]))
    flow.append(Paragraph(
        "3. No criminal case is pending against the firm or any of its directors before any "
        "court of competent jurisdiction in connection with any procurement contract.",
        s["body"]))
    flow.append(Paragraph(
        "4. The firm has not been declared insolvent, has not entered into a scheme of "
        "compromise or arrangement with its creditors, and is not undergoing corporate "
        "insolvency-resolution proceedings under the Insolvency and Bankruptcy Code, 2016.",
        s["body"]))
    flow.append(Paragraph(
        "5. I am aware that any wilful suppression of facts in this affidavit shall constitute "
        "perjury under the Indian Penal Code and shall additionally render the firm liable to "
        "debarment from the captioned tender and future procurements.", s["body"]))
    flow.append(Spacer(1, 10))
    flow.append(Paragraph(
        "<b>DEPONENT</b><br/>"
        f"(Sd/-) {p.contact_name}<br/>"
        f"Director, {p.org_name}", s["body"]))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "<b>VERIFICATION</b><br/>"
        "Verified at Pune on this 27th day of May, 2026, that the contents of paragraphs 1 to 5 "
        "above are true and correct to the best of my knowledge and belief, and nothing "
        "material has been concealed therefrom.", s["body"]))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "Identified before me — (Sd/-) <b>Shri. P. K. Joshi</b>, Notary, Pune — "
        "Regn. No. 1142/2018 — seal affixed.", s["muted"]))
    return flow


def page_poa(p: Persona) -> list:
    s = _styles()
    flow = _cert_banner(
        "POWER OF ATTORNEY FOR AUTHORISED SIGNATORY",
        "Executed by the Board of Directors of the Bidder",
    )
    flow.append(Paragraph(
        f"By a resolution duly passed at a meeting of the Board of Directors of <b>{p.org_name}</b> "
        f"held on 14-May-2026, the Board has nominated and constituted <b>{p.contact_name}</b>, "
        f"Director, as the Authorised Signatory of the Company for the purposes of submitting, "
        f"signing and executing the bid (and any consequent agreement) in response to the "
        f"captioned tender of the Ministry of Electronics & IT, Government of India.",
        s["body"]))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "The Authorised Signatory is empowered to: (i) sign, attest and submit the bid and all "
        "annexures thereto; (ii) negotiate and execute the contract upon award; (iii) sign "
        "performance guarantees, indemnities and the Integrity Pact; and (iv) attend pre-bid "
        "meetings and any post-bid clarifications on behalf of the Company.", s["body"]))
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(
        "<b>For and on behalf of the Board of Directors of " + p.org_name + "</b><br/>"
        "(Sd/-) <b>Smt. Ranjana Iyer</b>, Chairperson<br/>"
        f"(Sd/-) <b>K. R. Sundaram</b>, Company Secretary — M.No. F-7811", s["body"]))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        "Witnessed and notarised on this 14th day of May, 2026, at Pune. Notary Seal & "
        "Regn. No. 1142/2018 affixed in original.", s["muted"]))
    return flow


def page_declarations(p: Persona) -> list:
    s = _styles()
    flow = [
        Paragraph("DECLARATIONS & AUTHORISED SIGNATURE", s["h1"]),
        Paragraph(
            "We solemnly declare that (a) the information furnished in this bid is true and "
            "correct to the best of our knowledge, (b) we have not been debarred or blacklisted "
            "by any procuring entity of the Government of India or any State Government as on "
            "the date of bid submission, (c) we accept the terms and conditions of the tender "
            "in their entirety, and (d) the prices quoted in our financial bid are inclusive "
            "of all taxes, duties and levies.", s["body"]),
        Spacer(1, 24),
        _kv("For and on behalf of:", p.org_name),
        _kv("Name & Designation:", f"{p.contact_name}, Director"),
        _kv("Place / Date:", "Pune / 27-May-2026"),
        Spacer(1, 24),
        Paragraph("[Signature & company seal]", s["muted"]),
        Spacer(1, 18),
        Paragraph(f"— end of {p.slug}_technical.pdf —", s["muted"]),
    ]
    return flow


# ---------------------------------------------------------------------------
# Per-persona technical & financial PDF assembly.
# ---------------------------------------------------------------------------
def build_technical(p: Persona) -> list:
    pages: list[list] = [
        page_cover(p),
        page_index(),
        page_profile(p),
        page_gstin(p),
        page_pan_itr(p),
        page_turnover(p),
        page_past_project(p, 0),
        page_past_project(p, 1) if len(p.past_projects) > 1 else page_past_project(p, 0),
        page_past_project(p, 2) if len(p.past_projects) > 2 else page_past_project(p, 0),
        page_iso_9001(p),
        page_iso_27001(p),
        page_cmmi(p),
        page_tech_arch(p),
        page_tech_method(p),
        page_team(p),
        page_mii(p),
        page_integrity(p),
        page_emd(p),
        page_oem(p, "Dell Technologies", "servers, storage and converged infrastructure",
                 "V. Krishnan", "Director — Public Sector Channel",
                 "DTI/CH/MAF/2026-27/001142", "24-May-2026"),
        page_oem(p, "Cisco Systems", "network, security and collaboration equipment",
                 "A. Iyer", "Partner Account Manager — Public Sector",
                 "CSI/PSA/MAF/2026-27/000881", "22-May-2026"),
        page_oem(p, "Microsoft", "operating-system and database platform licences",
                 "S. Bhatia", "Public Sector Sales Lead",
                 "MSI/PS/MAF/26-27/0227", "25-May-2026"),
        page_bis(p),
        page_non_blacklisting(p),
        page_poa(p),
        page_declarations(p),
    ]
    flow: list = []
    for i, pg in enumerate(pages):
        flow.extend(pg)
        if i != len(pages) - 1:
            flow.append(PageBreak())
    return flow


def build_financial(p: Persona) -> list:
    s = _styles()
    flow: list = [
        Paragraph("BID DOCUMENT — FINANCIAL PROPOSAL", s["h1"]),
        Paragraph(
            "Selection of System Integrator — National e-Procurement Analytics Platform "
            "(Package B)", s["h2"]),
        Spacer(1, 10),
        _kv("Tender Reference:", "CPPP/SI/NEPAP-B/2026-27/001"),
        _kv("Bidder:", p.org_name),
        _kv("Submission Date:", "27-May-2026"),
        Spacer(1, 12),
        Paragraph(
            "The financial bid is quoted in the prescribed Item-wise Bill of Quantities (BoQ) "
            "format. All amounts are inclusive of GST, customs duties, freight, installation, "
            "commissioning, training and three years of warranty support.", s["body"]),
        PageBreak(),
        Paragraph("ITEM-WISE BoQ", s["h1"]),
    ]
    boq = [
        ("Hardware (servers, storage, network)", 0.32),
        ("Software licences (OS, DB, middleware)", 0.18),
        ("Implementation services (build + UAT)", 0.28),
        ("Pilot, cutover & training", 0.07),
        ("Post-go-live support — 3 years", 0.15),
    ]
    rows = [["#", "Item", "Indicative share", "Amount (₹)"]]
    running = 0
    for i, (item, share) in enumerate(boq, start=1):
        amt = int(round(p.quoted_total_inr * share / 10000.0)) * 10000
        running += amt
        rows.append([str(i), item, f"{int(share * 100)}%", _inr(amt)])
    diff = p.quoted_total_inr - running
    rows[-1][-1] = _inr(int(rows[-1][-1].replace("₹", "").replace(",", "")) + diff)
    rows.append(["", "Total (all-inclusive)", "100%", _inr(p.quoted_total_inr)])
    t = Table(rows, colWidths=[1.0 * cm, 7.6 * cm, 3.0 * cm, 4.6 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_R),
        ("FONTNAME", (0, 0), (-1, 0), FONT_B),
        ("FONTNAME", (0, -1), (-1, -1), FONT_B),
        ("BACKGROUND", (0, 0), (-1, 0), PAPER_DK),
        ("BACKGROUND", (0, -1), (-1, -1), PAPER),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE_LT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(t)
    flow.append(PageBreak())
    flow += [
        Paragraph("PRICED SUMMARY", s["h1"]),
        _kv("Tender estimated value:", f"{_inr(85_000_000)} (₹8.5 crore)"),
        _kv("Our quoted total (all-inclusive):", _inr(p.quoted_total_inr)),
        _kv("As a percentage of estimate:", f"{p.pct_of_estimate}%"),
        Spacer(1, 14),
        Paragraph(f"<b>Grand Total: {_inr(p.quoted_total_inr)}</b> (Rupees, all-inclusive).",
                  s["body"]),
        Spacer(1, 14),
    ]
    if p.pct_of_estimate < 70:
        flow.append(Paragraph(
            "Our quotation is significantly below the tender estimate. We confirm that the "
            "rates are sustainable and based on aggressive but achievable resource pricing.",
            s["body"]))
    flow += [
        Spacer(1, 20),
        _kv("For and on behalf of:", p.org_name),
        _kv("Authorised signatory:", f"{p.contact_name}, Director"),
        _kv("Place / Date:", "Pune / 27-May-2026"),
        Spacer(1, 18),
        Paragraph(f"— end of {p.slug}_financial.pdf —", s["muted"]),
    ]
    return flow


def render(out_path: Path, flowables: Callable[[], list]) -> None:
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title=out_path.stem.replace("_", " ").title(),
        author="TenderIQ synthetic-bid generator",
    )
    doc.build(flowables())


def main():
    for p in PERSONAS:
        tech_path = OUT / f"{p.slug}_technical.pdf"
        fin_path = OUT / f"{p.slug}_financial.pdf"
        render(tech_path, lambda p=p: build_technical(p))
        render(fin_path, lambda p=p: build_financial(p))
        print(f"  - {p.org_name:36} -> {tech_path.name} + {fin_path.name}")
    print(f"\nWrote {len(PERSONAS) * 2} PDFs to {OUT}")


if __name__ == "__main__":
    main()
