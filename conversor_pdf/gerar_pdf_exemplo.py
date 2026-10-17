# Gera um PDF de exemplo para testar o conversor

import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

caminho = os.path.join(os.path.dirname(__file__), "pdfs_exemplo", "exemplo_fatura.pdf")

c = canvas.Canvas(caminho, pagesize=A4)
largura, altura = A4

c.setFont("Helvetica-Bold", 16)
c.drawString(50, altura - 50, "FATURA EXEMPLO")

c.setFont("Helvetica", 12)
c.drawString(50, altura - 90, "Cliente: João Silva")
c.drawString(50, altura - 110, "Serviço: Desenvolvimento de Sistema Web")
c.drawString(50, altura - 130, "Valor: R$ 2.500,00")
c.drawString(50, altura - 150, "Data: 15/10/2026")

c.drawString(50, altura - 190, "Descricao:")
c.drawString(50, altura - 210, "- Analise de requisitos")
c.drawString(50, altura - 230, "- Codificacao do front-end")
c.drawString(50, altura - 250, "- Testes e deploy")

c.save()
print(f"PDF criado: {caminho}")
