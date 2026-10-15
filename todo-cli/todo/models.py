"""Modelos de dados do sistema Todo.

Define as estruturas centrais: Task (tarefa), TaskStatus (estado), TaskPriority (prioridade).
Usa 'dataclasses' para reduzir boilerplate e 'enum' para valores controlados.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Estados possíveis de uma tarefa.

    Usar 'str, Enum' faz com que o valor serializado em JSON seja a string
    (ex: "pending") em vez de um objeto complexo.
    """
    PENDING = "pending"      # Tarefa criada, não iniciada
    IN_PROGRESS = "in_progress"  # Tarefa em andamento
    DONE = "done"            # Tarefa concluída


class TaskPriority(str, Enum):
    """Níveis de prioridade da tarefa.

    Ordem: LOW < MEDIUM < HIGH
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    def __lt__(self, other: "TaskPriority") -> bool:
        """Permite ordenação por prioridade (HIGH > MEDIUM > LOW)."""
        order = {TaskPriority.LOW: 0, TaskPriority.MEDIUM: 1, TaskPriority.HIGH: 2}
        return order[self] < order[other]


@dataclass
class Task:
    """Representa uma única tarefa no sistema.

    'dataclass' gera automaticamente __init__, __repr__, __eq__.
    'field(default_factory=...)' é usado para campos mutáveis (list, dict)
    ou para valores que precisam ser gerados na hora da criação.
    """
    title: str                          # Título obrigatório da tarefa
    description: str = ""               # Descrição opcional (padrão: vazio)
    status: TaskStatus = TaskStatus.PENDING  # Estado inicial: pendente
    priority: TaskPriority = TaskPriority.MEDIUM  # Prioridade padrão: média
    due_date: datetime | None = None    # Data de vencimento opcional
    tags: list[str] = field(default_factory=list)  # Tags/labels (ex: ["trabalho", "urgente"])
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])  # ID único curto (8 chars)
    created_at: datetime = field(default_factory=datetime.now)  # Timestamp de criação
    updated_at: datetime = field(default_factory=datetime.now)  # Timestamp de última atualização
    completed_at: datetime | None = None  # Preenchido apenas quando status == DONE

    def mark_in_progress(self) -> None:
        """Marca a tarefa como 'em andamento'."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def mark_done(self) -> None:
        """Marca a tarefa como 'concluída' e registra o horário."""
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now()
        self.completed_at = datetime.now()

    def mark_pending(self) -> None:
        """Reverte a tarefa para 'pendente' (útil para desfazer conclusão)."""
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now()
        self.completed_at = None

    def update_title(self, new_title: str) -> None:
        """Atualiza o título da tarefa."""
        if not new_title or not new_title.strip():
            raise ValueError("Título não pode ser vazio")
        self.title = new_title.strip()
        self.updated_at = datetime.now()

    def update_description(self, new_description: str) -> None:
        """Atualiza a descrição da tarefa."""
        self.description = new_description.strip()
        self.updated_at = datetime.now()

    def set_priority(self, priority: TaskPriority) -> None:
        """Define a prioridade da tarefa."""
        self.priority = priority
        self.updated_at = datetime.now()

    def set_due_date(self, due_date: datetime | None) -> None:
        """Define a data de vencimento (None para remover)."""
        self.due_date = due_date
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Adiciona uma tag (normalizada: lowercase, sem espaços)."""
        normalized = tag.strip().lower().replace(" ", "-")
        if normalized and normalized not in self.tags:
            self.tags.append(normalized)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove uma tag."""
        normalized = tag.strip().lower().replace(" ", "-")
        if normalized in self.tags:
            self.tags.remove(normalized)
            self.updated_at = datetime.now()

    def clear_tags(self) -> None:
        """Remove todas as tags."""
        if self.tags:
            self.tags.clear()
            self.updated_at = datetime.now()

    def is_overdue(self) -> bool:
        """Verifica se a tarefa está vencida (due_date passou e não está done)."""
        if self.due_date is None or self.status == TaskStatus.DONE:
            return False
        return datetime.now() > self.due_date

    def to_dict(self) -> dict:
        """Converte a Task para dicionário serializável (para JSON).

        Converte datetime -> string ISO 8601, Enum -> string, list -> list.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstrói uma Task a partir de dicionário (vindo do JSON).

        'classmethod' permite criar instâncias sem instanciar a classe antes.
        Faz o caminho inverso de to_dict(): string -> datetime, string -> Enum.
        """
        # Converte strings ISO de volta para datetime
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        completed_at = (
            datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None
        )
        due_date = (
            datetime.fromisoformat(data["due_date"])
            if data.get("due_date")
            else None
        )

        # Tags: garante que seja lista (compatibilidade com dados antigos)
        tags = data.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=TaskStatus(data["status"]),
            priority=TaskPriority(data.get("priority", "medium")),
            due_date=due_date,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )
