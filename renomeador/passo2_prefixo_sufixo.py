# Bloco 2: adicionar prefixo/sufixo no nome (SÓ MOSTRA, não renomeia ainda)

import os

pasta_script = os.path.dirname(__file__)
pasta_fotos = os.path.join(pasta_script, "fotos_exemplo")

arquivos = os.listdir(pasta_fotos)

# Pede o prefixo ao usuário
prefixo = input("Digite o prefixo que quer adicionar (ex: viagem_): ")

print("\nComo ficariam os nomes (apenas pré-visualização):")
for nome in arquivos:
    novo_nome = prefixo + nome
    print(f"  {nome}  →  {novo_nome}")

print("\nAperte Enter para sair.")
input()
