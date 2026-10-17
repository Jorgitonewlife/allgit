# allgit — Meus Projetos de Automação em Python

Este repositório reúne pequenos projetos de automação que criei para praticar Python e montar um portfólio de freelancer. Cada projeto fica em sua própria pasta, com README próprio, passos numerados e arquivos de exemplo.

## Projetos

| Projeto | Pasta | O que faz |
|---------|-------|-----------|
| **Organizador de Downloads** | `organizador/` | Move arquivos da pasta Downloads para subpastas por tipo (`.pdf`, `.jpg`, `.zip`, `.csv`, `.mp4`, outros) |
| **Renomeador em Massa** | `renomeador/` | Renomeia vários arquivos de uma vez, adicionando um prefixo personalizado (ex: `viagem_2026_foto_01.jpg`) |
| **Gerador de Recibos** | `gerador_recibos/` | Lê uma planilha Excel de clientes e gera um recibo `.txt` separado para cada um |
| **Conversor de PDF para Texto** | `conversor_pdf/` | Extrai o texto de arquivos PDF e salva cada um em um `.txt` correspondente |

## Como usar cada projeto

Cada pasta tem seu próprio `README.md` com instruções detalhadas. Em geral, o fluxo é:

```bash
# 1. Entre na pasta do projeto
cd organizador

# 2. Rode os passos em ordem
python passo1_listar.py
python passo2_classificar.py
python passo3_mover.py
```

## Pré-requisitos

Os projetos usam apenas a biblioteca padrão do Python, exceto:

- `gerador_recibos/` → `openpyxl` (ler Excel)
- `conversor_pdf/` → `pypdf` (ler PDF) e `reportlab` (criar PDF de exemplo)

Para instalar:

```bash
pip install -r gerador_recibos/requirements.txt
pip install -r conversor_pdf/requirements.txt
```

## Tecnologias

- Python 3
- openpyxl
- pypdf
- reportlab

---

Feito por Jorge Augusto Magalhaes — focado em automação prática para pequenos negócios e freelancer.
