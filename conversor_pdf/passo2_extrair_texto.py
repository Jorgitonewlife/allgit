# Bloco 2: extrair texto de um PDF

import os

from pypdf import PdfReader

pasta_script = os.path.dirname(__file__)
caminho_pdf = os.path.join(pasta_script, "pdfs_exemplo", "exemplo_fatura.pdf")

# Abre o PDF
reader = PdfReader(caminho_pdf)

print(f"Arquivo: {caminho_pdf}")
print(f"Número de páginas: {len(reader.pages)}")
print()

# Extrai o texto de cada página
for i, pagina in enumerate(reader.pages, start=1):
    texto = pagina.extract_text()
    print(f"--- Página {i} ---")
    print(texto if texto else "(sem texto extraído)")
    print()
