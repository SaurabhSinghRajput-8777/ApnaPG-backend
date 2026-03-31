"""
PDF Generation Service — Digital Rental Agreement.

Uses ReportLab to generate a professional, structured rental
agreement PDF in memory. The PDF includes property details,
owner/tenant information, house rules, and signature lines.
"""

from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


# ── Style definitions ───────────────────────────────────────────

def _get_styles() -> dict[str, ParagraphStyle]:
    """Build custom paragraph styles for the lease document."""
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "LeaseTitle",
            parent=base["Title"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=4 * mm,
            alignment=1,  # center
        ),
        "subtitle": ParagraphStyle(
            "LeaseSubtitle",
            parent=base["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#555555"),
            spaceAfter=8 * mm,
            alignment=1,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#16213e"),
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
            borderPadding=(0, 0, 2, 0),
        ),
        "body": ParagraphStyle(
            "LeaseBody",
            parent=base["Normal"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#333333"),
        ),
        "body_bold": ParagraphStyle(
            "LeaseBodyBold",
            parent=base["Normal"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#1a1a2e"),
            fontName="Helvetica-Bold",
        ),
        "footer": ParagraphStyle(
            "LeaseFooter",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#999999"),
            alignment=1,
        ),
    }


# ── Helper builders ─────────────────────────────────────────────

def _build_details_table(
    data: list[tuple[str, str]],
) -> Table:
    """Build a two-column key-value table for details sections."""
    table_data = [[k, v] for k, v in data]
    table = Table(table_data, colWidths=[5.5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#333333")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e0e0e0")),
    ]))
    return table


def _build_house_rules_table(rules: dict[str, Any]) -> Table:
    """Build a styled table from house_rules JSONB data."""
    if not rules:
        return Table([["No house rules specified."]], colWidths=[16.5 * cm])

    table_data = [["Rule", "Details"]]
    for key, value in rules.items():
        # Pretty-format the key
        pretty_key = key.replace("_", " ").title()
        # Handle different value types
        if isinstance(value, bool):
            display_val = "Yes" if value else "No"
        elif isinstance(value, list):
            display_val = ", ".join(str(v) for v in value)
        else:
            display_val = str(value)
        table_data.append([pretty_key, display_val])

    table = Table(table_data, colWidths=[5.5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        # Body rows
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#333333")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, colors.HexColor("#e0e0e0")),
        # Grid
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#16213e")),
    ]))
    return table


