# Bloco 1: listar arquivos de uma pasta

import os

# Pasta de exemplo dentro do projeto (não mexe nas suas coisas pessoais)
# __file__ é o caminho desse próprio script; dirname pega a pasta dele
pasta_script = os.path.dirname(__file__)
pasta_fotos = os.path.join(pasta_script, "fotos_exemplo")

# Lista tudo que está dentro
arquivos = os.listdir(pasta_fotos)

print(f"Encontrei {len(arquivos)} arquivo(s) na pasta fotos_exemplo:")
for nome in arquivos:
    print(f" - {nome}")
