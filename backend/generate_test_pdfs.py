import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf(filename, title, sections):
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom Styles for Premium Report Look
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#4f46e5"),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        leading=14,
        spaceAfter=10
    )
    
    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 15))
    
    for section_title, content in sections:
        story.append(Paragraph(section_title, h2_style))
        if isinstance(content, str):
            story.append(Paragraph(content, body_style))
        elif isinstance(content, list):
            # Table formatting
            table_data = []
            for row in content:
                formatted_row = [Paragraph(str(cell), body_style) for cell in row]
                table_data.append(formatted_row)
            
            t = Table(table_data, colWidths=[150, 100, 100, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))
            
    doc.build(story)
    print(f"Generated PDF: {filename}")

if __name__ == "__main__":
    # Create the test_files directory in the root workspace
    os.makedirs("../test_files", exist_ok=True)
    
    # 1. Generate Clean Report
    clean_sections = [
        ("Executive Prepared Remarks", 
         "Microsoft Executive VP & CFO, Amy Hood: We are pleased to report strong performance. "
         "For the upcoming fiscal third quarter, we expect Q3 Revenue Guidance to be between $50.0B and $51.0B, driven by enterprise cloud renewals. "
         "We target an operating margin of 43.0% for the third quarter."),
        ("Q2 Historical Financials Table", [
            ["Financial Metric", "Q2 Actuals", "Q1 Actuals", "Q2 YoY Change"],
            ["Revenue", "$49.5B", "$48.0B", "+8.5%"],
            ["Net Income", "$15.4B", "$14.8B", "+6.0%"],
            ["Operating Margin", "42.5%", "42.0%", "+0.5%"]
        ]),
        ("Q&A Session Summary", 
         "Analyst: Can you expand on cloud growth expectations? "
         "Amy Hood: Cloud revenue continues to accelerate. We anticipate Microsoft Cloud revenue to hit $25.0B in Q3, representing 50% of our guided mid-point revenue of $50.5B.")
    ]
    generate_pdf("../test_files/microsoft_fy26_clean.pdf", "Microsoft Corp. Q2 FY26 Earnings Call Transcript", clean_sections)
    
    # 2. Generate Contradictory Report
    contradiction_sections = [
        ("Executive Prepared Remarks Summary", 
         "ACME Corp CEO, John Doe: We delivered solid momentum. "
         "Looking forward, we are establishing our Q3 Revenue Guidance at a range of $500M to $550M. "
         "We estimate our two operating segments will drive this: Product segment revenue is guided to reach $300M, and Services segment is guided to reach $120M. "
         "Additionally, we expect Q3 Net Income of $80M, which represents an operating margin target of 25% on the guided mid-point revenue of $525M."),
        ("Q2 Historical Financials Table", [
            ["Financial Segment", "Q2 Actuals", "Q1 Actuals", "Q2 YoY Change"],
            ["Product Revenue", "$290M", "$280M", "+3.4%"],
            ["Services Revenue", "$115M", "$110M", "+4.3%"],
            ["Total Revenue", "$405M", "$390M", "+3.7%"]
        ]),
        ("Operating Expense Outlook Notes",
         "CFO Jane Smith: In Q3, we project operating expenses of $450M to support product expansions. Our Q3 Net income guidance of $80M is sound.")
    ]
    generate_pdf("../test_files/acme_q3_contradiction.pdf", "ACME Corp. Q3 FY26 Earnings Call Transcript", contradiction_sections)
