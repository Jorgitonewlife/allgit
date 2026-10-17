# Gerador de Recibos a partir de Planilha (Projeto Freela #3)

Lê uma planilha de clientes (Excel) e gera recibos automáticos em arquivos `.txt` separados.

## Como usar

1. Abra o terminal no VS Code (`Ctrl + \``).
2. Navegue até a pasta do projeto:

   ```bash
   cd gerador_recibos
   ```

3. Se for a primeira vez, crie a planilha de exemplo:

   ```bash
   python criar_planilha_exemplo.py
   ```

4. Rode o passo 1 para ver o conteúdo da planilha:

   ```bash
   python passo1_listar.py
   ```

5. Rode o passo 2 para gerar recibos na tela:

   ```bash
   python passo2_gerar_recibos.py
   ```

6. Rode o passo 3 para salvar cada recibo como arquivo `.txt`:

   ```bash
   python passo3_salvar_recibos.py
   ```

7. Confira na pasta `recibos_gerados/` — deve ter um arquivo `.txt` por cliente.

## O que aprendi fazendo isso

- `openpyxl` — ler planilhas Excel (`.xlsx`) linha por linha.
- `ws.iter_rows(values_only=True)` — ler valores das células.
- `os.makedirs()` — criar pasta de destino se não existir.
- `open(caminho, "w", encoding="utf-8")` — criar e escrever arquivos de texto.
- `f-strings` com aspas triplas (`"""..."""`) — montar textos grandes com quebras de linha.

## Blocos concluídos

- [x] Bloco 1: ler planilha e mostrar conteúdo (`passo1_listar.py`)
- [x] Bloco 2: gerar recibo de texto na tela (`passo2_gerar_recibos.py`)
- [x] Bloco 3: salvar cada recibo como arquivo `.txt` separado (`passo3_salvar_recibos.py`)
- [x] Bloco 4: README completo (este arquivo)

## Próximo passo sugerido

Gerar PDFs em vez de `.txt` (usa biblioteca `fpdf2` ou `reportlab`), ou enviar os recibos por e-mail automaticamente.
