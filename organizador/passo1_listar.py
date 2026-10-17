# Bloco 1: listar arquivos da pasta Downloads
# Conceitos novos: import os, os.listdir(), os.path.join()

import os

# Pasta Downloads do usuário atual (funciona em qualquer PC Windows)
downloads = os.path.join(os.path.expanduser("~"), "Downloads")

# Lista tudo que está lá dentro
arquivos = os.listdir(downloads)
total = len(arquivos)
for nome in arquivos[:10]:  # mostra só os 10 primeiros
    print(f" - {nome}")

print(f"Encontrei {len(arquivos)} itens na pasta Downloads:")

print(f"Total de itens: {total}")

# ============================================================
# SUA TAREFA (usa só o que você já viu na aula 2 + len())
# ============================================================
# 1. Rode este arquivo (Ctrl+Shift+B) e me diga quantos itens
#    apareceram.
# 2. Desafio: crie uma variável 'total' com len(arquivos) e
#    imprima "Total de itens: <total>" com f-string.
