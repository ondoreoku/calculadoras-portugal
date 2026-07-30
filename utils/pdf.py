from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime
import io
import logging

logger = logging.getLogger(__name__)

def gerar_pdf_resultado(tipo, inputs, resultado):
    """
    Gera PDF usando reportlab
    """
    try:
        # Criar buffer para o PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        styles = getSampleStyleSheet()
        
        # Estilo personalizado
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#059669'),
            spaceAfter=12,
            alignment=1  # Centro
        )
        
        subtitulo_style = ParagraphStyle(
            'Subtitulo',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#059669'),
            spaceAfter=10
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6
        )
        
        valor_style = ParagraphStyle(
            'Valor',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#059669'),
            fontWeight='bold'
        )
        
        # Construir o documento
        story = []
        
        # Título
        story.append(Paragraph(f"📊 Calculadora de {tipo}", titulo_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Data
        story.append(Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", normal_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Resultados
        story.append(Paragraph("📈 Resultado", subtitulo_style))
        
        # Tabela de resultados
        data = []
        for key, value in resultado.items():
            data.append([Paragraph(key, normal_style), Paragraph(str(value), valor_style)])
        
        if data:
            table = Table(data, colWidths=[4*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#059669')),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#059669')),
            ]))
            story.append(table)
        
        story.append(Spacer(1, 0.5*cm))
        
        # Dados de entrada
        story.append(Paragraph("📋 Dados de Entrada", subtitulo_style))
        
        data_inputs = []
        for key, value in inputs.items():
            data_inputs.append([Paragraph(key, normal_style), Paragraph(str(value), normal_style)])
        
        if data_inputs:
            table_inputs = Table(data_inputs, colWidths=[4*cm, 4*cm])
            table_inputs.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(table_inputs)
        
        story.append(Spacer(1, 1*cm))
        
        # Rodapé
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=1
        )
        story.append(Paragraph("Calculadoras Portugal 2026", footer_style))
        story.append(Paragraph("https://calculadoras-portugal.onrender.com", footer_style))
        
        # Gerar PDF
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        if pdf_bytes and len(pdf_bytes) > 100:
            logger.info(f"[PDF] PDF gerado com reportlab ({len(pdf_bytes)} bytes)")
            return pdf_bytes
        else:
            logger.error(f"[PDF] PDF gerado tem apenas {len(pdf_bytes) if pdf_bytes else 0} bytes")
            return None
            
    except Exception as e:
        logger.error(f"[PDF] Falha ao gerar PDF: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
