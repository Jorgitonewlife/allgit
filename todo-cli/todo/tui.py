"""TUI (Terminal User Interface) usando Textual.

Interface rica e interativa para gerenciar tarefas.
"""

from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TextArea,
)

from .config import get_config
from .models import Task, TaskPriority, TaskStatus
from .service import TaskNotFoundError, TodoService, ValidationError
from .storage import Storage


class TaskAdded(Message):
    """Enviada quando uma tarefa é adicionada via TUI."""
    def __init__(self, task: Task) -> None:
        self.task = task
        super().__init__()


class TaskUpdated(Message):
    """Enviada quando uma tarefa é atualizada via TUI."""
    def __init__(self, task: Task) -> None:
        self.task = task
        super().__init__()


class TaskDeleted(Message):
    """Enviada quando uma tarefa é deletada via TUI."""
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__()


class AddTaskModal(ModalScreen):
    """Modal para adicionar nova tarefa."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancelar"),
        Binding("ctrl+s", "save", "Salvar"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="add-modal"):
            yield Label("Nova Tarefa", id="modal-title")
            yield Input(placeholder="Título (obrigatório)", id="title-input")
            yield TextArea(placeholder="Descrição (opcional)", id="desc-input")
            yield Select(
                [
                    ("Baixa", "low"),
                    ("Média", "medium"),
                    ("Alta", "high"),
                ],
                value="medium",
                id="priority-select"
            )
            yield Input(placeholder="Data vencimento (YYYY-MM-DD)", id="due-input")
            yield Input(placeholder="Tags separadas por vírgula", id="tags-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Salvar", variant="primary", id="save-btn")
                yield Button("Cancelar", variant="default", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def action_save(self) -> None:
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            self.notify("Título é obrigatório", severity="error")
            return

        desc = self.query_one("#desc-input", TextArea).text.strip()
        priority = TaskPriority(self.query_one("#priority-select", Select).value)
        due_str = self.query_one("#due-input", Input).value.strip()
        tags_str = self.query_one("#tags-input", Input).value.strip()

        due_date = None
        if due_str:
            try:
                due_date = datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                self.notify("Formato de data inválido. Use YYYY-MM-DD", severity="error")
                return

        tags = [t.strip().lower().replace(" ", "-") for t in tags_str.split(",") if t.strip()]

        task = Task(
            title=title,
            description=desc,
            priority=priority,
            due_date=due_date,
            tags=tags,
        )
        self.post_message(TaskAdded(task))
        self.dismiss()

    def action_cancel(self) -> None:
        self.dismiss()


class EditTaskModal(ModalScreen):
    """Modal para editar tarefa existente."""

    def __init__(self, task: Task) -> None:
        super().__init__()
        self.task = task

    def compose(self) -> ComposeResult:
        with Container(id="edit-modal"):
            yield Label(f"Editar: {self.task.title}", id="modal-title")
            yield Input(value=self.task.title, id="title-input")
            yield TextArea(text=self.task.description, id="desc-input")
            yield Select(
                [
                    ("Baixa", "low"),
                    ("Média", "medium"),
                    ("Alta", "high"),
                ],
                value=self.task.priority.value,
                id="priority-select"
            )
            due_val = self.task.due_date.strftime("%Y-%m-%d") if self.task.due_date else ""
            yield Input(value=due_val, placeholder="Data vencimento (YYYY-MM-DD)", id="due-input")
            yield Input(value=", ".join(self.task.tags), placeholder="Tags separadas por vírgula", id="tags-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Salvar", variant="primary", id="save-btn")
                yield Button("Cancelar", variant="default", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.dismiss()

    def action_save(self) -> None:
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            self.notify("Título é obrigatório", severity="error")
            return

        desc = self.query_one("#desc-input", TextArea).text.strip()
        priority = TaskPriority(self.query_one("#priority-select", Select).value)
        due_str = self.query_one("#due-input", Input).value.strip()
        tags_str = self.query_one("#tags-input", Input).value.strip()

        due_date = None
        if due_str:
            try:
                due_date = datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                self.notify("Formato de data inválido. Use YYYY-MM-DD", severity="error")
                return

        tags = [t.strip().lower().replace(" ", "-") for t in tags_str.split(",") if t.strip()]

        updated_task = Task(
            id=self.task.id,
            title=title,
            description=desc,
            status=self.task.status,
            priority=priority,
            due_date=due_date,
            tags=tags,
            created_at=self.task.created_at,
            updated_at=datetime.now(),
            completed_at=self.task.completed_at,
        )
        self.post_message(TaskUpdated(updated_task))
        self.dismiss()


class ConfirmModal(ModalScreen):
    """Modal de confirmação genérico."""

    def __init__(self, message: str, action_name: str, task_id: str) -> None:
        super().__init__()
        self.message = message
        self.action_name = action_name
        self.task_id = task_id

    def compose(self) -> ComposeResult:
        with Container(id="confirm-modal"):
            yield Label(self.message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button(f"Confirmar {self.action_name}", variant="error", id="confirm-btn")
                yield Button("Cancelar", variant="default", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-btn":
            self.post_message(TaskDeleted(self.task_id))
            self.dismiss()
        elif event.button.id == "cancel-btn":
            self.dismiss()


class TodoTUI(App):
    """Aplicação TUI principal."""

    TITLE = "Todo CLI - Gerenciador de Tarefas"
    SUB_TITLE = "Interface textual interativa"

    BINDINGS = [
        Binding("a", "add_task", "Adicionar"),
        Binding("e", "edit_task", "Editar"),
        Binding("d", "delete_task", "Deletar"),
        Binding("space", "toggle_status", "Alternar Status"),
        Binding("f", "filter", "Filtrar"),
        Binding("r", "refresh", "Atualizar"),
        Binding("q", "quit", "Sair"),
        Binding("ctrl+c", "quit", "Sair"),
        Binding("/", "search", "Buscar"),
        Binding("escape", "clear_search", "Limpar Busca"),
    ]

    CSS = """
    #add-modal, #edit-modal, #confirm-modal {
        align: center middle;
        width: 70%;
        max-width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #modal-buttons, #confirm-buttons {
        margin-top: 1;
        align: center middle;
    }

    #confirm-message {
        text-align: center;
        margin-bottom: 1;
    }

    DataTable {
        height: 1fr;
    }

    #status-bar {
        dock: bottom;
        height: 3;
        background: $surface;
        border-top: solid $primary;
        padding: 0 1;
    }

    #search-input {
        width: 100%;
        margin: 0 1;
    }

    .hidden {
        display: none;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        config = get_config()
        storage = Storage(file_path=config.get_storage_path())
        self.service = TodoService(storage=storage)
        self.current_filter: dict = {}
        self.search_query: str = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield DataTable(id="task-table", cursor_type="row")
            yield Input(placeholder="Buscar... (Pressione / para buscar, Esc para limpar)", id="search-input", classes="hidden")
            yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Inicializa a tabela e carrega tarefas."""
        table = self.query_one("#task-table", DataTable)
        table.add_columns(
            "ID", "Status", "Prioridade", "Título", "Descrição", "Tags", "Vencimento", "Criada"
        )
        table.cursor_type = "row"
        table.zebra_stripes = True
        self.refresh_table()
        self.update_status_bar()

    def refresh_table(self) -> None:
        """Atualiza a tabela com tarefas filtradas."""
        table = self.query_one("#task-table", DataTable)
        table.clear()

        tasks = self.service.list(
            status=self.current_filter.get("status"),
            priority=self.current_filter.get("priority"),
            tag=self.current_filter.get("tag"),
            overdue=self.current_filter.get("overdue"),
            search=self.search_query if self.search_query else None,
        )

        for task in tasks:
            status_icon = {"pending": "○", "in_progress": "◐", "done": "●"}[task.status.value]
            priority_icon = {"low": "▼", "medium": "■", "high": "▲"}[task.priority.value]
            due_str = task.due_date.strftime("%d/%m/%Y") if task.due_date else ""
            tags_str = ", ".join(f"#{t}" for t in task.tags) if task.tags else ""
            created_str = task.created_at.strftime("%d/%m/%Y")

            table.add_row(
                task.id,
                f"{status_icon} {task.status.value}",
                f"{priority_icon} {task.priority.value}",
                task.title,
                task.description[:50] + "..." if len(task.description) > 50 else task.description,
                tags_str,
                due_str,
                created_str,
                key=task.id
            )

        self.update_status_bar()

    def update_status_bar(self) -> None:
        """Atualiza barra de status."""
        stats = self.service.stats()
        bar = self.query_one("#status-bar", Static)
        filter_info = ""
        if self.current_filter:
            filter_info = " | Filtros: " + ", ".join(f"{k}={v}" for k, v in self.current_filter.items())
        if self.search_query:
            filter_info += f" | Busca: '{self.search_query}'"
        bar.update(
            f"Total: {stats['total']} | "
            f"Pendentes: {stats['pending']} | "
            f"Em andamento: {stats['in_progress']} | "
            f"Concluídas: {stats['done']} | "
            f"Vencidas: {stats['overdue']}"
            f"{filter_info}"
        )

    def action_add_task(self) -> None:
        """Abre modal para adicionar tarefa."""
        self.push_screen(AddTaskModal())

    def action_edit_task(self) -> None:
        """Abre modal para editar tarefa selecionada."""
        table = self.query_one("#task-table", DataTable)
        if table.cursor_row is not None:
            row_key = table.get_row_at(table.cursor_row)[0]  # ID está na primeira coluna
            task = self.service.get(row_key)
            self.push_screen(EditTaskModal(task))
        else:
            self.notify("Selecione uma tarefa para editar", severity="warning")

    def action_delete_task(self) -> None:
        """Abre modal de confirmação para deletar."""
        table = self.query_one("#task-table", DataTable)
        if table.cursor_row is not None:
            row_key = table.get_row_at(table.cursor_row)[0]
            task = self.service.get(row_key)
            self.push_screen(ConfirmModal(
                f"Deletar '{task.title}'? Esta ação não pode ser desfeita.",
                "deletar",
                row_key
            ))
        else:
            self.notify("Selecione uma tarefa para deletar", severity="warning")

    def action_toggle_status(self) -> None:
        """Alterna status da tarefa selecionada."""
        table = self.query_one("#task-table", DataTable)
        if table.cursor_row is not None:
            row_key = table.get_row_at(table.cursor_row)[0]
            task = self.service.get(row_key)
            try:
                if task.status == TaskStatus.PENDING:
                    self.service.start(row_key)
                elif task.status == TaskStatus.IN_PROGRESS:
                    self.service.complete(row_key)
                elif task.status == TaskStatus.DONE:
                    self.service.reopen(row_key)
                self.notify(f"Status alterado para {task.status.value}", severity="information")
                self.refresh_table()
            except ValidationError as e:
                self.notify(str(e), severity="error")
        else:
            self.notify("Selecione uma tarefa", severity="warning")

    def action_filter(self) -> None:
        """TODO: Implementar dialog de filtros."""
        self.notify("Filtros: use --status, --priority, --tag via CLI por enquanto", severity="information")

    def action_refresh(self) -> None:
        """Recarrega tarefas do disco."""
        self.service._loaded = False
        self.refresh_table()
        self.notify("Tarefas recarregadas", severity="information")

    def action_search(self) -> None:
        """Mostra campo de busca."""
        search_input = self.query_one("#search-input", Input)
        search_input.remove_class("hidden")
        search_input.focus()

    def action_clear_search(self) -> None:
        """Limpa busca."""
        search_input = self.query_one("#search-input", Input)
        search_input.add_class("hidden")
        search_input.value = ""
        self.search_query = ""
        self.refresh_table()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Captura mudança no campo de busca."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self.refresh_table()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter no campo de busca."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self.refresh_table()
            event.input.blur()

    def on_task_added(self, message: TaskAdded) -> None:
        """Handler para tarefa adicionada via modal."""
        try:
            self.service.add(
                message.task.title,
                message.task.description,
                message.task.priority,
                message.task.due_date,
                message.task.tags
            )
            self.notify(f"Tarefa '{message.task.title}' criada", severity="information")
            self.refresh_table()
        except ValidationError as e:
            self.notify(str(e), severity="error")

    def on_task_updated(self, message: TaskUpdated) -> None:
        """Handler para tarefa atualizada via modal."""
        try:
            self.service.update_title(message.task.id, message.task.title)
            self.service.update_description(message.task.id, message.task.description)
            self.service.set_priority(message.task.id, message.task.priority)
            self.service.set_due_date(message.task.id, message.task.due_date)
            self.service.clear_tags(message.task.id)
            for tag in message.task.tags:
                self.service.add_tag(message.task.id, tag)
            self.notify(f"Tarefa '{message.task.title}' atualizada", severity="information")
            self.refresh_table()
        except ValidationError as e:
            self.notify(str(e), severity="error")

    def on_task_deleted(self, message: TaskDeleted) -> None:
        """Handler para tarefa deletada via modal."""
        try:
            self.service.delete(message.task_id)
            self.notify("Tarefa deletada", severity="information")
            self.refresh_table()
        except TaskNotFoundError:
            self.notify("Tarefa não encontrada", severity="error")


def run_tui() -> None:
    """Entry point para executar a TUI."""
    app = TodoTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
