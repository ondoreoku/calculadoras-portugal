from jinja2 import Template
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def gerar_pdf_resultado(tipo, inputs, resultado):
    """
    Gera um PDF simplificado (HTML formatado como PDF)
    """
    try:
        # Gerar HTML para PDF
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Calculadora {tipo}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f9fafb; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; }}
                h1 {{ color: #059669; border-bottom: 3px solid #059669; padding-bottom: 10px; }}
                .resultado {{ background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #059669; }}
                .label {{ font-weight: 600; color: #374151; }}
                .valor {{ color: #059669; font-weight: 700; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Calculadora de {tipo}</h1>
                <p><strong>Data:</strong> {datetime.now().strftime("%d/%m/%Y às %H:%M")}</p>
                <div class="resultado">
                    <h2 style="font-size:18px; margin-top:0;">📈 Resultado</h2>
        """
        
        for key, value in resultado.items():
            html += f'<p><span class="label">{key}:</span> <span class="valor">{value}</span></p>'
        
        html += """
                </div>
                <div class="dados" style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="font-size:16px; margin-top:0;">📋 Dados de Entrada</h3>
        """
        
        for key, value in inputs.items():
            html += f'<p><span class="label">{key}:</span> {value}</p>'
        
        html += f"""
                </div>
                <div class="footer">
                    <p>Calculadoras Portugal 2026</p>
                    <p>https://calculadoras-portugal.onrender.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Tentar usar weasyprint se estiver disponível
        try:
            from weasyprint import HTML
            pdf = HTML(string=html).write_pdf()
            if pdf and len(pdf) > 100:
                logger.info(f"[PDF] PDF gerado com weasyprint ({len(pdf)} bytes)")
                return pdf
        except Exception as e:
            logger.warning(f"[PDF] weasyprint falhou: {e}")
        
        # Fallback: retornar HTML como texto (será salvo como .html)
        logger.info("[PDF] Usando fallback HTML")
        return html.encode('utf-8')
        
    except Exception as e:
        logger.error(f"[PDF] Falha ao gerar: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
