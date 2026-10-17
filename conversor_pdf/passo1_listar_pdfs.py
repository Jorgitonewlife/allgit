# Bloco 1: listar PDFs em uma pasta

import os

# Pasta onde estão os PDFs (dentro do projeto)
pasta_pdfs = os.path.join(os.path.dirname(__file__), "pdfs_exemplo")

# Cria a pasta se não existir (para você colocar seus PDFs lá)
os.makedirs(pasta_pdfs, exist_ok=True)

# Lista arquivos que terminam com .pdf
arquivos = os.listdir(pasta_pdfs)
pdfs = [a for a in arquivos if a.lower().endswith(".pdf")]

print(f"Encontrei {len(pdfs)} arquivo(s) PDF na pasta pdfs_exemplo:")
for nome in pdfs:
    print(f" - {nome}")

if len(pdfs) == 0:
    print("\nDica: coloque algum arquivo .pdf dentro da pasta pdfs_exemplo/ para testar.")
