# Calculadoras Portugal 2026

Aplicação Flask com 4 calculadoras financeiras para Portugal:
- Salário Líquido (conta de outrem + ENI)
- Crédito Habitação (sistema Price)
- Rescisão de Contrato
- Subsídio de Desemprego

## Funcionalidades

- Cálculos no servidor (Python)
- Histórico de cálculos em SQLite
- Feed de notícias via RSS (ECO, Jornal de Negócios, O Jornal Económico)
- Design responsivo, sem emojis

## Stack

- Python 3.12 + Flask
- SQLite (base de dados local)
- Jinja2 (templates)
- CSS puro (sem frameworks)

## Deploy no Render (gratuito)

1. Fork este repositório para a tua conta GitHub
2. Cria conta em [render.com](https://render.com)
3. Cria um **Web Service** novo
4. Liga ao teu repositório GitHub
5. O Render detecta automaticamente o `render.yaml`
6. Clica **Deploy**

### Nota importante sobre SQLite no Render

O plano gratuito do Render **não persiste ficheiros** entre reinícios. Isto significa que:
- A base de dados SQLite é criada automaticamente no primeiro deploy
- Os dados são **perdidos** quando o servidor "dorme" (após 15 min de inatividade)
- Para dados persistentes, considera migrar para PostgreSQL (Railway oferece gratuito)

Para desenvolvimento local, o SQLite funciona perfeitamente.

## Correr localmente

```bash
# 1. Criar ambiente virtual (opcional mas recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar base de dados (só uma vez)
python3 initdb.py

# 4. Iniciar servidor
python3 app.py

# 5. Abrir http://127.0.0.1:5000
```

## Estrutura do projeto

```
calculadoras-portugal/
├── app.py                  # Flask principal
├── initdb.py               # Cria base de dados
├── requirements.txt        # Dependências Python
├── render.yaml             # Configuração Render
├── database.db             # SQLite (não subir para Git)
├── templates/              # HTML (Jinja2)
│   ├── base.html
│   ├── home.html
│   ├── salario.html
│   ├── credito.html
│   ├── rescisao.html
│   ├── subsidio.html
│   └── historico.html
├── static/css/
│   └── style.css
└── utils/
    ├── __init__.py
    ├── noticias.py
    ├── salario.py
    ├── credito.py
    ├── rescisao.py
    └── subsidio.py
```

## Licença

Projeto de aprendizagem — uso livre.
