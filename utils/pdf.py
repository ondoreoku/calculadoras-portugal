from weasyprint import HTML
from jinja2 import Template
from datetime import datetime
def gerar_pdf_resultado(tipo, inputs, resultado):
    template_html = """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Calculadora {{ tipo }}</title>
    <style>
    body { font-family: Arial; margin: 40px; background: #f9fafb; }
    .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1 { color: #059669; border-bottom: 3px solid #059669; padding-bottom: 10px; }
    .resultado { background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #059669; }
    .dados { background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; text-align: center; }
    .label { font-weight: 600; color: #374151; }
    .valor { color: #059669; font-weight: 700; }
    </style>
    </head>
    <body>
    <div class="container">
    <h1>📊 Calculadora de {{ tipo }}</h1>
    <p><strong>Data:</strong> {{ data }}</p>
    <div class="resultado"><h2>📈 Resultado</h2>
    {% for key, value in resultado.items() %}
    <p><span class="label">{{ key }}:</span> <span class="valor">{{ value }}</span></p>
    {% endfor %}
    </div>
    <div class="dados"><h3>📋 Dados de Entrada</h3>
    {% for key, value in inputs.items() %}
    <p><span class="label">{{ key }}:</span> {{ value }}</p>
    {% endfor %}
    </div>
    <div class="footer"><p>Calculadoras Portugal 2026</p><p>https://calculadoras-portugal.onrender.com</p></div>
    </div>
    </body>
    </html>
    """
    html = Template(template_html).render(tipo=tipo, data=datetime.now().strftime("%d/%m/%Y às %H:%M"), inputs=inputs, resultado=resultado)
    try:
        return HTML(string=html).write_pdf()
    except:
        return None
