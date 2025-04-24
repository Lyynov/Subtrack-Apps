from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime, date
import calendar
import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)

def create_title(title, styles):
    """Create a title paragraph"""
    return Paragraph(title, styles["Title"])

def create_heading(heading, styles):
    """Create a heading paragraph"""
    return Paragraph(heading, styles["Heading1"])

def create_subheading(subheading, styles):
    """Create a subheading paragraph"""
    return Paragraph(subheading, styles["Heading2"])

def create_paragraph(text, styles):
    """Create a normal paragraph"""
    return Paragraph(text, styles["Normal"])

def create_table(data, colWidths=None, rowHeights=None):
    """Create a table with data"""
    table = Table(data, colWidths=colWidths, rowHeights=rowHeights)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    return table

def create_pie_chart(data, labels, title=None, width=5*inch, height=3*inch):
    """Create a pie chart"""
    drawing = Drawing(width, height)
    
    # Add title if provided
    if title:
        drawing.add(String(width/2, height-10, title, textAnchor='middle'))
    
    # Create pie chart
    pie = Pie()
    pie.x = width/2
    pie.y = height/2 - 10  # Adjust position if there's a title
    pie.width = min(width, height) * 0.6
    pie.height = min(width, height) * 0.6
    pie.data = data
    pie.labels = labels
    pie.slices.strokeWidth = 0.5
    
    # Add different colors for slices
    colors_list = [
        colors.blue, colors.green, colors.red, colors.orange, 
        colors.purple, colors.yellow, colors.pink, colors.lightblue,
        colors.lightgreen, colors.coral
    ]
    
    for i in range(len(data)):
        pie.slices[i].fillColor = colors_list[i % len(colors_list)]
    
    # Add legend
    if labels:
        legend = Legend()
        legend.alignment = 'right'
        legend.x = width - 10
        legend.y = height / 2
        legend.colorNamePairs = [(colors_list[i % len(colors_list)], labels[i]) for i in range(len(labels))]
        drawing.add(legend)
    
    drawing.add(pie)
    return drawing

def create_bar_chart(data, categories, title=None, width=7*inch, height=4*inch):
    """Create a bar chart"""
    drawing = Drawing(width, height)
    
    # Add title if provided
    if title:
        drawing.add(String(width/2, height-10, title, textAnchor='middle'))
    
    # Create bar chart
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 50
    bc.height = height - 100
    bc.width = width - 100
    bc.data = data
    bc.categoryAxis.categoryNames = categories
    bc.valueAxis.valueMin = 0
    
    # Automatically determine valueMax with 10% headroom
    max_value = max([max(d) for d in data]) if data and data[0] else 0
    bc.valueAxis.valueMax = max_value * 1.1
    
    # Add grid lines
    bc.valueAxis.gridStrokeWidth = 0.5
    bc.valueAxis.gridStrokeColor = colors.lightgrey
    
    # Add labels
    bc.categoryAxis.labels.boxAnchor = 'ne'
    bc.categoryAxis.labels.dx = 8
    bc.categoryAxis.labels.dy = -2
    bc.categoryAxis.labels.angle = 30
    
    # Style bars
    colors_list = [colors.blue, colors.green, colors.red, colors.orange, colors.purple]
    for i in range(len(data)):
        bc.bars[i].fillColor = colors_list[i % len(colors_list)]
    
    drawing.add(bc)
    return drawing

def create_line_chart(data, categories, series_names=None, title=None, width=7*inch, height=4*inch):
    """Create a line chart"""
    drawing = Drawing(width, height)
    
    # Add title if provided
    if title:
        drawing.add(String(width/2, height-10, title, textAnchor='middle'))
    
    # Create line chart
    lc = HorizontalLineChart()
    lc.x = 50
    lc.y = 50
    lc.height = height - 100
    lc.width = width - 100
    lc.data = data
    lc.categoryAxis.categoryNames = categories
    lc.valueAxis.valueMin = 0
    
    # Automatically determine valueMax with 10% headroom
    max_value = max([max(d) for d in data]) if data and data[0] else 0
    lc.valueAxis.valueMax = max_value * 1.1
    
    # Add grid lines
    lc.valueAxis.gridStrokeWidth = 0.5
    lc.valueAxis.gridStrokeColor = colors.lightgrey
    
    # Add labels
    lc.categoryAxis.labels.boxAnchor = 'ne'
    lc.categoryAxis.labels.dx = 8
    lc.categoryAxis.labels.dy = -2
    
    # Style lines
    colors_list = [colors.blue, colors.green, colors.red, colors.orange, colors.purple]
    for i in range(len(data)):
        lc.lines[i].strokeColor = colors_list[i % len(colors_list)]
        lc.lines[i].strokeWidth = 2
    
    drawing.add(lc)
    return drawing

