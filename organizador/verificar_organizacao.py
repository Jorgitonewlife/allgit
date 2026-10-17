# Verificação simples da organização
# Executa depois do passo3_mover.py para conferir se tudo foi movido corretamente.

import os

downloads = os.path.join(os.path.expanduser("~"), "Downloads")

pastas_esperadas = ["Documentos", "Imagens", "Compactados", "Planilhas", "Videos", "Outros"]

print("Verificando se as pastas foram criadas...\n")

for pasta in pastas_esperadas:
    caminho_pasta = os.path.join(downloads, pasta)
    if os.path.isdir(caminho_pasta):
        arquivos = os.listdir(caminho_pasta)
        print(f"{pasta}/ -> {len(arquivos)} arquivo(s):")
        for a in arquivos[:5]:  # mostra só os 5 primeiros de cada
            print(f"    - {a}")
        if len(arquivos) > 5:
            print(f"    ... e mais {len(arquivos) - 5}")
    else:
        print(f"{pasta}/ -> NAO FOI CRIADA")

print("\nVerificacao concluida!")
