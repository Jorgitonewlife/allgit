# Renomeador em Massa de Fotos (Projeto Freela #2)

Script que renomeia arquivos em lote, adicionando prefixo personalizado.

Exemplo:
- `foto_01.jpg` → `viagem_2026_foto_01.jpg`
- `foto_02.jpg` → `viagem_2026_foto_02.jpg`
- `foto_03.png` → `viagem_2026_foto_03.png`

## Como usar

1. Abra o terminal no VS Code (`Ctrl + \``).
2. Navegue até a pasta do projeto:

   ```bash
   cd renomeador
   ```

3. Rode o script:

   ```bash
   python passo3_renomear.py
   ```

4. Digite o prefixo desejado (ex: `viagem_2026_`).
5. Confira a pré-visualização e digite `s` para confirmar a renomeação.

## O que aprendi fazendo isso

- `os.listdir()` — lista arquivos de uma pasta.
- `os.path.join()` — monta caminhos de arquivo de forma segura.
- `os.path.dirname(__file__)` — encontra a pasta do próprio script.
- `input()` — recebe texto do usuário durante a execução.
- `os.rename()` — renomeia arquivos de verdade.
- Confirmação antes de alterar arquivos (boa prática para não estragar nada por engano).

## Blocos concluídos

- [x] Bloco 1: listar arquivos de uma pasta (`passo1_listar.py`)
- [x] Bloco 2: pré-visualizar novo nome com prefixo (`passo2_prefixo_sufixo.py`)
- [x] Bloco 3: renomear de verdade com confirmação (`passo3_renomear.py`)
- [x] Bloco 4: README completo (este arquivo)
