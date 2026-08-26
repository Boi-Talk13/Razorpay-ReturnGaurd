import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # We don't want headers and footers on the cover page (Page 1)
        if self._pageNumber == 1:
            # Draw decorative top bar on cover
            self.setFillColor(colors.HexColor("#0F172A")) # Dark slate
            self.rect(0, 770, 612, 22, fill=True, stroke=False)
            self.setFillColor(colors.HexColor("#6366F1")) # Indigo accent
            self.rect(0, 765, 612, 5, fill=True, stroke=False)
            self.restoreState()
            return

        # Header (Pages 2+)
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(54, 755, "RETURNGUARD PITCH GUIDE")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(558, 755, "Razorpay AI Buildathon 2026")
        
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 747, 558, 747)
        
        # Footer (Pages 2+)
        self.line(54, 55, 558, 55)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 40, "Confidential — For Presentation Demo Pitch Script Only")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        
        self.restoreState()

def create_script_pdf(output_path):
    # Set document margins to avoid headers/footers overlap
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#6366F1"),
        spaceAfter=30
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#475569")
    )
    
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=12
    )

    # Script table styles
    time_style = ParagraphStyle(
        'TableTime',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        alignment=1, # Center
        textColor=colors.HexColor("#0F172A")
    )
    
    show_style = ParagraphStyle(
        'TableShow',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1E293B")
    )
    
    say_style = ParagraphStyle(
        'TableSay',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )
    
    do_style = ParagraphStyle(
        'TableDo',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#475569")
    )
    
    th_style = ParagraphStyle(
        'TableHeaderText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []
    
    # ------------------ COVER PAGE ------------------
    story.append(Spacer(1, 40))
    story.append(Paragraph("🛡️ ReturnGuard — AI Risk Manager", title_style))
    story.append(Paragraph("Razorpay AI Buildathon — Track 02 (Presentation Demo Guide)", subtitle_style))
    
    story.append(Spacer(1, 10))
    intro_p = (
        "<b>ReturnGuard</b> is an intelligent return-risk scoring engine & dynamic checkout intervention "
        "system designed to eliminate RTO (Return to Origin) losses and return fraud for Indian merchants. "
        "This guide outlines the perfect workflow, visual cues, and word-for-word voiceover script "
        "for a <b>5-minute video pitch</b> for hackathon submissions."
    )
    story.append(Paragraph(intro_p, body_style))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Author</b>: Antigravity Developer Assistant<br/>"
                           "<b>Project Target</b>: Razorpay AI Buildathon Submission<br/>"
                           "<b>Local Server Url</b>: http://localhost:8000<br/>"
                           "<b>Documentation Reference</b>: README.md / app.py<br/>"
                           "<b>Created Date</b>: August 26, 2026", meta_style))
    story.append(Spacer(1, 30))
    
    quick_tips_text = (
        "<b>Tips for a Successful Video Demo:</b><br/>"
        "• <b>Keep it brisk</b>: Do not pause during transitions. Make your mouse clicks deliberate.<br/>"
        "• <b>Local Environment Check</b>: Ensure your local server is running on <code>http://localhost:8000</code> before recording.<br/>"
        "• <b>Clean Dashboard Data</b>: Clear any noisy transaction history using the 'Clear Ledger' button if you want a clean demo state.<br/>"
        "• <b>Preparation</b>: Open the dashboard, simulated mobile checkout, and terminal side-by-side or in clean tabs."
    )
    story.append(Paragraph(quick_tips_text, body_style))
    
    story.append(PageBreak())
    
    # ------------------ SCRIPT TABLE ------------------
    story.append(Paragraph("5-Minute Video Pitch Script Table", h1_style))
    story.append(Paragraph(
        "Follow the column segments sequentially. Make sure your actions in the web UI match the visual guide.",
        body_style
    ))
    
    # Build Table Content
    # Columns: Time (75), Show (100), Say (230), Do (99) -> Total 504
    
    headers = [
        Paragraph("<b>Time & Sec</b>", ParagraphStyle('H0', parent=th_style, alignment=1)),
        Paragraph("<b>What to Show</b>", ParagraphStyle('H1', parent=th_style, alignment=0)),
        Paragraph("<b>What to Say (Voiceover)</b>", ParagraphStyle('H2', parent=th_style, alignment=0)),
        Paragraph("<b>What to Do (Actions)</b>", ParagraphStyle('H3', parent=th_style, alignment=0))
    ]
    
    # Row data template: (Time, Show, Say, Do)
    script_data = [
        (
            "<b>0:00 - 0:45</b><br/><br/><b>1. Hook &<br/>RTO Problem</b>",
            "• Model Performance panel<br/>• Precision (40.0%) & Recall (38.9%) cards<br/>• SHAP Feature Importance list",
            "Hello, I am excited to present ReturnGuard, an intelligent return-risk scoring engine and dynamic checkout intervention system built for Razorpay merchants.<br/><br/>"
            "Here on our Model Performance & Economics panel, we see our classifier trained on ten thousand transactions. It achieves a 40.0% Precision—nearly four times higher than standard baseline RTO rates—a 38.9% Recall, and an AUC-ROC of 0.787.<br/><br/>"
            "Our feature importance attribution shows that customer account age at 18.9% and transaction amount at 18.2% are the primary indicators of return risk, followed by order velocity at 11.2%.",
            "• Hover over the Precision, Recall, and AUC-ROC cards.<br/>• Highlight the Confusion Matrix and point out Customer Age Days in the Feature Importance list.<br/>• Scroll down to the Threshold Tuner."
        ),
        (
            "<b>0:45 - 2:00</b><br/><br/><b>2. ML Engine &<br/>SHAP Reasons</b>",
            "• Transaction Scorer panel<br/>• 1-Click Presets<br/>• SHAP explainability chart & list",
            "ReturnGuard is powered by a Random Forest Classifier trained on 10,000 transaction records with realistic demographic, velocity, and payment markers. "
            "But raw scores aren't enough—merchants need to understand why an order is flagged.<br/><br/>"
            "By clicking our 'High-Risk COD Electronics' preset, the system evaluates the order. The risk gauge instantly turns red. Underneath, our SHAP explainer shows the exact risk drivers: "
            "the Tier-3 delivery pincode increases risk by 32%, and a new buyer status adds 16%, while customer loyalty reduces risk. "
            "Post-ML safety rules also apply—gating large purchases while keeping lower value purchases frictionless.",
            "• Go to the Scorer section.<br/>• Click the preset button for 'High-Risk COD Electronics'.<br/>• Point to the red gauge and read out the top SHAP factors."
        ),
        (
            "<b>2:00 - 3:15</b><br/><br/><b>3. Dynamic<br/>Checkout UX</b>",
            "• Mobile simulator mockup<br/>• Payment modal choices<br/>• UPI discount banner",
            "Instead of blanket blocks, we use Razorpay Checkout APIs to intervene dynamically. Let's see it in action in our simulator. "
            "For a low-risk buyer, all payment channels, including COD, remain active. "
            "If a buyer exhibits medium risk, COD is gated behind an SMS OTP verification. "
            "For high-risk buyers, COD is deactivated entirely. To salvage the sale, ReturnGuard injects an instant UPI discount—for example, 200 rupees off—incentivizing them to convert to a verified prepaid payment. "
            "This converts a risky COD order to a secure prepaid transaction, eliminating RTO risk completely.",
            "• Open the simulator widget.<br/>• Toggle risk presets to show the checkout page changing: COD active, gated, or disabled.<br/>• Click the prepaid option showing the UPI discount applied."
        ),
        (
            "<b>3:15 - 4:15</b><br/><br/><b>4. Tuner &<br/>AI Copilot</b>",
            "• Threshold Tuner & ROI Simulator panel<br/>• Cost tradeoff curves chart<br/>• ROI Calculator: RTO Prevented (+Rs. 10,70,025), Blocked (-Rs. 2,82,799), Net Savings (+Rs. 7,87,226)",
            "Every merchant has a different risk appetite. That’s why we built the interactive Threshold Tuner and Merchant ROI Simulator.<br/><br/>"
            "By adjusting our risk threshold cutoff slider—currently set to a balanced 0.50—we can see the tradeoff curves between Precision, Recall, and Costs. For a merchant processing 10,000 monthly orders at a Rs. 5,000 average order value, ReturnGuard prevents Rs. 10,70,025 in RTO losses, blocks only Rs. 2,82,799 in genuine orders, yielding Rs. 7,87,226 in net monthly savings directly to the merchant's bottom line!<br/><br/>"
            "Additionally, the AI Copilot compiles forensic briefs and generates ready-to-dispatch 1-click WhatsApp verification templates.",
            "• Hover over the risk cutoff slider at 0.50.<br/>• Highlight the cost curves on the line chart.<br/>• Highlight the RTO Prevented (+Rs. 10,70,025) and Net Monthly Savings (+Rs. 7,87,226) results on the ROI Calculator.<br/>• Click 'Copy Template' for WhatsApp."
        ),
        (
            "<b>4:15 - 5:00</b><br/><br/><b>5. Tech Stack &<br/>Summary</b>",
            "• Webhook simulator<br/>• API Docs section<br/>• Health check JSON in new tab",
            "From an engineering standpoint, ReturnGuard runs on a Flask API with a vanilla CSS dark-mode dashboard. All charts are lightweight, dynamic inline SVG drawings. "
            "We provide production-ready endpoints, including a live webhook listener with HMAC-SHA256 signature verification to intercept events directly from the Razorpay Dashboard. "
            "The app is containerized via Docker and fully deployable on Render or Railway.<br/><br/>"
            "ReturnGuard bridges ML explainability and checkout interventions to protect merchant profits. Thank you!",
            "• Trigger the Webhook Simulator button to fire a live simulated event.<br/>• Show the webhook event logged instantly in the audit list.<br/>• Show the '/api/health' JSON page in a tab."
        )
    ]
    
    table_data = [headers]
    for row in script_data:
        table_data.append([
            Paragraph(row[0], time_style),
            Paragraph(row[1], show_style),
            Paragraph(row[2], say_style),
            Paragraph(row[3], do_style)
        ])
    
    t = Table(table_data, colWidths=[75, 100, 230, 99])
    
    # Grid styling
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")), # Dark slate header
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]), # Alternate row coloring
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,1), (-1,-1), 10),
        ('BOTTOMPADDING', (0,1), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(t)
    
    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_pdf_path = os.path.join(base_dir, "..", "ReturnGuard_5Min_Pitch_Script.pdf")
    create_script_pdf(output_pdf_path)
    print(f"PDF Successfully generated at: {os.path.abspath(output_pdf_path)}")
