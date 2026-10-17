# Conversor de PDF para Texto (Projeto Freela #4)

Extrai texto de arquivos PDF e salva em arquivos `.txt`, um por PDF.

## Como usar

1. Abra o terminal no VS Code (`Ctrl + \``).
2. Navegue até a pasta do projeto:

   ```bash
   cd conversor_pdf
   ```

3. Se for a primeira vez, gere um PDF de exemplo para testar:

   ```bash
   python gerar_pdf_exemplo.py
   ```

4. Liste os PDFs encontrados:

   ```bash
   python passo1_listar_pdfs.py
   ```

5. Extraia o texto de um PDF específico:

   ```bash
   python passo2_extrair_texto.py
   ```

6. Converta todos os PDFs da pasta para `.txt`:

   ```bash
   python passo3_converter_todos.py
   ```

7. Confira na pasta `txt_gerados/` — deve ter um arquivo `.txt` por PDF.

## O que aprendi fazendo isso

- `pypdf.PdfReader` — abrir e ler arquivos PDF.
- `reader.pages` — acessar páginas individuais.
- `pagina.extract_text()` — extrair texto de cada página.
- `os.makedirs()` — criar pasta de saída se não existir.
- `open(caminho, "w", encoding="utf-8")` — salvar texto em arquivo `.txt`.

## Blocos concluídos

- [x] Bloco 1: listar PDFs em uma pasta (`passo1_listar_pdfs.py`)
- [x] Bloco 2: extrair texto de um PDF (`passo2_extrair_texto.py`)
- [x] Bloco 3: converter todos os PDFs para `.txt` (`passo3_converter_todos.py`)
- [x] Bloco 4: README completo (este arquivo)

## Próximo passo sugerido

Adicionar conversão em lote com barra de progresso, ou gerar um único `.txt` com todo o texto de vários PDFs concatenados.
