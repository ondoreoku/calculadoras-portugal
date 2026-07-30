# 🔐 Calculadoras Portugal 2026 — Branch CYBERSEC

**Branch de segurança e funcionalidades avançadas** do projeto Calculadoras Portugal 2026.

> 🌐 **Site em produção:** [https://calculadoras-portugal.onrender.com](https://calculadoras-portugal.onrender.com)

---

## 📌 ÍNDICE

- [Sobre o Branch](#sobre-o-branch)
- [Calculadoras Disponíveis](#calculadoras-disponíveis)
- [Funcionalidades de Segurança](#funcionalidades-de-segurança)
- [APIs Disponíveis](#apis-disponíveis)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar Localmente](#como-executar-localmente)
- [Deploy no Render](#deploy-no-render)
- [Testes Automatizados](#testes-automatizados)

---

## 📖 Sobre o Branch

O branch **CYBERSEC** é uma evolução do projeto base com foco em:

- 🛡️ **Segurança avançada** — proteção contra ataques XSS, SQL Injection, brute force, rate limiting e headers de segurança.
- 📄 **Geração de PDFs** — resultados em PDF para todas as calculadoras.
- 🔌 **APIs REST** — integração com dados reais (INE, Carros).
- 🎨 **UI/UX melhorada** — Dark Mode, design responsivo, novas calculadoras.
- 🤖 **CI/CD** — GitHub Actions com análise de segurança automática.

---

## 🧮 Calculadoras Disponíveis (8)

| # | Calculadora | Descrição | PDF | API |
|---|-------------|-----------|-----|-----|
| 1 | **Salário Líquido** | Conta de Outrem + ENI (IRS, Segurança Social) | ✅ | ✅ |
| 2 | **Crédito Habitação** | Sistema Price com tabela de amortização | ✅ | ✅ |
| 3 | **Rescisão de Contrato** | Cálculo de indemnização (vários motivos) | ✅ | ✅ |
| 4 | **Subsídio de Desemprego** | Com limites IAS 2026 | ✅ | ✅ |
| 5 | **Inflação (INE)** | Taxa de inflação em Portugal (IPC) | ❌ | ✅ |
| 6 | **ISV** | Imposto Sobre Veículos (ano, cilindrada, CO₂) | ❌ | ✅ |
| 7 | **IUC** | Imposto Único de Circulação (ano, CO₂) | ❌ | ✅ |
| 8 | **Poupança** | Juros compostos — planeamento financeiro | ✅ | ❌ |

---

## 🛡️ Funcionalidades de Segurança

### Headers HTTP

Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Content-Security-Policy: default-src 'self' https://*.buymeacoffee.com
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=(), usb=()


### Proteções Implementadas

- ✅ **Rate Limiting** — por endpoint (HTML: 5/min, API: 10/min)
- ✅ **Bloqueio de XSS** — deteção de `<script>`, `onerror=`, `alert(`, etc.
- ✅ **Bloqueio de SQL Injection** — deteção de `UNION`, `SELECT`, `DROP`, `OR '1'='1`, etc.
- ✅ **Validação de Inputs** — números válidos, intervalos, tipos
- ✅ **Bloqueio por Cookie** — utilizador bloqueado sem afetar outros na mesma rede
- ✅ **CORS Restrito** — apenas domínios autorizados
- ✅ **Logging de Segurança** — registo de todos os eventos suspeitos

---

## 🔌 APIs Disponíveis

| Endpoint | Método | Descrição | Exemplo |
|----------|--------|-----------|---------|
| `/api/salario` | POST | Calcula salário líquido | `{"bruto":1500}` |
| `/api/credito` | POST | Simula crédito habitação | `{"valor_imovel":200000}` |
| `/api/rescisao` | POST | Calcula indemnização | `{"vencimento_base":1200}` |
| `/api/subsidio` | POST | Calcula subsídio desemprego | `{"media_salarial":1200}` |
| `/api/ine/inflacao` | GET | Inflação em Portugal | — |
| `/api/carros/isv` | GET | Imposto Sobre Veículos | `?ano=2020&cilindrada=2000&co2=150` |
| `/api/carros/iuc` | GET | Imposto Único de Circulação | `?ano=2020&co2=150` |
| `/api/health` | GET | Health check | — |

### Exemplo de uso da API

```bash
# Calcular salário líquido
curl -X POST https://calculadoras-portugal.onrender.com/api/salario \
  -H "Content-Type: application/json" \
  -d '{"bruto": 1500}'

# Resposta
{
  "bruto": 1500,
  "liquido": 1047,
  "irs": 420,
  "seguranca_social": 165,
  "regime": "Conta de Outrem"
}

🛠️ Tecnologias Utilizadas
Backend

    Python 3.12 + Flask 3.0.3

    SQLite (cache de notícias e histórico)

    Gunicorn (servidor WSGI)

Frontend

    Jinja2 (templates)

    CSS Puro (sem frameworks)

    JavaScript (Dark Mode, interações)

Segurança

    Flask-Limiter (rate limiting)

    Custom Security Headers (CSP, HSTS, etc.)

    Input Validation (sanitização e validação)

PDFs

    ReportLab 4.2.5 (geração de PDFs)

APIs Externas

    INE — dados de inflação (JSON)

    ClaraCars — cálculo ISV/IUC

DevOps

    Render (deploy gratuito)

    GitHub Actions (CI/CD com Bandit e Safety)

    Uptime Robot (monitorização)

📁 Estrutura do Projeto

calculadoras-portugal/
├── app.py                    # Flask principal (rotas, segurança)
├── initdb.py                 # Inicialização da base de dados
├── rate_limits.py            # Configuração de rate limiting
├── ip_blocker.py             # Bloqueio de IPs e ataques
├── security_logger.py        # Logging de segurança
├── render.yaml               # Configuração Render
├── requirements.txt          # Dependências Python
├── README.md                 # Este ficheiro
│
├── templates/                # HTML (Jinja2)
│   ├── base.html             # Template base (menu, dark mode)
│   ├── home.html             # Página inicial (8 cards)
│   ├── salario.html          # Calculadora Salário
│   ├── credito.html          # Calculadora Crédito
│   ├── rescisao.html         # Calculadora Rescisão
│   ├── subsidio.html         # Calculadora Subsídio
│   ├── inflacao.html         # Calculadora Inflação
│   ├── isv.html              # Calculadora ISV
│   ├── iuc.html              # Calculadora IUC
│   ├── poupanca.html         # Calculadora Poupança
│   ├── historico.html        # Histórico de cálculos
│   ├── bloqueado.html        # Página de bloqueio
│   └── 500.html              # Página de erro
│
├── static/
│   └── css/
│       └── style.css         # Estilos (inclui Dark Mode)
│
├── utils/                    # Módulos de cálculo
│   ├── __init__.py
│   ├── salario.py            # Lógica do salário
│   ├── credito.py            # Lógica do crédito
│   ├── rescisao.py           # Lógica da rescisão
│   ├── subsidio.py           # Lógica do subsídio
│   ├── poupanca.py           # Lógica da poupança (juros compostos)
│   ├── ine.py                # API INE (inflação)
│   ├── carros.py             # API Carros (ISV/IUC)
│   ├── noticias.py           # Feed RSS (ECO, Negócios, Económico)
│   └── pdf.py                # Geração de PDFs (reportlab)
│
├── .github/
│   └── workflows/
│       └── security.yml      # GitHub Actions (Bandit, Safety)
│
└── sqlmap_results/           # Resultados de testes de segurança (SQLMap)

🖥️ Como Executar Localmente

# 1. Clonar o repositório
git clone https://github.com/ondoreoku/calculadoras-portugal.git
cd calculadoras-portugal

# 2. Mudar para o branch CYBERSEC
git checkout CYBERSEC

# 3. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Criar base de dados (só uma vez)
python3 initdb.py

# 6. Iniciar servidor
python3 app.py

# 7. Abrir http://127.0.0.1:5000

🚀 Deploy no Render
Configuração automática (via render.yaml)

services:
  - type: web
    name: calculadoras-portugal-2026
    runtime: python
    plan: free
    buildCommand: |
      apt-get update && apt-get install -y \
        build-essential \
        python3-dev \
        libpango1.0-dev \
        libpangoft2-1.0-0 \
        libharfbuzz-dev \
        libfreetype-dev \
        libffi-dev \
        libjpeg-dev \
        libopenjp2-7 \
        libtiff-dev \
        && pip install -r requirements.txt
    startCommand: "gunicorn app:app"
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: FLASK_ENV
        value: production
        
Deploy manual

git push origin CYBERSEC
# O Render deteta automaticamente e faz deploy

🧪 Testes Automatizados
Executar testes completos

./testar_completo.sh

O que é testado (29 testes)

    ✅ Health Check

    ✅ Todas as páginas HTML (8 calculadoras + home + histórico)

    ✅ APIs (Salário, Crédito, Rescisão, Subsídio, INE, ISV, IUC)

    ✅ PDFs (todas as calculadoras com PDF)

    ✅ Headers de Segurança (5 headers)

    ✅ Rate Limiting

    ✅ XSS Protection

    ✅ SQL Injection Protection

    ✅ Dark Mode

    ✅ Notícias

    ✅ CORS

    ✅ Interface Visual

Resultado esperado
text

✅ Total de testes: 29
✅ Passaram: 29
❌ Falharam: 0
📊 Taxa de sucesso: 100%
🎉 TODOS OS TESTES PASSARAM!
🚀 PROJETO 100% FUNCIONAL!

🔗 Links Úteis

    🌐 Site em produção: https://calculadoras-portugal.onrender.com

    📦 Repositório: https://github.com/ondoreoku/calculadoras-portugal

    📊 Uptime Robot: https://uptimerobot.com

    ☕ Apoiar o projeto: https://www.buymeacoffee.com/ondoreoku

📝 Notas

    Este branch (CYBERSEC) é a versão principal em produção.

    O branch main contém a versão base (sem as funcionalidades avançadas).

    O Render está configurado para fazer deploy automático do branch CYBERSEC.

© 2026 Calculadoras Portugal — Branch CYBERSEC
