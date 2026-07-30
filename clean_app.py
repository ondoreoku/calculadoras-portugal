#!/usr/bin/env python3
import re

with open('app.py', 'r') as f:
    content = f.read()

# Padrão para encontrar funções PDF duplicadas
pattern = r'@app\.route\("/salario/pdf".*?def salario_pdf\(\):.*?(?=@app\.route|\Z)'

# Encontrar todas as ocorrências
matches = list(re.finditer(pattern, content, re.DOTALL))

print(f"Encontradas {len(matches)} definições de salario_pdf")

if len(matches) > 1:
    # Manter apenas a última
    last_match = matches[-1]
    
    # Remover todas as ocorrências anteriores
    for match in matches[:-1]:
        content = content.replace(match.group(0), '')
    
    # Escrever o ficheiro limpo
    with open('app.py', 'w') as f:
        f.write(content)
    print(f"✅ Removidas {len(matches)-1} definições duplicadas")
    
    # Verificar se ainda há outras duplicações
    with open('app.py', 'r') as f:
        new_content = f.read()
    
    # Verificar outras funções PDF
    for func in ['credito_pdf', 'rescisao_pdf', 'subsidio_pdf']:
        count = len(re.findall(rf'def {func}\(\):', new_content))
        if count > 1:
            print(f"⚠️ Ainda há {count} definições de {func}")
else:
    print("✅ Apenas uma definição encontrada")
