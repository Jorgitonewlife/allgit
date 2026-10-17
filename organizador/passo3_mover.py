# Bloco 3: mover arquivos de verdade para as pastas certas
# Conceitos novos: shutil.move, os.path.isfile, os.makedirs

import os
import shutil

downloads = os.path.join(os.path.expanduser("~"), "Downloads")

arquivos = os.listdir(downloads)

for arquivo in arquivos:
    caminho_origem = os.path.join(downloads, arquivo)

    # ignora pastas, pega só arquivos
    if not os.path.isfile(caminho_origem):
        continue

    # descobre a pasta de destino
    if arquivo.endswith(".pdf"):
        pasta = "Documentos"
    elif arquivo.endswith(".jpg"):
        pasta = "Imagens"
    elif arquivo.endswith(".zip"):
        pasta = "Compactados"
    elif arquivo.endswith(".csv"):
        pasta = "Planilhas"
    elif arquivo.endswith(".mp4"):
        pasta = "Videos"
    else:
        pasta = "Outros"

    # cria a pasta de destino se não existir
    pasta_destino = os.path.join(downloads, pasta)
    os.makedirs(pasta_destino, exist_ok=True)

    # move o arquivo
    caminho_destino = os.path.join(pasta_destino, arquivo)
    shutil.move(caminho_origem, caminho_destino)
    print(f"Movido: {arquivo} -> {pasta}")

print("Pronto! Sua pasta Downloads está organizada.")
