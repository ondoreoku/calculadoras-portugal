from weasyprint import HTML, CSS
from jinja2 import Template
from datetime import datetime
import os

def gerar_pdf_resultado(tipo, inputs, resultado):
    template_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Calculadora {{ tipo }}</title>
        <style>
            body { 
                font-family: Arial, Helvetica, sans-serif; 
                margin: 40px; 
                background: #f9fafb;
                color: #1f2937;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 12px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            }
            h1 { 
                color: #059669; 
                border-bottom: 3px solid #059669; 
                padding-bottom: 10px; 
                font-size: 24px;
            }
            .resultado { 
                background: #f0fdf4; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 20px 0; 
                border-left: 4px solid #059669; 
            }
            .dados { 
                background: #f9fafb; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 20px 0; 
            }
            .footer { 
                margin-top: 30px; 
                padding-top: 20px; 
                border-top: 1px solid #e5e7eb; 
                font-size: 12px; 
                color: #6b7280; 
                text-align: center; 
            }
            .label { 
                font-weight: 600; 
                color: #374151; 
            }
            .valor { 
                color: #059669; 
                font-weight: 700; 
            }
            .linha {
                margin: 8px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Calculadora de {{ tipo }}</h1>
            <p><strong>Data:</strong> {{ data }}</p>
            
            <div class="resultado">
                <h2 style="font-size:18px; margin-top:0;">📈 Resultado</h2>
                {% for key, value in resultado.items() %}
                <p class="linha"><span class="label">{{ key }}:</span> <span class="valor">{{ value }}</span></p>
                {% endfor %}
            </div>
            
            <div class="dados">
                <h3 style="font-size:16px; margin-top:0;">📋 Dados de Entrada</h3>
                {% for key, value in inputs.items() %}
                <p class="linha"><span class="label">{{ key }}:</span> {{ value }}</p>
                {% endfor %}
            </div>
            
            <div class="footer">
                <p>Calculadoras Portugal 2026</p>
                <p>https://calculadoras-portugal.onrender.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        html = Template(template_html).render(
            tipo=tipo, 
            data=datetime.now().strftime("%d/%m/%Y às %H:%M"), 
            inputs=inputs, 
            resultado=resultado
        )
        
        pdf = HTML(string=html).write_pdf(
            stylesheets=[CSS(string='@page { margin: 1cm; }')]
        )
        
        if pdf and len(pdf) > 100:
            return pdf
        else:
            print(f"[ERRO PDF] PDF gerado tem apenas {len(pdf) if pdf else 0} bytes")
            return None
            
    except Exception as e:
        print(f"[ERRO PDF] Falha ao gerar PDF: {str(e)}")
        return None
