"""Camada de serviço: lógica de negócio e regras da aplicação.

Esta camada NÃO sabe como dados são salvos (Storage) nem como são exibidos (CLI).
Ela apenas coordena: valida entrada, aplica regras, chama storage.
"""

import uuid
from datetime import datetime

from .config import get_config
from .models import Task, TaskPriority, TaskStatus
from .storage import Storage


class ServiceError(Exception):
    """Exceção base para erros de regra de negócio."""
    pass


class TaskNotFoundError(ServiceError):
    """Lançada quando uma tarefa não é encontrada pelo ID."""
    pass


class ValidationError(ServiceError):
    """Lançada quando dados de entrada são inválidos."""
    pass


class TodoService:
    """Orquestra operações de todo: criar, listar, atualizar, deletar.

    Responsabilidades:
    - Validar dados de entrada (tamanho, obrigatoriedade)
    - Aplicar regras de negócio (ex: não pode concluir tarefa já concluída)
    - Delegar persistência ao Storage
    - Retornar objetos de domínio (Task) ou levantar exceções claras
    """

    def __init__(self, storage: Storage | None = None):
        """Inicializa o service com um storage (injeção de dependência).

        Args:
            storage: Instância de Storage. Se None, cria uma usando config.
        """
        if storage is None:
            config = get_config()
            storage = Storage(file_path=config.get_storage_path())
        self._storage = storage
        # Cache em memória para evitar ler disco a cada operação
        self._tasks: list[Task] = []
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Carrega tarefas do disco se ainda não carregou (lazy loading)."""
        if not self._loaded:
            self._tasks = self._storage.load()
            self._loaded = True

    def _persist(self) -> None:
        """Salva o estado atual no disco."""
        self._storage.save(self._tasks)

    def _find_by_id(self, task_id: str) -> Task:
        """Busca tarefa por ID (case-insensitive para os 8 primeiros chars).

        Args:
            task_id: ID completo ou prefixo (mínimo 3 chars).

        Returns:
            Task encontrada.

        Raises:
            TaskNotFoundError: Se não encontrar ou ID ambíguo.
        """
        if len(task_id) < 3:
            raise ValidationError("ID deve ter pelo menos 3 caracteres")

        matches = [t for t in self._tasks if t.id.startswith(task_id.lower())]

        if not matches:
            raise TaskNotFoundError(f"Tarefa '{task_id}' não encontrada")
        if len(matches) > 1:
            raise TaskNotFoundError(
                f"ID '{task_id}' é ambíguo (encontradas {len(matches)} tarefas). "
                "Use mais caracteres."
            )
        return matches[0]

    # ===== OPERAÇÕES PÚBLICAS =====

    def add(self, title: str, description: str = "", priority: TaskPriority = TaskPriority.MEDIUM, due_date: datetime | None = None, tags: list[str] | None = None) -> Task:
        """Cria uma nova tarefa.

        Args:
            title: Título obrigatório (1-200 chars).
            description: Descrição opcional (máx 1000 chars).
            priority: Prioridade da tarefa (padrão: MEDIUM).
            due_date: Data de vencimento opcional.
            tags: Lista de tags opcional.

        Returns:
            Task criada.

        Raises:
            ValidationError: Se título vazio ou muito longo.
        """
        self._ensure_loaded()

        title = title.strip()
        if not title:
            raise ValidationError("Título é obrigatório")
        if len(title) > 200:
            raise ValidationError("Título deve ter no máximo 200 caracteres")

        description = description.strip()
        if len(description) > 1000:
            raise ValidationError("Descrição deve ter no máximo 1000 caracteres")

        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags or [],
        )
        self._tasks.append(task)
        self._persist()
        return task

    def list(
        self,
        status: TaskStatus | None = None,
        search: str | None = None,
        priority: TaskPriority | None = None,
        tag: str | None = None,
        overdue: bool | None = None,
    ) -> list[Task]:
        """Lista tarefas com filtros opcionais.

        Args:
            status: Filtrar por status (PENDING, IN_PROGRESS, DONE).
            search: Busca textual no título e descrição (case-insensitive).
            priority: Filtrar por prioridade (LOW, MEDIUM, HIGH).
            tag: Filtrar por tag (case-insensitive).
            overdue: Filtrar tarefas vencidas (True) ou não vencidas (False).

        Returns:
            Lista de tarefas filtradas (mais recentes primeiro).
        """
        self._ensure_loaded()

        tasks = self._tasks

        if status:
            tasks = [t for t in tasks if t.status == status]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        if tag:
            tag_lower = tag.lower().replace(" ", "-")
            tasks = [t for t in tasks if tag_lower in t.tags]

        if overdue is not None:
            now = datetime.now()
            if overdue:
                tasks = [t for t in tasks if t.due_date and t.due_date < now and t.status != TaskStatus.DONE]
            else:
                tasks = [t for t in tasks if not t.due_date or t.due_date >= now or t.status == TaskStatus.DONE]

        if search:
            search_lower = search.lower()
            tasks = [
                t for t in tasks
                if search_lower in t.title.lower() or search_lower in t.description.lower()
            ]

        # Ordena: mais recentemente atualizadas primeiro
        tasks.sort(key=lambda t: t.updated_at, reverse=True)
        return tasks

    def get(self, task_id: str) -> Task:
        """Obtém uma tarefa pelo ID."""
        self._ensure_loaded()
        return self._find_by_id(task_id)

    def update_title(self, task_id: str, new_title: str) -> Task:
        """Atualiza o título de uma tarefa."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)
        try:
            task.update_title(new_title)
        except ValueError as e:
            raise ValidationError(str(e)) from e
        self._persist()
        return task

    def update_description(self, task_id: str, new_description: str) -> Task:
        """Atualiza a descrição de uma tarefa."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)
        task.update_description(new_description)
        self._persist()
        return task

    def set_priority(self, task_id: str, priority: TaskPriority) -> Task:
        """Define a prioridade de uma tarefa."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)
        task.set_priority(priority)
        self._persist()
        return task

    def set_due_date(self, task_id: str, due_date: datetime | None) -> Task:
        """Define a data de vencimento de uma tarefa (None para remover)."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)
        task.set_due_date(due_date)
        self._persist()
        return task

    def add_tag(self, task_id: str, tag: str) -> Task:
        """Adiciona uma tag a uma tarefa."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)
        task.add_tag(tag)
        self._persist()
        return task

    def remove_tag(self, task_id: str, tag: str) -> Task:
        """Remove uma tag de uma tarefa."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)
        task.remove_tag(tag)
        self._persist()
        return task

    def clear_tags(self, task_id: str) -> Task:
        """Remove todas as tags de uma tarefa."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)
        task.clear_tags()
        self._persist()
        return task

    def start(self, task_id: str) -> Task:
        """Marca tarefa como 'em andamento'."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)

        if task.status == TaskStatus.DONE:
            raise ValidationError("Não pode iniciar tarefa já concluída. Use 'reabrir'.")

        task.mark_in_progress()
        self._persist()
        return task

    def complete(self, task_id: str) -> Task:
        """Marca tarefa como 'concluída'."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)

        if task.status == TaskStatus.DONE:
            raise ValidationError("Tarefa já está concluída")

        task.mark_done()
        self._persist()
        return task

    def reopen(self, task_id: str) -> Task:
        """Reabre tarefa concluída (volta para 'pendente')."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)

        if task.status == TaskStatus.PENDING:
            raise ValidationError("Tarefa já está pendente")

        task.mark_pending()
        self._persist()
        return task

    def delete(self, task_id: str) -> None:
        """Remove uma tarefa permanentemente."""
        self._ensure_loaded()
        task = self._find_by_id(task_id)
        self._tasks.remove(task)
        self._persist()

    def clear_completed(self) -> int:
        """Remove todas as tarefas concluídas.

        Returns:
            Quantidade de tarefas removidas.
        """
        self._ensure_loaded()
        completed = [t for t in self._tasks if t.status == TaskStatus.DONE]
        count = len(completed)
        if count > 0:
            self._tasks = [t for t in self._tasks if t.status != TaskStatus.DONE]
            self._persist()
        return count

    def stats(self) -> dict:
        """Retorna estatísticas rápidas."""
        self._ensure_loaded()
        total = len(self._tasks)
        overdue_count = sum(1 for t in self._tasks if t.is_overdue())
        return {
            "total": total,
            "pending": sum(1 for t in self._tasks if t.status == TaskStatus.PENDING),
            "in_progress": sum(1 for t in self._tasks if t.status == TaskStatus.IN_PROGRESS),
            "done": sum(1 for t in self._tasks if t.status == TaskStatus.DONE),
            "overdue": overdue_count,
            "by_priority": {
                "high": sum(1 for t in self._tasks if t.priority == TaskPriority.HIGH),
                "medium": sum(1 for t in self._tasks if t.priority == TaskPriority.MEDIUM),
                "low": sum(1 for t in self._tasks if t.priority == TaskPriority.LOW),
            },
        }

    # ===== EXPORT / IMPORT =====

    def export_json(self) -> str:
        """Exporta todas as tarefas para string JSON."""
        self._ensure_loaded()
        import json
        # Ordena por updated_at desc (mais recentes primeiro), igual ao list()
        tasks = sorted(self._tasks, key=lambda t: t.updated_at, reverse=True)
        data = [task.to_dict() for task in tasks]
        return json.dumps(data, ensure_ascii=False, indent=2)

    def export_csv(self) -> str:
        """Exporta todas as tarefas para string CSV."""
        self._ensure_loaded()
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        # Header
        writer.writerow([
            "id", "title", "description", "status", "priority",
            "due_date", "tags", "created_at", "updated_at", "completed_at"
        ])
        # Ordena por updated_at desc (mais recentes primeiro)
        tasks = sorted(self._tasks, key=lambda t: t.updated_at, reverse=True)
        for task in tasks:
            writer.writerow([
                task.id,
                task.title,
                task.description,
                task.status.value,
                task.priority.value,
                task.due_date.isoformat() if task.due_date else "",
                ",".join(task.tags),
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
                task.completed_at.isoformat() if task.completed_at else "",
            ])
        return output.getvalue()

    def export_markdown(self) -> str:
        """Exporta todas as tarefas para string Markdown."""
        self._ensure_loaded()
        lines = ["# Tarefas\n"]
        # Ordena por updated_at desc (mais recentes primeiro)
        tasks = sorted(self._tasks, key=lambda t: t.updated_at, reverse=True)
        for task in tasks:
            status_icon = {"pending": "[ ]", "in_progress": "[>]", "done": "[x]"}[task.status.value]
            priority_icon = {"low": "[LOW]", "medium": "[MED]", "high": "[HIGH]"}[task.priority.value]
            tags = " ".join(f"`#{t}`" for t in task.tags) if task.tags else ""
            due = f" [due:{task.due_date.strftime('%d/%m/%Y')}]" if task.due_date else ""
            lines.append(f"- {status_icon} {priority_icon} **{task.title}**{due} {tags}")
            if task.description:
                lines.append(f"  > {task.description}")
        return "\n".join(lines)

    def import_json(self, json_str: str, merge: bool = True) -> int:
        """Importa tarefas de string JSON.

        Args:
            json_str: String JSON com array de tarefas.
            merge: Se True, adiciona às existentes; se False, substitui tudo.

        Returns:
            Número de tarefas importadas.
        """
        import json
        self._ensure_loaded()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValidationError(f"JSON inválido: {e}") from e

        if not isinstance(data, list):
            raise ValidationError("JSON deve ser um array de tarefas")

        if not merge:
            self._tasks.clear()

        imported = 0
        for item in data:
            try:
                task = Task.from_dict(item)
                # Evita duplicatas por ID
                if not any(t.id == task.id for t in self._tasks):
                    self._tasks.append(task)
                    imported += 1
            except (KeyError, ValueError, TypeError):
                # Pula itens inválidos
                continue

        if imported > 0:
            self._persist()
        return imported

    def import_csv(self, csv_str: str, merge: bool = True) -> int:
        """Importa tarefas de string CSV.

        Args:
            csv_str: String CSV com header.
            merge: Se True, adiciona às existentes; se False, substitui tudo.

        Returns:
            Número de tarefas importadas.
        """
        import csv
        import io
        from datetime import datetime

        self._ensure_loaded()

        try:
            reader = csv.DictReader(io.StringIO(csv_str))
            rows = list(reader)
        except Exception as e:
            raise ValidationError(f"CSV inválido: {e}") from e

        if not merge:
            self._tasks.clear()

        imported = 0
        for row in rows:
            try:
                # Converte campos
                due_date = None
                if row.get("due_date"):
                    due_date = datetime.fromisoformat(row["due_date"])

                tags = []
                if row.get("tags"):
                    tags = [t.strip() for t in row["tags"].split(",") if t.strip()]

                task = Task(
                    id=row.get("id", str(uuid.uuid4())[:8]),
                    title=row["title"],
                    description=row.get("description", ""),
                    status=TaskStatus(row.get("status", "pending")),
                    priority=TaskPriority(row.get("priority", "medium")),
                    due_date=due_date,
                    tags=tags,
                    created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else datetime.now(),
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
                )
                if not any(t.id == task.id for t in self._tasks):
                    self._tasks.append(task)
                    imported += 1
            except (KeyError, ValueError, TypeError):
                continue

        if imported > 0:
            self._persist()
        return imported
