"""Testes da CLI do módulo CRM.

Usa pytest + capsys para capturar stdout/stderr.
"""

import os
import tempfile
from pathlib import Path

import pytest

from todo.cli import TodoCLI
from todo.crm.service import CrmService
from todo.crm.storage import CrmStorage
from todo.service import TodoService
from todo.storage import Storage


@pytest.fixture
def temp_task_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    storage = Storage(file_path=tmp_path)
    yield storage
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def temp_crm_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    storage = CrmStorage(file_path=Path(tmp_path))
    yield storage
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def cli(temp_task_storage, temp_crm_storage):
    service = TodoService(storage=temp_task_storage)
    crm_service = CrmService(storage=temp_crm_storage)
    return TodoCLI(service=service, crm_service=crm_service)


class TestCLICrmCustomerAdd:
    def test_add_basic(self, cli, capsys):
        exit_code = cli.run(["crm", "customer", "add", "Acme Corp"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Cliente criado" in captured.out
        assert "Acme Corp" in captured.out

    def test_add_with_all_fields(self, cli, capsys):
        exit_code = cli.run([
            "crm", "customer", "add", "Acme",
            "--email", "a@a.com", "--phone", "1199",
            "--company", "Acme LTDA", "--notes", "Bom cliente",
        ])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Acme" in captured.out
        assert "a@a.com" in captured.out
        assert "Acme LTDA" in captured.out

    def test_add_with_status(self, cli, capsys):
        exit_code = cli.run(["crm", "customer", "add", "Ativo", "--status", "active"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "active" in captured.out

    def test_add_empty_name_fails(self, cli, capsys):
        exit_code = cli.run(["crm", "customer", "add", ""])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "obrigatório" in captured.err

    def test_add_invalid_email_fails(self, cli, capsys):
        exit_code = cli.run(["crm", "customer", "add", "Acme", "--email", "invalido"])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "Email" in captured.err


class TestCLICrmCustomerList:
    def test_list_empty(self, cli, capsys):
        exit_code = cli.run(["crm", "customer", "list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Nenhum cliente" in captured.out

    def test_list_shows_customers(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Cliente 1"])
        cli.run(["crm", "customer", "add", "Cliente 2"])
        exit_code = cli.run(["crm", "customer", "list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Cliente 1" in captured.out
        assert "Cliente 2" in captured.out

    def test_list_filter_status(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Lead 1", "--status", "lead"])
        cli.run(["crm", "customer", "add", "Ativo 1", "--status", "active"])
        capsys.readouterr()  # limpa saída dos adds

        exit_code = cli.run(["crm", "customer", "list", "--status", "active"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Ativo 1" in captured.out
        assert "Lead 1" not in captured.out


class TestCLICrmCustomerGet:
    def test_get_customer(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        assert match
        customer_id = match.group(1)

        exit_code = cli.run(["crm", "customer", "get", customer_id])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Acme" in captured.out

    def test_get_nonexistent(self, cli, capsys):
        exit_code = cli.run(["crm", "customer", "get", "naoexiste"])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "não encontrado" in captured.err


class TestCLICrmCustomerEdit:
    def test_edit_email(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        exit_code = cli.run(["crm", "customer", "edit", customer_id, "--email", "novo@acme.com"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "novo@acme.com" in captured.out


class TestCLICrmCustomerStatus:
    def test_set_status(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        exit_code = cli.run(["crm", "customer", "status", customer_id, "active"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "active" in captured.out


class TestCLICrmCustomerRm:
    def test_rm_with_confirm(self, cli, capsys, monkeypatch):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        monkeypatch.setattr("builtins.input", lambda _: "s")
        exit_code = cli.run(["crm", "customer", "rm", customer_id])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "removido" in captured.out

    def test_rm_force_flag(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        exit_code = cli.run(["crm", "customer", "rm", customer_id, "-y"])
        assert exit_code == 0

    def test_rm_blocked_with_deals(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        cli.run(["crm", "deal", "add", "Proposta", "--customer", customer_id, "--value", "100"])
        exit_code = cli.run(["crm", "customer", "rm", customer_id, "-y"])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "possui deals" in captured.err


class TestCLICrmDealAdd:
    def test_add_basic(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        exit_code = cli.run([
            "crm", "deal", "add", "Proposta site",
            "--customer", customer_id, "--value", "5000",
        ])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Deal criado" in captured.out
        assert "Proposta site" in captured.out
        assert "5,000" in captured.out

    def test_add_with_invalid_customer(self, cli, capsys):
        exit_code = cli.run([
            "crm", "deal", "add", "Proposta", "--customer", "inexistente", "--value", "100",
        ])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "não encontrado" in captured.err

    def test_add_negative_value_fails(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        exit_code = cli.run([
            "crm", "deal", "add", "Proposta", "--customer", customer_id, "--value", "-100",
        ])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "negativo" in captured.err


class TestCLICrmDealList:
    def test_list_empty(self, cli, capsys):
        exit_code = cli.run(["crm", "deal", "list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Nenhum deal" in captured.out

    def test_list_shows_deals(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        cli.run(["crm", "deal", "add", "Deal 1", "--customer", customer_id, "--value", "100"])
        cli.run(["crm", "deal", "add", "Deal 2", "--customer", customer_id, "--value", "200"])

        exit_code = cli.run(["crm", "deal", "list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Deal 1" in captured.out
        assert "Deal 2" in captured.out


class TestCLICrmDealStatus:
    def test_set_status_won(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        cli.run(["crm", "deal", "add", "Proposta", "--customer", customer_id, "--value", "100"])
        cli.run(["crm", "deal", "list"])
        captured = capsys.readouterr()
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        deal_id = match.group(1)

        exit_code = cli.run(["crm", "deal", "status", deal_id, "won"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "won" in captured.out
        assert "fechado" in captured.out


class TestCLICrmPipeline:
    def test_pipeline_empty(self, cli, capsys):
        exit_code = cli.run(["crm", "pipeline"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "PIPELINE" in captured.out
        assert "OPEN" in captured.out
        assert "WON" in captured.out

    def test_pipeline_with_deals(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        cli.run(["crm", "customer", "list"])
        captured = capsys.readouterr()
        import re
        match = re.search(r"\[([a-f0-9]{8})\]", captured.out)
        customer_id = match.group(1)

        cli.run(["crm", "deal", "add", "Open Deal", "--customer", customer_id, "--value", "100"])
        cli.run(["crm", "deal", "add", "Won Deal", "--customer", customer_id, "--value", "300"])

        # Marca um como won
        cli.run(["crm", "deal", "list"])
        captured = capsys.readouterr()
        matches = re.findall(r"\[([a-f0-9]{8})\]", captured.out)
        # O mais recente primeiro é o "Won Deal"
        cli.run(["crm", "deal", "status", matches[0], "won"])

        exit_code = cli.run(["crm", "pipeline"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "400" in captured.out  # total
        assert "300" in captured.out  # won


class TestCLICrmStats:
    def test_stats_command(self, cli, capsys):
        cli.run(["crm", "customer", "add", "Acme"])
        exit_code = cli.run(["crm", "crm", "stats"])  # will fail - wrong path
        # Actually should be crm stats not crm crm stats
        exit_code = cli.run(["crm", "stats"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "STATS" in captured.out
        assert "Clientes total" in captured.out


class TestCLICrmHelp:
    def test_crm_help(self, cli, capsys):
        exit_code = cli.run(["crm", "--help"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "customer" in captured.out
        assert "deal" in captured.out

    def test_crm_customer_help(self, cli, capsys):
        exit_code = cli.run(["crm", "customer", "--help"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "add" in captured.out
        assert "list" in captured.out

    def test_crm_deal_help(self, cli, capsys):
        exit_code = cli.run(["crm", "deal", "--help"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "add" in captured.out
        assert "status" in captured.out

    def test_crm_without_subcommand(self, cli, capsys):
        exit_code = cli.run(["crm"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "customer" in captured.out
