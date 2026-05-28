"""Generate a realistic synthetic CPPP-style IT-services tender PDF for testing.

  uv run python fixtures/make_sample_tender.py

Writes fixtures/sample_tender.pdf (~12 pages) with quotable text for every field
the Tender Parser extracts. Replace with real eprocure.gov.in PDFs via the UI.
"""

from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

OUT = Path(__file__).resolve().parent / "sample_tender.pdf"

styles = getSampleStyleSheet()
H = ParagraphStyle("H", parent=styles["Heading1"], fontSize=14, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceAfter=8)
P = ParagraphStyle("P", parent=styles["BodyText"], fontSize=10, leading=15, spaceAfter=6)
CENTER = ParagraphStyle("C", parent=P, alignment=TA_CENTER)


def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, topMargin=20 * mm, bottomMargin=18 * mm)
    e = []

    # Page 1 — cover
    e += [
        Paragraph("MINISTRY OF ELECTRONICS AND INFORMATION TECHNOLOGY", CENTER),
        Paragraph("National Informatics Centre (NIC)", CENTER),
        Spacer(1, 8 * mm),
        Paragraph("REQUEST FOR PROPOSAL (RFP)", CENTER),
        Paragraph(
            "Selection of System Integrator for Design, Development and Maintenance "
            "of a National e-Procurement Analytics Platform",
            H,
        ),
        Spacer(1, 6 * mm),
        Paragraph("Tender Reference No.: NIC/MeitY/2026/RFP/IT-SVCS/0417", P),
        Paragraph("Mode of Tender: e-Procurement (CPPP, eprocure.gov.in)", P),
        Paragraph("Estimated Cost of Procurement: Rs. 8,50,00,000 (Rupees Eight Crore Fifty Lakh only).", P),
        Paragraph("Earnest Money Deposit (EMD): Rs. 8,50,000 (Rupees Eight Lakh Fifty Thousand only).", P),
        PageBreak(),
    ]

    # Page 2 — critical dates
    e += [
        Paragraph("1. Critical Dates", H2),
        Paragraph("Date of publication of RFP: 12.05.2026.", P),
        Paragraph("Pre-bid meeting: 22.05.2026 at 1100 hours.", P),
        Paragraph(
            "Last date and time for submission of bids (Submission Deadline): "
            "26.06.2026 up to 1500 hours (IST).",
            P,
        ),
        Paragraph("Technical bid opening: 27.06.2026 at 1530 hours.", P),
        PageBreak(),
    ]

    # Page 3-4 — eligibility
    e += [
        Paragraph("2. Eligibility Criteria (Pre-Qualification)", H2),
        Paragraph(
            "2.1 The bidder must be a company registered in India under the Companies Act, "
            "1956/2013 and in continuous operation for at least five (5) years as on the bid "
            "submission date.",
            P,
        ),
        Paragraph(
            "2.2 The bidder must have an average annual turnover of at least Rs. 25,00,00,000 "
            "(Rupees Twenty Five Crore) in each of the last three financial years.",
            P,
        ),
        Paragraph(
            "2.3 The bidder must be CMMI Level 5 appraised and ISO/IEC 27001:2013 certified as "
            "on the date of bid submission.",
            P,
        ),
        Paragraph(
            "2.4 The bidder must have successfully executed at least two (2) similar software "
            "development projects each of value not less than Rs. 3,00,00,000 for a Central/State "
            "Government department in the last five years.",
            P,
        ),
        PageBreak(),
        Paragraph(
            "2.5 The bidder must not have been blacklisted by any Central/State Government or PSU "
            "as on the bid submission date, and must submit a self-declaration to this effect.",
            P,
        ),
        PageBreak(),
    ]

    # Page 5-6 — evaluation method + technical matrix
    e += [
        Paragraph("3. Method of Evaluation", H2),
        Paragraph(
            "3.1 The selection shall be made under the Quality and Cost Based Selection (QCBS) "
            "method. The combined score shall be computed assigning a weight of 70% to the "
            "Technical score and 30% to the Financial score.",
            P,
        ),
        Paragraph("4. Technical Evaluation Criteria", H2),
        Table(
            [
                ["Criterion", "Max Marks"],
                ["Relevant project experience (Govt e-Gov / analytics)", "30"],
                ["Proposed solution architecture & approach", "25"],
                ["Key personnel qualifications & CVs", "25"],
                ["Demonstrated capability (presentation/PoC)", "20"],
            ],
            colWidths=[110 * mm, 30 * mm],
            style=TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]
            ),
        ),
        Paragraph(
            "The minimum technical qualifying score is 70 marks out of 100. Bidders scoring below "
            "70 shall not be considered for financial evaluation.",
            P,
        ),
        PageBreak(),
    ]

    # Page 7 — financial format
    e += [
        Paragraph("5. Financial Bid Format", H2),
        Paragraph(
            "5.1 The financial bid shall be submitted strictly in the prescribed BoQ "
            "(Bill of Quantities) template available on the CPPP portal. Bidders shall quote a "
            "single all-inclusive lump-sum price inclusive of all taxes except GST, which shall "
            "be shown separately.",
            P,
        ),
        Paragraph(
            "5.2 Prices must be quoted in Indian Rupees (INR) only. Conditional or partial bids "
            "shall be summarily rejected.",
            P,
        ),
        PageBreak(),
    ]

    # Page 8-9 — EMD, PBG, integrity pact, MII
    e += [
        Paragraph("6. General Conditions of Contract", H2),
        Paragraph(
            "6.1 Performance Bank Guarantee: The successful bidder shall furnish a Performance "
            "Bank Guarantee equal to 10% of the total contract value, valid for the entire "
            "contract period plus sixty (60) days.",
            P,
        ),
        Paragraph(
            "6.2 Integrity Pact: The bidder is required to sign an Integrity Pact, as per the "
            "Central Vigilance Commission guidelines, along with the technical bid. Bids "
            "received without a duly signed Integrity Pact shall be rejected.",
            P,
        ),
        PageBreak(),
        Paragraph(
            "6.3 Public Procurement (Preference to Make in India): This procurement is subject to "
            "the PPP-MII Order, 2017 (as amended). Only Class-I Local Suppliers, having a minimum "
            "local content of 50%, are eligible to participate in this tender.",
            P,
        ),
        Paragraph(
            "6.4 The bidder shall submit a certificate regarding the percentage of local content "
            "in the format prescribed under the said Order.",
            P,
        ),
        PageBreak(),
    ]

    # Page 10-12 — filler clauses
    for i in range(3):
        e += [
            Paragraph(f"7.{i + 1} Miscellaneous Conditions", H2),
            Paragraph(
                "The purchaser reserves the right to accept or reject any or all bids without "
                "assigning any reason. Any dispute shall be subject to the jurisdiction of courts "
                "at New Delhi. The bidder shall comply with all applicable laws and the General "
                "Financial Rules, 2017.",
                P,
            ),
            Spacer(1, 4 * mm),
            Paragraph(
                "All notices and corrigenda shall be published only on the CPPP portal "
                "(eprocure.gov.in). Bidders are advised to check the portal regularly.",
                P,
            ),
            PageBreak(),
        ]

    doc.build(e)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
