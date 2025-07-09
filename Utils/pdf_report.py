from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from datetime import datetime
import os

def generate_pdf_report(metrics, trades=None, stock_name="N/A", strategy_name="N/A", fig=None, ai_explanation=None, filename="static/trading_report.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin = 50
    y = height - margin


    c.setFont("Times-Bold", 20)
    title = "Trading Strategy Report"
    title_width = c.stringWidth(title, "Times-Bold", 20)
    c.drawString((width - title_width) / 2, y, title)
    y -= 40

    
    c.setFont("Times-Roman", 12)
    metadata_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}   |   Stock: {stock_name}   |   Strategy: {strategy_name}"
    meta_width = c.stringWidth(metadata_text, "Times-Roman", 12)
    c.drawString((width - meta_width) / 2, y, metadata_text)
    y -= 40

  
    c.setFont("Times-Bold", 16)
    perf_title = "Performance Metrics"
    perf_title_width = c.stringWidth(perf_title, "Times-Bold", 16)
    c.drawString((width - perf_title_width) / 2, y, perf_title)
    y -= 25

    data = [
        ["Metric", "Value"],
        ["Invested Capital", f"₹{metrics['invested_capital']:.2f}"],
        ["Final Portfolio Value", f"₹{metrics['portfolio_value']:.2f}"],
        ["CAGR", f"{metrics['cagr']*100:.2f}%"],
        ["Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}"],
        ["Sortino Ratio", f"{metrics['sortino_ratio']:.2f}"],
        ["Win Rate", f"{metrics['win_rate']:.2f}%"],
        ["Loss Rate", f"{metrics['loss_rate']:.2f}%"],
        ["Max Drawdown", f"{metrics['max_drawdown']*100:.2f}%"],
        ["Standard Deviation", f"{metrics['std']:.4f}"],
        ["Mean Return", f"{metrics['mean']:.4f}"],
        ["Median Return", f"{metrics['median']:.4f}"],
    ]

 
    table_width = 4.2 * inch  
    col_widths = [table_width * 0.55, table_width * 0.45]

    table = Table(data, colWidths=col_widths)
    style = TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4B8BBE')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),   
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.8, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ])
    table.setStyle(style)

    w, h = table.wrapOn(c, table_width, y)
    x = (width - w) / 2
    y -= h
    table.drawOn(c, x, y)

    y -= 25  


    if fig:
        c.setFont("Times-Bold", 16)
        perf_curve_title = "Performance Curve"
        perf_curve_width = c.stringWidth(perf_curve_title, "Times-Bold", 16)
        c.drawString((width - perf_curve_width) / 2, y, perf_curve_title)
        y -= 25

        plot_img_path = "static/plot_temp.png"
        fig.write_image(plot_img_path, width=900, height=450, scale=2)

        img_width = width - 2 * margin
        img_height = 360  
        img_x = margin
        img_y = y - img_height

        c.drawImage(plot_img_path, img_x, img_y, width=img_width, height=img_height)

        y = img_y - 20

        if os.path.exists(plot_img_path):
            os.remove(plot_img_path)

    c.save()

    return filename