def _build_signature_block(styles: dict) -> list:
    """Build the signature lines at the bottom of the agreement."""
    elements = []

    sig_data = [
        ["", ""],
        ["_" * 35, "_" * 35],
        ["Owner Signature", "Tenant Signature"],
        ["", ""],
        ["Date: _______________", "Date: _______________"],
    ]

    sig_table = Table(sig_data, colWidths=[8.25 * cm, 8.25 * cm])
    sig_table.setStyle(TableStyle([
        ("ALIGNMENT", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#333333")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(sig_table)
    return elements


# ── Main generator ──────────────────────────────────────────────

def generate_lease_pdf(
    tenant_data: dict[str, Any],
    owner_data: dict[str, Any],
    property_data: dict[str, Any],
) -> io.BytesIO:
    """
    Generate a Digital Rental Agreement PDF in memory.

    Args:
        tenant_data: {full_name, email, phone_number}
        owner_data:  {full_name, email, phone_number}
        property_data: {title, locality, monthly_rent, occupancy_type,
                        house_rules, tenancy_start_date, ...}

    Returns:
        BytesIO buffer containing the rendered PDF.
    """
    buffer = io.BytesIO()
    styles = _get_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Digital Rental Agreement - ApnaPG",
        author="ApnaPG Platform",
    )

    elements: list = []

    # ── Title ───────────────────────────────────────────────────
    elements.append(Paragraph("Digital Rental Agreement", styles["title"]))
    elements.append(Paragraph(
        f"Generated on {date.today().strftime('%B %d, %Y')} via ApnaPG Platform",
        styles["subtitle"],
    ))
    elements.append(HRFlowable(
        width="100%", thickness=1.5,
        color=colors.HexColor("#16213e"),
        spaceAfter=6 * mm,
    ))

    # ── Property Details ────────────────────────────────────────
    elements.append(Paragraph("Property Details", styles["section_heading"]))
    elements.append(_build_details_table([
        ("Property Title:", property_data.get("title", "N/A")),
        ("Locality:", property_data.get("locality", "N/A")),
        ("Monthly Rent:", f"₹{property_data.get('monthly_rent', 0):,}"),
        ("Occupancy Type:", property_data.get("occupancy_type", "N/A").title()),
        ("Tenancy Start:", str(property_data.get("tenancy_start_date", "To be decided"))),
    ]))
    elements.append(Spacer(1, 4 * mm))

    # ── Owner Details ───────────────────────────────────────────
    elements.append(Paragraph("Owner Details", styles["section_heading"]))
    elements.append(_build_details_table([
        ("Full Name:", owner_data.get("full_name", "N/A")),
        ("Email:", owner_data.get("email", "N/A")),
        ("Phone:", owner_data.get("phone_number", "N/A") or "Not provided"),
    ]))
    elements.append(Spacer(1, 4 * mm))

    # ── Tenant Details ──────────────────────────────────────────
    elements.append(Paragraph("Tenant Details", styles["section_heading"]))
    elements.append(_build_details_table([
        ("Full Name:", tenant_data.get("full_name", "N/A")),
        ("Email:", tenant_data.get("email", "N/A")),
        ("Phone:", tenant_data.get("phone_number", "N/A") or "Not provided"),
    ]))
    elements.append(Spacer(1, 4 * mm))

    # ── House Rules ─────────────────────────────────────────────
    elements.append(Paragraph("House Rules", styles["section_heading"]))
    house_rules = property_data.get("house_rules") or {}
    elements.append(_build_house_rules_table(house_rules))
    elements.append(Spacer(1, 4 * mm))

    # ── Terms & Conditions ──────────────────────────────────────
    elements.append(Paragraph("Terms &amp; Conditions", styles["section_heading"]))
    terms = [
        "1. This agreement is generated digitally via the ApnaPG platform and "
        "serves as a record of the mutual understanding between the Owner and Tenant.",
        "2. Both parties agree to abide by the House Rules listed above for the "
        "duration of the tenancy.",
        "3. The monthly rent of <b>₹{:,}</b> is to be paid by the Tenant to the "
        "Owner on or before the 5th of each month.".format(
            property_data.get("monthly_rent", 0)
        ),
        "4. Either party may terminate this agreement with a minimum of 30 days "
        "written notice.",
        "5. Any disputes shall be resolved amicably. If unresolved, the matter "
        "may be reported to the ApnaPG platform for mediation.",
    ]
    for term in terms:
        elements.append(Paragraph(term, styles["body"]))
        elements.append(Spacer(1, 2 * mm))

    elements.append(Spacer(1, 8 * mm))

    # ── Signature Block ─────────────────────────────────────────
    elements.append(Paragraph("Signatures", styles["section_heading"]))
    elements.append(Paragraph(
        "Both parties acknowledge that they have read, understood, and agree "
        "to the terms of this rental agreement.",
        styles["body"],
    ))
    elements.append(Spacer(1, 6 * mm))
    elements.extend(_build_signature_block(styles))

    # ── Footer ──────────────────────────────────────────────────
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#cccccc"),
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    ))
    elements.append(Paragraph(
        "This document was auto-generated by the ApnaPG platform. "
        "It is intended for offline signing and record-keeping purposes.",
        styles["footer"],
    ))

    # ── Build PDF ───────────────────────────────────────────────
    doc.build(elements)
    buffer.seek(0)
    return buffer