def add_logo(elements, logo_path, width=2*inch):
    """Add logo to PDF if it exists"""
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=width)
            elements.append(img)
            elements.append(Spacer(1, 0.25*inch))
        except Exception as e:
            logger.warning(f"Could not add logo: {str(e)}")

def generate_monthly_report_pdf(report_data, currency="IDR"):
    """Generate a PDF monthly report"""
    buffer = BytesIO()
    
    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"{settings.APP_NAME} - Monthly Report",
        author=settings.APP_NAME,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Centered', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
    
    # Content elements
    elements = []
    
    # Logo (if exists)
    logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'logo.png')
    add_logo(elements, logo_path)
    
    # Title
    year = report_data['year']
    month = report_data['month']
    month_name = calendar.month_name[month]
    
    elements.append(create_title(f"{settings.APP_NAME} - Monthly Report", styles))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(create_heading(f"{month_name} {year}", styles))
    elements.append(Spacer(1, 0.25*inch))
    
    # Summary
    elements.append(create_subheading("Summary", styles))
    elements.append(Spacer(1, 0.1*inch))
    
    total_billed_amount = report_data.get('total_billed_amount', 0)
    total_monthly_equivalent = report_data.get('total_monthly_equivalent', 0)
    subscription_count = report_data.get('subscription_count', 0)
    
    summary_data = [
        ["Metric", "Value"],
        ["Total Billed Amount", f"{currency} {total_billed_amount:,.2f}"],
        ["Monthly Equivalent", f"{currency} {total_monthly_equivalent:,.2f}"],
        ["Active Subscriptions", f"{subscription_count}"]
    ]
    
    elements.append(create_table(summary_data))
    elements.append(Spacer(1, 0.25*inch))
    
    # Category breakdown
    by_category = report_data.get('by_category', [])
    if by_category:
        elements.append(create_subheading("Category Breakdown", styles))
        elements.append(Spacer(1, 0.1*inch))
        
        # Prepare data for table
        category_table_data = [["Category", "Count", "Monthly Amount"]]
        pie_data = []
        pie_labels = []
        
        for category in by_category:
            category_name = category.get('name', 'Unknown')
            count = category.get('count', 0)
            monthly_equivalent = category.get('monthly_equivalent', 0)
            
            category_table_data.append([
                category_name,
                str(count),
                f"{currency} {monthly_equivalent:,.2f}"
            ])
            
            if monthly_equivalent > 0:  # Only include non-zero values in chart
                pie_data.append(monthly_equivalent)
                pie_labels.append(category_name)
        
        # Add table
        elements.append(create_table(category_table_data))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add pie chart
        if pie_data:
            elements.append(create_pie_chart(
                pie_data, 
                pie_labels, 
                title="Monthly Expense by Category"
            ))
            elements.append(Spacer(1, 0.25*inch))
    
    # Subscription details
    subscription_details = report_data.get('subscription_details', [])
    if subscription_details:
        elements.append(create_subheading("Subscription Details", styles))
        elements.append(Spacer(1, 0.1*inch))
        
        # Prepare data for table
        subscription_table_data = [["Name", "Amount", "Next Billing", "Category"]]
        
        for sub in subscription_details:
            name = sub.get('name', 'Unknown')
            amount = sub.get('amount', 0)
            next_billing_date = sub.get('next_billing_date', '')
            category = sub.get('category', {})
            category_name = category.get('name', 'Uncategorized') if category else 'Uncategorized'
            
            subscription_table_data.append([
                name,
                f"{currency} {amount:,.2f}",
                next_billing_date,
                category_name
            ])
        
        # Add table with adjusted column widths
        col_widths = [2.5*inch, 1.2*inch, 1.2*inch, 1.5*inch]
        elements.append(create_table(subscription_table_data, colWidths=col_widths))
        elements.append(Spacer(1, 0.25*inch))
    
    # Payment history
    payment_history = report_data.get('payment_history', [])
    if payment_history:
        elements.append(create_subheading("Payment History", styles))
        elements.append(Spacer(1, 0.1*inch))
        
        # Prepare data for table
        payment_table_data = [["Date", "Subscription", "Amount", "Method", "Status"]]
        
        for payment in payment_history:
            payment_date = payment.get('payment_date', '')
            subscription_name = payment.get('subscription_name', 'Unknown')
            amount = payment.get('amount', 0)
            payment_method = payment.get('payment_method', '-')
            status = payment.get('status', 'unknown')
            
            payment_table_data.append([
                payment_date,
                subscription_name,
                f"{currency} {amount:,.2f}",
                payment_method or "-",
                status.capitalize()
            ])
        
        # Add table with adjusted column widths
        col_widths = [1*inch, 2.5*inch, 1.2*inch, 1.2*inch, 0.8*inch]
        elements.append(create_table(payment_table_data, colWidths=col_widths))
        elements.append(Spacer(1, 0.25*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Right"]))
    elements.append(Paragraph(f"© {datetime.now().year} {settings.APP_NAME}", styles["Centered"]))
    
    # Build the document
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_yearly_report_pdf(report_data, currency="IDR"):
    """Generate a PDF yearly report"""
    buffer = BytesIO()
    
    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"{settings.APP_NAME} - Yearly Report",
        author=settings.APP_NAME,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Centered', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
    
    # Content elements
    elements = []
    
    # Logo (if exists)
    logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'logo.png')
    add_logo(elements, logo_path)
    
    # Title
    year = report_data['year']
    
    elements.append(create_title(f"{settings.APP_NAME} - Yearly Report", styles))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(create_heading(f"Annual Summary {year}", styles))
    elements.append(Spacer(1, 0.25*inch))
    
    # Summary
    elements.append(create_subheading("Annual Summary", styles))
    elements.append(Spacer(1, 0.1*inch))
    
    total_yearly_amount = report_data.get('total_yearly_amount', 0)
    total_annual_equivalent = report_data.get('total_annual_equivalent', 0)
    subscription_count = report_data.get('subscription_count', 0)
    
    summary_data = [
        ["Metric", "Value"],
        ["Total Yearly Amount", f"{currency} {total_yearly_amount:,.2f}"],
        ["Annual Equivalent", f"{currency} {total_annual_equivalent:,.2f}"],
        ["Active Subscriptions", f"{subscription_count}"]
    ]
    
    elements.append(create_table(summary_data))
    elements.append(Spacer(1, 0.25*inch))
    
    # Monthly breakdown
    monthly_data = report_data.get('monthly_data', [])
    if monthly_data:
        elements.append(create_subheading("Monthly Breakdown", styles))
        elements.append(Spacer(1, 0.1*inch))
        
        # Prepare data for table and chart
        monthly_table_data = [["Month", "Billed Amount", "Monthly Equivalent"]]
        bar_data = [[]]  # For the billed amounts
        bar_categories = []  # Month names
        
        for month_data in monthly_data:
            month_name = month_data.get('month_name', 'Unknown')
            billed_amount = month_data.get('total_billed_amount', 0)
            monthly_equivalent = month_data.get('total_monthly_equivalent', 0)
            
            monthly_table_data.append([
                month_name,
                f"{currency} {billed_amount:,.2f}",
                f"{currency} {monthly_equivalent:,.2f}"
            ])
            
            bar_data[0].append(billed_amount)
            bar_categories.append(month_name[:3])  # Abbreviated month name
        
        # Add table
        elements.append(create_table(monthly_table_data))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add bar chart
        if bar_data[0]:
            elements.append(create_bar_chart(
                bar_data, 
                bar_categories, 
                title="Monthly Expenses"
            ))
            elements.append(Spacer(1, 0.25*inch))
    
    # Category breakdown
    by_category = report_data.get('by_category', [])
    if by_category:
        elements.append(create_subheading("Category Breakdown", styles))
        elements.append(Spacer(1, 0.1*inch))
        
        # Prepare data for table and pie chart
        category_table_data = [["Category", "Count", "Annual Amount"]]
        pie_data = []
        pie_labels = []
        
        for category in by_category:
            category_name = category.get('name', 'Unknown')
            count = category.get('count', 0)
            annual_amount = category.get('annual_amount', 0)
            
            category_table_data.append([
                category_name,
                str(count),
                f"{currency} {annual_amount:,.2f}"
            ])
            
            if annual_amount > 0:  # Only include non-zero values in chart
                pie_data.append(annual_amount)
                pie_labels.append(category_name)
        
        # Add table
        elements.append(create_table(category_table_data))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add pie chart
        if pie_data:
            elements.append(create_pie_chart(
                pie_data, 
                pie_labels, 
                title="Annual Expense by Category"
            ))
            elements.append(Spacer(1, 0.25*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Right"]))
    elements.append(Paragraph(f"© {datetime.now().year} {settings.APP_NAME}", styles["Centered"]))
    
    # Build the document
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_subscription_details_pdf(subscription, payment_history=None, currency="IDR"):
    """Generate a PDF for a single subscription with detailed information"""
    buffer = BytesIO()
    
    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"{settings.APP_NAME} - Subscription Details",
        author=settings.APP_NAME,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Centered', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
    
    # Content elements
    elements = []
    
    # Logo (if exists)
    logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'logo.png')
    add_logo(elements, logo_path)
    
    # Title
    elements.append(create_title(f"{settings.APP_NAME} - Subscription Details", styles))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(create_heading(subscription.name, styles))
    elements.append(Spacer(1, 0.25*inch))
    
    # Subscription Details
    elements.append(create_subheading("Subscription Information", styles))
    elements.append(Spacer(1, 0.1*inch))
    
    category_name = subscription.category.name if subscription.category else "Uncategorized"
    
    details_data = [
        ["Field", "Value"],
        ["Name", subscription.name],
        ["Description", subscription.description or "-"],
        ["Amount", f"{currency} {subscription.amount:,.2f}"],
        ["Billing Cycle", subscription.billing_cycle.capitalize()],
        ["Next Billing Date", subscription.next_billing_date.strftime("%Y-%m-%d")],
        ["Start Date", subscription.start_date.strftime("%Y-%m-%d")],
        ["Category", category_name],
        ["Website", subscription.website_url or "-"],
        ["Status", "Active" if subscription.is_active else "Inactive"],
        ["Auto Renew", "Yes" if subscription.auto_renew else "No"],
        ["Reminder Days", str(subscription.reminder_days)],
    ]
    
    if subscription.end_date:
        details_data.insert(7, ["End Date", subscription.end_date.strftime("%Y-%m-%d")])
    
    elements.append(create_table(details_data))
    elements.append(Spacer(1, 0.25*inch))
    
    # Notes (if any)
    if subscription.notes:
        elements.append(create_subheading("Notes", styles))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(create_paragraph(subscription.notes, styles))
        elements.append(Spacer(1, 0.25*inch))
    
    # Payment History (if provided)
    if payment_history:
        elements.append(create_subheading("Payment History", styles))
        elements.append(Spacer(1, 0.1*inch))
        
        payment_data = [["Date", "Amount", "Status", "Payment Method", "Notes"]]
        
        for payment in payment_history:
            payment_data.append([
                payment.payment_date.strftime("%Y-%m-%d"),
                f"{currency} {payment.amount:,.2f}",
                payment.status.capitalize(),
                payment.payment_method or "-",
                payment.notes or "-"
            ])
        
        elements.append(create_table(payment_data))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add a payment trend chart if there are multiple payments
        if len(payment_history) > 1:
            # Collect data for the chart
            dates = [p.payment_date for p in payment_history]
            amounts = [p.amount for p in payment_history]
            
            # Sort by date
            sorted_data = sorted(zip(dates, amounts))
            dates = [d.strftime("%Y-%m-%d") for d, _ in sorted_data]
            amounts = [a for _, a in sorted_data]
            
            # Create chart
            elements.append(create_line_chart(
                [amounts],
                dates,
                title="Payment History Trend"
            ))
            elements.append(Spacer(1, 0.25*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Right"]))
    elements.append(Paragraph(f"© {datetime.now().year} {settings.APP_NAME}", styles["Centered"]))
    
    # Build the document
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Import these classes only if needed for importing - they'll be available
# for the create_pie_chart function
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.shapes import String