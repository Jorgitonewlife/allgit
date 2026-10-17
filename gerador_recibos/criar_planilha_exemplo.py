# Gera clientes.xlsx a partir de clientes.csv (arenas uma vez, para criar a planilha de exemplo)

import csv
import os

from openpyxl import Workbook

caminho_csv = os.path.join(os.path.dirname(__file__), "clientes.csv")
caminho_xlsx = os.path.join(os.path.dirname(__file__), "clientes.xlsx")

wb = Workbook()
ws = wb.active
ws.title = "Clientes"

with open(caminho_csv, newline="", encoding="utf-8") as f:
    leitor = csv.reader(f)
    for linha in leitor:
        ws.append(linha)

wb.save(caminho_xlsx)
print(f"Planilha criada: {caminho_xlsx}")
