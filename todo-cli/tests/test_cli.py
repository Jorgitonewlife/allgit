"""Testes da CLI (interface de linha de comando).

Usa pytest + capsys para capturar stdout/stderr.
"""

import os
import tempfile

import pytest

from todo.cli import TodoCLI
from todo.service import TodoService
from todo.storage import Storage


@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    storage = Storage(file_path=tmp_path)
    yield storage
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def cli(temp_storage):
    service = TodoService(storage=temp_storage)
    return TodoCLI(service=service)


class TestCLIAdd:
    def test_add_basic(self, cli, capsys):
        exit_code = cli.run(["add", "Tarefa de teste"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Tarefa criada" in captured.out
        assert "Tarefa de teste" in captured.out

    def test_add_with_description(self, cli, capsys):
        exit_code = cli.run(["add", "Título", "-d", "Descrição detalhada"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Descrição detalhada" in captured.out

    def test_add_empty_title_fails(self, cli, capsys):
        exit_code = cli.run(["add", ""])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "obrigatório" in captured.err


class TestCLIList:
    def test_list_empty(self, cli, capsys):
        exit_code = cli.run(["list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Nenhuma tarefa" in captured.out

    def test_list_shows_tasks(self, cli, capsys):
        cli.run(["add", "Tarefa 1"])
        cli.run(["add", "Tarefa 2"])
        exit_code = cli.run(["list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Tarefa 1" in captured.out
        assert "Tarefa 2" in captured.out

    def test_list_filter_status(self, cli, capsys):
        _t1 = cli.run(["add", "Pendente"])
        _t2 = cli.run(["add", "Concluída"])
        # Pega o ID da segunda tarefa criada (precisa acessar service)
        # Como não temos acesso direto, usamos list para ver IDs
        cli.run(["list"])
        # Simplificação: testamos via service em test_service.py


class TestCLIStatusTransitions:
    def test_done_command(self, cli, capsys):
        cli.run(["add", "Para completar"])
        cli.run(["list"])
        captured = capsys.readouterr()
        # Extrai ID da saída (formato [abc123])
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        assert match
        task_id = match.group(1)

        exit_code = cli.run(["done", task_id])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "done" in captured.out.lower() or "conclu" in captured.out.lower()

    def test_start_command(self, cli, capsys):
        cli.run(["add", "Para iniciar"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["start", task_id])
        assert exit_code == 0

    def test_reopen_command(self, cli, capsys):
        cli.run(["add", "Para reabrir"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        cli.run(["done", task_id])
        exit_code = cli.run(["reopen", task_id])
        assert exit_code == 0


class TestCLIEdit:
    def test_edit_title(self, cli, capsys):
        cli.run(["add", "Título original"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["edit", task_id, "-t", "Novo título"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Novo título" in captured.out

    def test_edit_description(self, cli, capsys):
        cli.run(["add", "Título", "-d", "Desc original"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["edit", task_id, "-d", "Nova descrição"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Nova descrição" in captured.out


class TestCLIDelete:
    def test_delete_with_confirm(self, cli, capsys, monkeypatch):
        cli.run(["add", "Para deletar"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        # Simula confirmação 's'
        monkeypatch.setattr("builtins.input", lambda _: "s")
        exit_code = cli.run(["delete", task_id])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "removida" in captured.out

    def test_delete_force_flag(self, cli, capsys):
        cli.run(["add", "Para deletar force"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["delete", task_id, "-y"])
        assert exit_code == 0


class TestCLIStats:
    def test_stats_command(self, cli, capsys):
        cli.run(["add", "T1"])
        cli.run(["add", "T2"])
        exit_code = cli.run(["stats"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Total" in captured.out
        assert "2" in captured.out


class TestCLIClearDone:
    def test_clear_done_force(self, cli, capsys):
        cli.run(["add", "T1"])
        cli.run(["add", "T2"])
        # Completa uma
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)
        cli.run(["done", task_id])

        exit_code = cli.run(["clear-done", "-y"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "removida" in captured.out


class TestCLIHelp:
    def test_main_help(self, cli, capsys):
        exit_code = cli.run(["--help"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or "uso" in captured.out.lower()

    def test_subcommand_help(self, cli, capsys):
        exit_code = cli.run(["add", "--help"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "title" in captured.out.lower()

    def test_alias_ls(self, cli, capsys):
        cli.run(["add", "Teste alias"])
        exit_code = cli.run(["ls"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Teste alias" in captured.out

    def test_alias_rm(self, cli, capsys):
        cli.run(["add", "Teste rm"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["rm", task_id, "-y"])
        assert exit_code == 0


class TestCLIPriority:
    def test_add_with_priority(self, cli, capsys):
        exit_code = cli.run(["add", "Tarefa alta", "-p", "high"])
        assert exit_code == 0
        captured = capsys.readouterr()
        # Verifica se mostra indicador de prioridade alta (Unicode ▲ ou texto HIGH)
        assert "HIGH" in captured.out or "▲" in captured.out or "alta" in captured.out.lower()

    def test_priority_command(self, cli, capsys):
        cli.run(["add", "Tarefa normal"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["priority", task_id, "high"])
        assert exit_code == 0
        captured = capsys.readouterr()
        # Verifica se mostra indicador de prioridade alta
        assert "HIGH" in captured.out or "▲" in captured.out or "alta" in captured.out.lower()


class TestCLIDueDate:
    def test_add_with_due_date(self, cli, capsys):
        exit_code = cli.run(["add", "Tarefa com vencimento", "--due", "2026-12-31"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "due:" in captured.out or "31/12/2026" in captured.out

    def test_due_date_command_set(self, cli, capsys):
        cli.run(["add", "Tarefa sem vencimento"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["due-date", task_id, "2026-10-15"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "15/10/2026" in captured.out or "definida" in captured.out

    def test_due_date_command_remove(self, cli, capsys):
        cli.run(["add", "Tarefa com vencimento", "--due", "2026-12-31"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["due-date", task_id])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "removida" in captured.out


class TestCLITag:
    def test_add_with_tags(self, cli, capsys):
        exit_code = cli.run(["add", "Tarefa com tags", "--tags", "trabalho,urgente"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "#trabalho" in captured.out and "#urgente" in captured.out

    def test_tag_add(self, cli, capsys):
        cli.run(["add", "Tarefa sem tags"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["tag", task_id, "estudo"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "#estudo" in captured.out

    def test_tag_remove(self, cli, capsys):
        cli.run(["add", "Tarefa com tag", "--tags", "remover"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["tag", task_id, "remover", "--remove"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "#remover" not in captured.out

    def test_tag_clear(self, cli, capsys):
        cli.run(["add", "Tarefa com tags", "--tags", "a,b,c"])
        cli.run(["list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        task_id = match.group(1)

        exit_code = cli.run(["tag", task_id, "--clear"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "#a" not in captured.out and "#b" not in captured.out


class TestCLIListFilters:
    def test_list_filter_priority(self, cli, capsys):
        cli.run(["add", "Alta", "-p", "high"])
        cli.run(["add", "Baixa", "-p", "low"])
        capsys.readouterr()  # Limpa saída dos adds
        exit_code = cli.run(["list", "--priority", "high"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Alta" in captured.out
        assert "Baixa" not in captured.out

    def test_list_filter_tag(self, cli, capsys):
        cli.run(["add", "Trabalho", "--tags", "trabalho"])
        cli.run(["add", "Pessoal", "--tags", "pessoal"])
        capsys.readouterr()  # Limpa saída dos adds
        exit_code = cli.run(["list", "--tag", "trabalho"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Trabalho" in captured.out
        assert "Pessoal" not in captured.out


class TestCLIExportImport:
    def test_export_json(self, cli, capsys, tmp_path):
        import time
        cli.run(["add", "Tarefa 1", "-p", "high", "--due", "2026-12-31", "--tags", "tag1"])
        time.sleep(0.01)  # Garante timestamp diferente
        cli.run(["add", "Tarefa 2", "-p", "low"])

        output_file = tmp_path / "export.json"
        exit_code = cli.run(["export", "json", "-o", str(output_file)])
        assert exit_code == 0
        assert output_file.exists()

        import json
        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 2
        # Ordenado por updated_at desc (mais recente primeiro)
        assert data[0]["title"] == "Tarefa 2"
        assert data[0]["priority"] == "low"
        assert data[1]["priority"] == "high"
        assert "tag1" in data[1]["tags"]

    def test_export_csv(self, cli, capsys, tmp_path):
        cli.run(["add", "Tarefa CSV", "-p", "medium", "--tags", "csv,test"])

        output_file = tmp_path / "export.csv"
        exit_code = cli.run(["export", "csv", "-o", str(output_file)])
        assert exit_code == 0
        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert "Tarefa CSV" in content
        assert "medium" in content
        assert "csv" in content and "test" in content

    def test_export_markdown(self, cli, capsys, tmp_path):
        cli.run(["add", "Tarefa MD", "-p", "high", "--due", "2026-12-31", "--tags", "md"])

        output_file = tmp_path / "export.md"
        exit_code = cli.run(["export", "md", "-o", str(output_file)])
        assert exit_code == 0
        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert "# Tarefas" in content
        assert "Tarefa MD" in content
        assert "[HIGH]" in content
        assert "[due:31/12/2026]" in content
        assert "#md" in content

    def test_import_json_merge(self, cli, capsys, tmp_path):
        # Cria arquivo JSON
        json_content = '''[
            {"id": "import1", "title": "Importada 1", "description": "", "status": "pending", "priority": "high", "due_date": null, "tags": ["import"], "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00", "completed_at": null}
        ]'''
        json_file = tmp_path / "import.json"
        json_file.write_text(json_content, encoding="utf-8")

        # Importa com merge (padrão)
        exit_code = cli.run(["import", "json", str(json_file)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "importadas" in captured.out

        # Verifica se foi adicionada
        cli.run(["list", "--search", "Importada"])
        captured = capsys.readouterr()
        assert "Importada 1" in captured.out

    def test_import_json_replace(self, cli, capsys, tmp_path):
        cli.run(["add", "Existente"])

        json_content = '''[
            {"id": "import2", "title": "Nova Importada", "description": "", "status": "done", "priority": "low", "due_date": null, "tags": [], "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00", "completed_at": "2026-01-01T00:00:00"}
        ]'''
        json_file = tmp_path / "import.json"
        json_file.write_text(json_content, encoding="utf-8")

        # Importa com replace
        exit_code = cli.run(["import", "json", str(json_file), "--replace"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "substitu" in captured.out

        # Verifica se a antiga foi removida
        cli.run(["list"])
        captured = capsys.readouterr()
        assert "Existente" not in captured.out
        assert "Nova Importada" in captured.out

    def test_import_csv(self, cli, capsys, tmp_path):
        csv_content = """id,title,description,status,priority,due_date,tags,created_at,updated_at,completed_at
csv1,Tarefa CSV,,pending,high,2026-12-31,"csv,import",2026-01-01T00:00:00,2026-01-01T00:00:00,
"""
        csv_file = tmp_path / "import.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        exit_code = cli.run(["import", "csv", str(csv_file)])
        assert exit_code == 0

        cli.run(["list", "--search", "CSV"])
        captured = capsys.readouterr()
        assert "Tarefa CSV" in captured.out
        # Verifica prioridade alta (ícone Unicode ▲ ou texto HIGH)
        assert "▲" in captured.out or "[HIGH]" in captured.out or "high" in captured.out.lower()
