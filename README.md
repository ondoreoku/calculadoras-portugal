# 🧼 Calculadoras Portugal 2026 — Branch CLEAN CODE

**Branch dedicada à refatoração estrutural, eliminação de redundâncias e higienização profunda do repositório.**

> 🌐 **Produção:** [https://calculadoras-portugal.onrender.com](https://calculadoras-portugal.onrender.com)

---

## 📌 Histórico e Contexto

O desenvolvimento deste ecossistema passou por várias fases críticas de iteração rápida e auditoria agressiva de segurança (refletidas nas branches anteriores *Getting pissed* e *Cybersec*). Embora essas etapas tenham sido fundamentais para blindar a aplicação contra vulnerabilidades e garantir a estabilidade inicial, elas introduziram ruído, ficheiros temporários e código redundante.

A branch **Clean Code** nasce com o propósito de "despaghettificar" a base de código, consolidar a arquitetura modular e remover definitivamente todo o lixo computacional que não deve pertencer ao controlo de versões.

---

## 🎯 Objetivos Específicos de Refatoração

* **Purga de Artefactos:** Remoção total de cópias `.backup`, logs locais, dumps de ferramentas de scan (`sqlmap`, `nuclei`, `nikto`) e payloads de cookies utilizados em testes de invasão.
* **Isolamento de Domínio:** Separação estrita entre a camada de apresentação (Flask/Jinja2), a lógica de filtragem/segurança (`ip_blocker.py`, `rate_limits.py`) e os motores de cálculo puro.
* **Padronização:** Ajuste do código aos padrões de legibilidade e manutenibilidade do PEP 8, garantindo que futuras expansões sejam limpas e previsíveis.

---

## 🧮 Módulos de Cálculo Integrados (8)

A aplicação centraliza oito simuladores financeiros e fiscais essenciais para o contexto macroeconómico português:

1. **Salário Líquido:** Suporte para Contrato de Outrem e Trabalhadores Independentes (ENI).
2. **Crédito Habitação:** Simulação pelo Sistema Price com geração de tabela de amortização.
3. **Rescisão de Contrato:** Cálculo de indemnizações e direitos laborais cessantes.
4. **Subsídio de Desemprego:** Integração com os limites e indexantes IAS correspondentes.
5. **Inflação (INE):** Atualização de valores com base no Índice de Preços ao Consumidor real.
6. **ISV:** Cálculo do Imposto Sobre Veículos baseado nas tabelas de CO₂ e cilindrada.
7. **IUC:** Simulador do Imposto Único de Circulação.
8. **Poupança:** Projeções de evolução patrimonial baseadas em juros compostos.

---

## 📁 Estrutura de Ficheiros Otimizada

```text
ondoreoku-calculadoras-portugal/
├── app.py                    # Ponto de entrada Flask (Rotas e Middlewares)
├── initdb.py                 # Inicialização estrutural do SQLite
├── rate_limits.py            # Regras e limites de tráfego por IP
├── ip_blocker.py             # Lógica de contenção e bloqueio adaptativo
├── security_logger.py        # Centralização de logs e auditoria interna
├── render.yaml               # Infraestrutura como código (Blueprint Render)
├── requirements.txt          # Dependências Python estritas e atualizadas
├── README.md                 # Documentação técnica do projeto
│
├── static/
│   └── css/
│       └── style.css         # Estilização global e suporte a Dark Mode
│
├── templates/                # Camada de Visualização (HTML + Jinja2)
│   ├── base.html             # Esqueleto estrutural comum
│   └── [calculadoras].html   # Interfaces dedicadas a cada simulador
│
├── utils/                    # Motores de Cálculo Isolados (Regras de Negócio)
│   ├── __init__.py
│   ├── salario.py | credito.py | rescisao.py | subsidio.py | poupanca.py
│   ├── ine.py | carros.py    # Integrações externas e parsing de tabelas
│   ├── noticias.py           # Parsing do Feed RSS de atualizações económicas
│   └── pdf.py                # Geração de relatórios estruturados (ReportLab)
│
└── .github/
    └── workflows/
        └── security.yml      # CI/CD - Verificação estática de segurança

## 🖥️ Configuração do Ambiente Local

1. **Clonar o repositório e aceder à diretoria:**
   ```bash
   git clone [https://github.com/ondoreoku/calculadoras-portugal.git](https://github.com/ondoreoku/calculadoras-portugal.git)
   cd calculadoras-portugal

git checkout clean-code

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python3 initdb.py

python3 app.py

Para validar que as operações de limpeza e refatoração mantiveram a integridade de todas as rotas e regras fiscais, execute o script de automação de testes:

./testar_tudo.sh

© 2026 Calculadoras Portugal — Engenharia e Refatoração de Software.