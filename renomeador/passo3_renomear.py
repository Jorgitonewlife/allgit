# Bloco 3: renomear de verdade com os.rename()

import os

pasta_script = os.path.dirname(__file__)
pasta_fotos = os.path.join(pasta_script, "fotos_exemplo")

arquivos = os.listdir(pasta_fotos)

# Pede o prefixo ao usuário
prefixo = input("Digite o prefixo que quer adicionar (ex: viagem_): ")

print("\nComo ficariam os nomes:")
mudancas = []
for nome in arquivos:
    novo_nome = prefixo + nome
    print(f"  {nome}  →  {novo_nome}")
    mudancas.append((nome, novo_nome))

# Confirmação antes de mexer de verdade
resposta = input("\nDeseja renomear de verdade? (s/n): ").strip().lower()

if resposta == "s":
    for nome_antigo, nome_novo in mudancas:
        caminho_antigo = os.path.join(pasta_fotos, nome_antigo)
        caminho_novo = os.path.join(pasta_fotos, nome_novo)
        os.rename(caminho_antigo, caminho_novo)
        print(f"Renomeado: {nome_antigo} → {nome_novo}")
    print("\nPronto! Todos os arquivos foram renomeados.")
else:
    print("\nNenhum arquivo foi alterado.")
