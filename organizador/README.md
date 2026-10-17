# Organizador de Downloads (Projeto Freela #1)

Script que organiza a pasta Downloads separando arquivos por tipo:
- `.pdf` → Documentos
- `.jpg` → Imagens
- `.zip` → Compactados
- `.csv` → Planilhas
- `.mp4` → Vídeos
- resto → Outros

## Como usar

1. Abra o terminal no VS Code (`Ctrl + \``).
2. Navegue até a pasta do projeto:

   ```bash
   cd organizador
   ```

3. Rode o script:

   ```bash
   python passo3_mover.py
   ```

4. Confira no Explorador de Arquivos se as pastas `Documentos`, `Imagens`, `Compactados`, `Planilhas`, `Videos` e `Outros` foram criadas dentro da sua `Downloads`.

## O que aprendi fazendo isso

- `import os` e `import shutil` — bibliotecas para trabalhar com arquivos e pastas.
- `os.path.expanduser("~")` — pega a pasta do usuário atual (funciona em qualquer PC Windows).
- `os.listdir()` — lista tudo que está dentro de uma pasta.
- `os.path.isfile()` — descobre se é arquivo (ignora pastas).
- `if / elif / else` — escolhe a pasta de destino com base na extensão do arquivo.
- `endswith()` — verifica se o nome termina com determinada extensão.
- `os.makedirs()` — cria a pasta de destino se ela ainda não existir.
- `shutil.move()` — move o arquivo fisicamente para a nova pasta.

## Bloco 4 — checklist de conclusão

- [x] Script funcional (`passo3_mover.py`)
- [x] README completo (este arquivo)
- [ ] Teste simples (`verificar_organizacao.py`) — confere se as pastas foram criadas
- [ ] Vídeo/demo — grava sua tela rodando o script (ótimo para portfólio)
