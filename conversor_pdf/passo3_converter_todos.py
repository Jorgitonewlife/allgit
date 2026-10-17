# Bloco 3: converter todos os PDFs da pasta para .txt separados

import os

from pypdf import PdfReader

pasta_script = os.path.dirname(__file__)
pasta_pdfs = os.path.join(pasta_script, "pdfs_exemplo")
pasta_txt = os.path.join(pasta_script, "txt_gerados")

# Cria a pasta de saída se não existir
os.makedirs(pasta_txt, exist_ok=True)

# Lista todos os PDFs
arquivos = os.listdir(pasta_pdfs)
pdfs = [a for a in arquivos if a.lower().endswith(".pdf")]

if len(pdfs) == 0:
    print("Nenhum PDF encontrado na pasta pdfs_exemplo/")
else:
    print(f"Encontrados {len(pdfs)} PDF(s). Convertendo...\n")

    for nome_pdf in pdfs:
        caminho_pdf = os.path.join(pasta_pdfs, nome_pdf)
        reader = PdfReader(caminho_pdf)

        # Extrai texto de todas as páginas e junta
        texto_completo = ""
        for pagina in reader.pages:
            texto = pagina.extract_text()
            if texto:
                texto_completo += texto + "\n\n"

        # Nome do arquivo .txt (substitui .pdf por .txt)
        nome_txt = nome_pdf.lower().replace(".pdf", ".txt")
        caminho_txt = os.path.join(pasta_txt, nome_txt)

        # Salva o arquivo
        with open(caminho_txt, "w", encoding="utf-8") as f:
            f.write(texto_completo)

        print(f"Convertido: {nome_pdf} → {nome_txt}")

    print(f"\nPronto! {len(pdfs)} PDF(s) convertido(s) para a pasta 'txt_gerados/'.")
