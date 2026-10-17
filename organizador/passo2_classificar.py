# Bloco 2: descobrir o tipo de cada arquivo (if / elif / else)
# Conceitos novos: endswith(), if, elif, else

# --- Mini-aula ---
# nome.endswith(".pdf") responde True/False se o nome termina com .pdf
# O if escolhe o caminho conforme a resposta:

arquivo = "foto-viagem.jpg"

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

print(f"{arquivo} -> {pasta}")  # foto-viagem.jpg -> Imagens

# Regras do if:
# - if / elif / else terminam com DOIS PONTOS (:)
# - o bloco de dentro tem 4 espaços de indentação
# - o elif pode repetir quantas vezes quiser; o else é opcional


# ============================================================
# SUA TAREFA
# ============================================================
# 1. Rode este arquivo e confirme que imprime "foto-viagem.jpg -> Imagens".
# 2. Adicione elif para: .zip -> "Compactados", .csv -> "Planilhas",
#    .mp4 -> "Videos".
# 3. Troque a variável 'arquivo' para "relatorio.pdf" e confira
#    se imprime "relatorio.pdf -> Documentos".
# 4. Desafio: troque para "musica.mp3" — o que acontece? Por quê?
