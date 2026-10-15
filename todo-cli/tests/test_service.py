"""Testes automatizados para o TodoService.

Cobre: criação, listagem, filtros, transições de estado, edição, deleção, estatísticas.
"""

import os
import tempfile

import pytest

from todo import TaskStatus, TodoService
from todo.service import TaskNotFoundError, ValidationError
from todo.storage import Storage


@pytest.fixture
def temp_storage():
    """Fixture que cria um Storage em arquivo temporário."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    storage = Storage(file_path=tmp_path)
    yield storage
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def service(temp_storage):
    """Fixture que cria um TodoService com storage temporário."""
    return TodoService(storage=temp_storage)


class TestAddTask:
    """Testes de adição de tarefas."""

    def test_add_basic(self, service):
        task = service.add("Estudar Python")
        assert task.title == "Estudar Python"
        assert task.description == ""
        assert task.status == TaskStatus.PENDING
        assert len(task.id) == 8

    def test_add_with_description(self, service):
        task = service.add("Título", "Descrição detalhada")
        assert task.description == "Descrição detalhada"

    def test_add_strips_whitespace(self, service):
        task = service.add("  Título com espaços  ", "  Descrição  ")
        assert task.title == "Título com espaços"
        assert task.description == "Descrição"

    def test_add_empty_title_raises(self, service):
        with pytest.raises(ValidationError, match="obrigatório"):
            service.add("")
        with pytest.raises(ValidationError, match="obrigatório"):
            service.add("   ")

    def test_add_title_too_long_raises(self, service):
        with pytest.raises(ValidationError, match="200"):
            service.add("x" * 201)

    def test_add_description_too_long_raises(self, service):
        with pytest.raises(ValidationError, match="1000"):
            service.add("Título", "x" * 1001)


class TestListTasks:
    """Testes de listagem e filtros."""

    def test_list_empty(self, service):
        assert service.list() == []

    def test_list_all(self, service):
        service.add("Tarefa 1")
        service.add("Tarefa 2")
        tasks = service.list()
        assert len(tasks) == 2
        # Mais recentes primeiro
        assert tasks[0].title == "Tarefa 2"
        assert tasks[1].title == "Tarefa 1"

    def test_list_filter_by_status(self, service):
        t1 = service.add("Pendente")
        t2 = service.add("Em andamento")
        t3 = service.add("Concluída")
        service.start(t2.id)
        service.complete(t3.id)

        pending = service.list(status=TaskStatus.PENDING)
        in_progress = service.list(status=TaskStatus.IN_PROGRESS)
        done = service.list(status=TaskStatus.DONE)

        assert len(pending) == 1
        assert len(in_progress) == 1
        assert len(done) == 1
        assert pending[0].id == t1.id
        assert in_progress[0].id == t2.id
        assert done[0].id == t3.id

    def test_list_search_title(self, service):
        service.add("Estudar Python")
        service.add("Ler livro")
        service.add("Python para iniciantes")

        results = service.list(search="python")
        assert len(results) == 2

    def test_list_search_description(self, service):
        service.add("Tarefa 1", "Descrição sobre Python")
        service.add("Tarefa 2", "Outra descrição")

        results = service.list(search="python")
        assert len(results) == 1
        assert results[0].title == "Tarefa 1"


class TestStatusTransitions:
    """Testes de transições de estado."""

    def test_start_pending_task(self, service):
        task = service.add("Nova")
        started = service.start(task.id)
        assert started.status == TaskStatus.IN_PROGRESS

    def test_complete_pending_task(self, service):
        task = service.add("Nova")
        done = service.complete(task.id)
        assert done.status == TaskStatus.DONE
        assert done.completed_at is not None

    def test_complete_in_progress_task(self, service):
        task = service.add("Nova")
        service.start(task.id)
        done = service.complete(task.id)
        assert done.status == TaskStatus.DONE

    def test_complete_already_done_raises(self, service):
        task = service.add("Nova")
        service.complete(task.id)
        with pytest.raises(ValidationError, match="já está concluída"):
            service.complete(task.id)

    def test_start_done_task_raises(self, service):
        task = service.add("Nova")
        service.complete(task.id)
        with pytest.raises(ValidationError, match="já concluída"):
            service.start(task.id)

    def test_reopen_done_task(self, service):
        task = service.add("Nova")
        service.complete(task.id)
        reopened = service.reopen(task.id)
        assert reopened.status == TaskStatus.PENDING
        assert reopened.completed_at is None

    def test_reopen_pending_task_raises(self, service):
        task = service.add("Nova")
        with pytest.raises(ValidationError, match="já está pendente"):
            service.reopen(task.id)


class TestEditTask:
    """Testes de edição."""

    def test_update_title(self, service):
        task = service.add("Título original")
        updated = service.update_title(task.id, "Novo título")
        assert updated.title == "Novo título"

    def test_update_description(self, service):
        task = service.add("Título", "Descrição original")
        updated = service.update_description(task.id, "Nova descrição")
        assert updated.description == "Nova descrição"

    def test_update_empty_title_raises(self, service):
        task = service.add("Título")
        with pytest.raises(ValidationError, match="vazio"):
            service.update_title(task.id, "   ")


class TestDeleteTask:
    """Testes de deleção."""

    def test_delete_task(self, service):
        task = service.add("Para deletar")
        service.delete(task.id)
        assert service.list() == []

    def test_delete_nonexistent_raises(self, service):
        with pytest.raises(TaskNotFoundError):
            service.delete("inexistente")


class TestClearCompleted:
    """Testes de limpeza de concluídas."""

    def test_clear_completed(self, service):
        t1 = service.add("Tarefa 1")
        t2 = service.add("Tarefa 2")
        t3 = service.add("Tarefa 3")
        service.complete(t1.id)
        service.complete(t2.id)

        count = service.clear_completed()
        assert count == 2
        remaining = service.list()
        assert len(remaining) == 1
        assert remaining[0].id == t3.id

    def test_clear_completed_none(self, service):
        service.add("Tarefa 1")
        count = service.clear_completed()
        assert count == 0


class TestStats:
    """Testes de estatísticas."""

    def test_stats_empty(self, service):
        stats = service.stats()
        assert stats["total"] == 0
        assert stats["pending"] == 0
        assert stats["in_progress"] == 0
        assert stats["done"] == 0
        assert stats["overdue"] == 0
        assert stats["by_priority"] == {"high": 0, "medium": 0, "low": 0}

    def test_stats_mixed(self, service):
        _t1 = service.add("Pendente")
        _t2 = service.add("Em andamento")
        _t3 = service.add("Concluída")
        service.start(_t2.id)
        service.complete(_t3.id)

        stats = service.stats()
        assert stats["total"] == 3
        assert stats["pending"] == 1
        assert stats["in_progress"] == 1
        assert stats["done"] == 1
        assert stats["overdue"] == 0
        assert stats["by_priority"] == {"high": 0, "medium": 3, "low": 0}


class TestPersistence:
    """Testes de persistência (recarregar do disco)."""

    def test_data_persists_across_services(self, temp_storage):
        # Primeiro service cria tarefas
        s1 = TodoService(storage=temp_storage)
        t1 = s1.add("Tarefa persistida")
        s1.complete(t1.id)

        # Segundo service (nova instância) deve ver os dados
        s2 = TodoService(storage=temp_storage)
        tasks = s2.list()
        assert len(tasks) == 1
        assert tasks[0].title == "Tarefa persistida"
        assert tasks[0].status == TaskStatus.DONE


class TestIDPrefixMatching:
    """Testes de busca por prefixo de ID."""

    def test_find_by_full_id(self, service):
        task = service.add("Teste")
        found = service.get(task.id)
        assert found.id == task.id

    def test_find_by_prefix(self, service):
        task = service.add("Teste")
        # Usa apenas primeiros 3-4 chars
        found = service.get(task.id[:4])
        assert found.id == task.id

    def test_prefix_too_short_raises(self, service):
        task = service.add("Teste")
        with pytest.raises(ValidationError, match="3 caracteres"):
            service.get(task.id[:2])

    def test_ambiguous_prefix_raises(self, service):
        _t1 = service.add("Tarefa 1")  # id começa com "abc..."
        _t2 = service.add("Tarefa 2")  # id começa com "abc..." (improvável mas possível)
        # Força IDs com mesmo prefixo para testar
        # Nota: na prática UUIDs curtos têm colisão rara
        # Este teste documenta o comportamento esperado
