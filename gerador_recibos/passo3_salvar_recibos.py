# Bloco 3: salvar cada recibo como arquivo .txt separado

import os
from openpyxl import load_workbook

caminho_planilha = os.path.join(os.path.dirname(__file__), "clientes.xlsx")
pasta_recibos = os.path.join(os.path.dirname(__file__), "recibos_gerados")

# Cria a pasta de recibos se não existir
os.makedirs(pasta_recibos, exist_ok=True)

wb = load_workbook(caminho_planilha)
ws = wb.active

# Pula o cabeçalho
linhas = list(ws.iter_rows(values_only=True))[1:]

for linha in linhas:
    nome, email, valor, servico = linha

    recibo = f"""==============================
        RECIBO DE PAGAMENTO
==============================

Cliente: {nome}
E-mail:  {email}
Serviço: {servico}
Valor:   R$ {valor}

Data: 15/10/2026

Assinatura: __________________________

==============================
Obrigado pela preferência!
=============================="""

    # Nome do arquivo seguro (remove espaços e caracteres especiais)
    nome_arquivo = f"recibo_{nome.replace(' ', '_')}.txt"
    caminho_arquivo = os.path.join(pasta_recibos, nome_arquivo)

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(recibo)

    print(f"Salvo: {nome_arquivo}")

print(f"\nPronto! {len(linhas)} recibos salvos na pasta 'recibos_gerados'.")
