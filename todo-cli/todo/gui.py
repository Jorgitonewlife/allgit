"""GUI (Interface Gráfica) usando PySide6.

Interface moderna para o Todo CLI usando Qt.
Fornece visualização tabular com filtros, ações de toolbar,
menu de contexto, delegate customizado para tags coloridas,
e design responsivo.
"""

import sys
from typing import override

# Qt Core - modelos, timers, sinais, geometria
from PySide6.QtCore import QAbstractTableModel, QDate, QModelIndex, QRect, QSize, Qt, QTimer, Signal

# Qt Gui - ações, cores, fontes, métricas, painter
from PySide6.QtGui import QAction, QColor, QFont, QFontMetrics, QPainter

# Qt Widgets - componentes visuais, layouts, delegates, toolbars
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStatusBar,
    QStyledItemDelegate,
    QTableView,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

# Módulos locais do projeto
from .config import get_config
from .models import Task, TaskPriority, TaskStatus
from .service import TaskNotFoundError, TodoService, ValidationError
from .storage import Storage

# Cores por status/prioridade
STATUS_COLORS = {
    TaskStatus.PENDING: "#fbbf24",      # amber
    TaskStatus.IN_PROGRESS: "#3b82f6",  # blue
    TaskStatus.DONE: "#22c55e",         # green
}

PRIORITY_COLORS = {
    TaskPriority.LOW: "#22c55e",        # green
    TaskPriority.MEDIUM: "#fbbf24",     # amber
    TaskPriority.HIGH: "#ef4444",       # red
}

STATUS_ICONS = {
    TaskStatus.PENDING: "○",
    TaskStatus.IN_PROGRESS: "◐",
    TaskStatus.DONE: "●",
}

PRIORITY_ICONS = {
    TaskPriority.LOW: "▼",
    TaskPriority.MEDIUM: "■",
    TaskPriority.HIGH: "▲",
}

# Cores por status/prioridade (Tailwind CSS palette para consistência)
STATUS_COLORS = {
    TaskStatus.PENDING: "#fbbf24",      # amber - pendente
    TaskStatus.IN_PROGRESS: "#3b82f6",  # blue - em andamento
    TaskStatus.DONE: "#22c55e",         # green - concluído
}

PRIORITY_COLORS = {
    TaskPriority.LOW: "#22c55e",        # green - baixa
    TaskPriority.MEDIUM: "#fbbf24",     # amber - média
    TaskPriority.HIGH: "#ef4444",       # red - alta
}

# Ícones Unicode para status (compatível com terminais modernos)
STATUS_ICONS = {
    TaskStatus.PENDING: "○",           # círculo vazio
    TaskStatus.IN_PROGRESS: "◐",       # círculo meio preenchido
    TaskStatus.DONE: "●",              # círculo preenchido
}

# Ícones Unicode para prioridade
PRIORITY_ICONS = {
    TaskPriority.LOW: "▼",             # seta para baixo
    TaskPriority.MEDIUM: "■",          # quadrado
    TaskPriority.HIGH: "▲",            # seta para cima
}

# Paleta de 8 cores para tags (background, foreground)
# Cores escolhidas para bom contraste WCAG AA
TAG_COLORS = [
    ("#3b82f6", "#ffffff"),  # azul
    ("#22c55e", "#ffffff"),  # verde
    ("#f97316", "#ffffff"),  # laranja
    ("#ec4899", "#ffffff"),  # rosa
    ("#8b5cf6", "#ffffff"),  # roxo
    ("#06b6d4", "#ffffff"),  # ciano
    ("#eab308", "#1f2937"),  # amarelo (texto escuro para contraste)
    ("#ef4444", "#ffffff"),  # vermelho
]


def get_tag_color(tag: str) -> tuple[str, str]:
    """Retorna cor de fundo e texto para uma tag baseada no hash.
    
    Usa hash determinístico para garantir que a mesma tag
    sempre tenha a mesma cor, facilitando identificação visual.
    """
    idx = hash(tag) % len(TAG_COLORS)
    return TAG_COLORS[idx]


class TagDelegate(QStyledItemDelegate):
    """Delegate customizado para renderizar tags como chips coloridos.
    
    Substitui renderização padrão de texto por badges arredondados
    coloridos (estilo 'chip' Material Design), um por tag.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Fonte pequena para tags (8pt, peso médio)
        self.tag_font = QFont()
        self.tag_font.setPointSize(8)
        self.tag_font.setWeight(QFont.Weight.Medium)

    def paint(self, painter, option, index):
        """Desenha as tags como chips coloridos na célula."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Obtém texto das tags do model (string separada por vírgula)
        tags_text = index.data(Qt.DisplayRole) or ""
        if not tags_text:
            painter.restore()
            return

        # Parse das tags: remove #, espaços, ignora vazias
        tags = [t.strip().lstrip("#") for t in tags_text.split(",") if t.strip()]

        # Configuração visual dos chips
        padding_h = 6       # padding horizontal interno
        spacing = 4         # espaço entre chips
        radius = 4          # raio dos cantos arredondados
        margin = 4          # margem esquerda da célula

        # Posição inicial (centralizado verticalmente)
        x = option.rect.left() + margin
        y = option.rect.top() + (option.rect.height() - 20) // 2

        for tag in tags:
            bg_color, text_color = get_tag_color(tag)

            # Mede largura do texto para dimensionar chip
            metrics = QFontMetrics(self.tag_font)
            text_width = metrics.horizontalAdvance(tag)
            tag_width = text_width + 2 * padding_h
            tag_height = 20  # altura fixa do chip

            # Quebra linha se não couber (não implementado wrap multi-linha)
            if x + tag_width > option.rect.right() - margin:
                break

            # Desenha chip arredondado
            rect = QRect(x, y, tag_width, tag_height)
            painter.setBrush(QColor(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, radius, radius)

            # Desenha texto centralizado no chip
            painter.setPen(QColor(text_color))
            painter.setFont(self.tag_font)
            painter.drawText(rect, Qt.AlignCenter, tag)

            x += tag_width + spacing

        painter.restore()

    @override
    def sizeHint(self, option, index):
        """Tamanho sugerido para a célula de tags."""
        return QSize(150, 24)


class TaskTableModel(QAbstractTableModel):
    """Modelo de dados para a tabela de tarefas.
    
    Implementa interface QAbstractTableModel para integrar
    com QTableView. Mantém cache em memória sincronizado com Service.
    """

    # Definição das colunas: (nome, role para alinhamento)
    COLUMNS = ["ID", "Status", "Prioridade", "Título", "Descrição", "Tags", "Vencimento", "Criada"]

    def __init__(self, service: TodoService):
        super().__init__()
        self.service = service          # Referência ao service para operações
        self.tasks: list[Task] = []     # Cache em memória das tarefas
        self._load_tasks()              # Carrega inicial do storage

    def _load_tasks(self):
        """Recarrega tarefas do service (storage) e notifica view."""
        self.beginResetModel()          # Notifica início de mudança estrutural
        self.tasks = self.service.list()  # Busca do service (com filtros se houver)
        self.endResetModel()            # Notifica fim - view atualiza

    def refresh(self):
        """Recarrega dados do service (chamado após operações CRUD)."""
        self._load_tasks()

    @override
    def rowCount(self, parent: QModelIndex = None) -> int:
        """Número de linhas = número de tarefas no cache."""
        return len(self.tasks)

    @override
    def columnCount(self, parent: QModelIndex = None) -> int:
        """Número fixo de colunas definidas em COLUMNS."""
        return len(self.COLUMNS)

    @override
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """Cabeçalhos das colunas (apenas horizontal, role Display)."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Retorna dados para a célula (index) e role solicitada.
        
        Suporta roles: DisplayRole (texto), ForegroundRole (cor texto),
        TextAlignmentRole (alinhamento).
        """
        if not index.isValid() or index.row() >= len(self.tasks):
            return None

        task = self.tasks[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            # Texto exibido na célula
            if col == 0:
                return f"#{task.id}"                    # ID com prefixo #
            elif col == 1:
                return f"{STATUS_ICONS[task.status]} {task.status.value}"
            elif col == 2:
                return f"{PRIORITY_ICONS[task.priority]} {task.priority.value}"
            elif col == 3:
                return task.title
            elif col == 4:
                return task.description[:50] + ("..." if len(task.description) > 50 else "")
            elif col == 5:
                return ""  # Tags renderizadas pelo TagDelegate (coluna 5)
            elif col == 6:
                return task.due_date.strftime("%d/%m/%Y") if task.due_date else ""
            elif col == 7:
                return task.created_at.strftime("%d/%m/%Y %H:%M")

        elif role == Qt.ForegroundRole:
            # Cor do texto baseada em status/prioridade
            if col == 1:
                return QColor(STATUS_COLORS[task.status])
            elif col == 2:
                return QColor(PRIORITY_COLORS[task.priority])

        elif role == Qt.TextAlignmentRole:
            # Centraliza colunas de ícones/ID
            if col in (0, 1, 2, 6):
                return Qt.AlignCenter

        return None

    def get_task(self, row: int) -> Task | None:
        """Retorna tarefa pelo índice da linha (para seleção na tabela)."""
        if 0 <= row < len(self.tasks):
            return self.tasks[row]
        return None


class AddTaskDialog(QDialog):
    """Dialog para adicionar/editar tarefa.
    
    Modal com formulário completo: título, descrição, status,
    prioridade, data vencimento, tags.
    """

    def __init__(self, parent=None, task: Task | None = None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("Editar Tarefa" if task else "Nova Tarefa")
        self.setModal(True)           # Bloqueia interação com janela pai
        self.resize(500, 400)
        self._setup_ui()

        if task:
            self._populate(task)      # Preenche campos se editando existente

    def _setup_ui(self):
        """Constrói interface do formulário."""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Título (obrigatório)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título da tarefa (obrigatório)")
        form.addRow("Título *:", self.title_edit)

        # Descrição (opcional, altura limitada)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Descrição (opcional)")
        self.desc_edit.setMaximumHeight(100)
        form.addRow("Descrição:", self.desc_edit)

        # Status com ícones
        self.status_combo = QComboBox()
        for s in TaskStatus:
            self.status_combo.addItem(f"{STATUS_ICONS[s]} {s.value}", s)
        form.addRow("Status:", self.status_combo)

        # Prioridade com ícones
        self.priority_combo = QComboBox()
        for p in TaskPriority:
            self.priority_combo.addItem(f"{PRIORITY_ICONS[p]} {p.value}", p)
        form.addRow("Prioridade:", self.priority_combo)

        # Data vencimento (calendário popup)
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDisplayFormat("dd/MM/yyyy")
        self.due_date.setSpecialValueText("Sem data")  # Texto quando nulo
        self.due_date.setDate(QDate.currentDate())
        form.addRow("Vencimento:", self.due_date)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Tags separadas por vírgula (ex: trabalho, urgente)")
        form.addRow("Tags:", self.tags_edit)

        layout.addLayout(form)

        # Botões OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)  # Valida antes de aceitar
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, task: Task):
        """Preenche campos do formulário com dados da tarefa existente."""
        self.title_edit.setText(task.title)
        self.desc_edit.setPlainText(task.description)

        # Status - encontra índice pelo enum
        idx = self.status_combo.findData(task.status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        # Prioridade
        idx = self.priority_combo.findData(task.priority)
        if idx >= 0:
            self.priority_combo.setCurrentIndex(idx)

        # Due date - converte datetime para QDate
        if task.due_date:
            self.due_date.setDate(QDate(task.due_date.year, task.due_date.month, task.due_date.day))

        # Tags - junta com vírgula
        self.tags_edit.setText(", ".join(task.tags) if task.tags else "")

    def _validate_and_accept(self):
        """Valida título obrigatório antes de aceitar."""
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Erro", "Título é obrigatório")
            return
        self.accept()

    def get_task_data(self) -> dict:
        """Extrai dados do formulário para dicionário pronto para Service."""
        return {
            "title": self.title_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "status": self.status_combo.currentData(),      # Enum TaskStatus
            "priority": self.priority_combo.currentData(),  # Enum TaskPriority
            # Converte QDate para date Python; >2000 evita data nula (ano 0)
            "due_date": self.due_date.date().toPython() if self.due_date.date().year() > 2000 else None,
            # Tags: split por vírgula, trim, lowercase, substitui espaços por hífen
            "tags": [t.strip().lower().replace(" ", "-") for t in self.tags_edit.text().split(",") if t.strip()],
        }


class FilterWidget(QWidget):
    """Widget de filtros na toolbar.
    
    Emite signal filter_changed quando qualquer filtro muda,
    permitindo atualização reativa da tabela.
    """

    filter_changed = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Constrói layout horizontal dos filtros."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Todos", None)  # None = sem filtro
        for s in TaskStatus:
            self.status_combo.addItem(f"{STATUS_ICONS[s]} {s.value}", s)
        self.status_combo.currentIndexChanged.connect(self.filter_changed.emit)
        layout.addWidget(self.status_combo)

        # Priority filter
        layout.addWidget(QLabel("Prioridade:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("Todas", None)
        for p in TaskPriority:
            self.priority_combo.addItem(f"{PRIORITY_ICONS[p]} {p.value}", p)
        self.priority_combo.currentIndexChanged.connect(self.filter_changed.emit)
        layout.addWidget(self.priority_combo)

# Tag filter (texto livre)
        layout.addWidget(QLabel("Tag:"))
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("Filtrar por tag")
        self.tag_edit.textChanged.connect(self.filter_changed.emit)  # Emite a cada keystroke
        layout.addWidget(self.tag_edit)

        # Overdue filter (checkbox)
        self.overdue_check = QCheckBox("Apenas vencidas")
        self.overdue_check.toggled.connect(self.filter_changed.emit)
        layout.addWidget(self.overdue_check)

        # Busca textual
        layout.addWidget(QLabel("Busca:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar no título/descrição...")
        self.search_edit.textChanged.connect(self.filter_changed.emit)
        layout.addWidget(self.search_edit)

        layout.addStretch()  # Empurra filtros para esquerda

    def get_filters(self) -> dict:
        """Retorna dicionário de filtros atuais para Service.list()."""
        return {
            "status": self.status_combo.currentData(),
            "priority": self.priority_combo.currentData(),
            "tag": self.tag_edit.text().strip() or None,
            "overdue": self.overdue_check.isChecked() or None,
            "search": self.search_edit.text().strip() or None,
        }


class MainWindow(QMainWindow):
    """Janela principal da aplicação.
    
    Orquestra: Model (TaskTableModel), View (QTableView),
    Toolbar, StatusBar, Dialogs, Filtros.
    """

    def __init__(self):
        super().__init__()
        # Service com storage configurado (TOML + env vars)
        self.service = TodoService(Storage(file_path=get_config().get_storage_path()))
        self.setWindowTitle("Todo CLI - Gerenciador de Tarefas")
        self.resize(1200, 700)
        self._setup_ui()
        self._setup_shortcuts()
        self.refresh_table()

    def _setup_ui(self):
        """Constrói toda a interface: toolbar, filtros, tabela, statusbar."""
        # Configurações de janela responsiva
        self.setMinimumSize(800, 500)   # Mínimo para não quebrar layout
        self.resize(1200, 700)          # Tamanho inicial confortável

        # Toolbar principal (ações CRUD + status)
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # Ícone + texto
        self.addToolBar(toolbar)

        # Ações da toolbar principal
        self.add_action = QAction("➕ Nova", self)
        self.add_action.setShortcut("Ctrl+N")
        self.add_action.triggered.connect(self.add_task)
        toolbar.addAction(self.add_action)

        self.edit_action = QAction("✏️ Editar", self)
        self.edit_action.setShortcut("Enter")
        self.edit_action.triggered.connect(self.edit_task)
        toolbar.addAction(self.edit_action)

        self.delete_action = QAction("🗑️ Excluir", self)
        self.delete_action.setShortcut("Del")
        self.delete_action.triggered.connect(self.delete_task)
        toolbar.addAction(self.delete_action)

        toolbar.addSeparator()

        self.done_action = QAction("✅ Concluir", self)
        self.done_action.setShortcut("Ctrl+D")
        self.done_action.triggered.connect(self.toggle_done)
        toolbar.addAction(self.done_action)

        self.start_action = QAction("▶️ Iniciar", self)
        self.start_action.setShortcut("Ctrl+I")
        self.start_action.triggered.connect(self.toggle_start)
        toolbar.addAction(self.start_action)

        self.reopen_action = QAction("🔄 Reabrir", self)
        self.reopen_action.triggered.connect(self.toggle_reopen)
        toolbar.addAction(self.reopen_action)

        toolbar.addSeparator()

        self.refresh_action = QAction("🔄 Atualizar", self)
        self.refresh_action.setShortcut("F5")
        self.refresh_action.triggered.connect(self.refresh_table)
        toolbar.addAction(self.refresh_action)

        self.export_action = QAction("📤 Exportar", self)
        self.export_action.triggered.connect(self.export_dialog)
        toolbar.addAction(self.export_action)

        # Filtros - toolbar responsiva (quebra linha)
        self.filter_widget = FilterWidget()
        self.filter_widget.filter_changed.connect(self.apply_filters)  # Reativo
        self.addToolBarBreak()
        filter_toolbar = QToolBar("Filtros")
        filter_toolbar.setMovable(False)
        filter_toolbar.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        self.addToolBar(filter_toolbar)
        filter_toolbar.addWidget(self.filter_widget)

        # Tabela responsiva
        self.model = TaskTableModel(self.service)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)  # Seleciona linha inteira
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)   # Zebra striping
        self.table.setSortingEnabled(True)         # Clique no header ordena
        self.table.setShowGrid(False)              # Visual limpo sem grid
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)  # Scroll suave
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionsMovable(True)      # Usuário pode reordenar colunas
        header.setSectionsClickable(True)    # Click no header ordena
        header.setHighlightSections(False)

        # Modos de redimensionamento responsivos
        header.setSectionResizeMode(0, QHeaderView.Fixed)       # ID
        header.setSectionResizeMode(1, QHeaderView.Fixed)       # Status
        header.setSectionResizeMode(2, QHeaderView.Fixed)       # Prioridade
        header.setSectionResizeMode(3, QHeaderView.Stretch)     # Título (estica)
        header.setSectionResizeMode(4, QHeaderView.Stretch)     # Descrição (estica)
        header.setSectionResizeMode(5, QHeaderView.Interactive) # Tags (arrastável)
        header.setSectionResizeMode(6, QHeaderView.Fixed)       # Vencimento
        header.setSectionResizeMode(7, QHeaderView.Fixed)       # Criada

        # Larguras iniciais
        self.table.setColumnWidth(0, 70)    # ID
        self.table.setColumnWidth(1, 110)   # Status
        self.table.setColumnWidth(2, 110)   # Prioridade
        self.table.setColumnWidth(3, 300)   # Título
        self.table.setColumnWidth(4, 250)   # Descrição
        self.table.setColumnWidth(5, 150)   # Tags
        self.table.setColumnWidth(6, 100)   # Vencimento
        self.table.setColumnWidth(7, 130)   # Criada

        # Delegate customizado para tags (coluna 5) - chips coloridos
        self.table.setItemDelegateForColumn(5, TagDelegate(self.table))

        self.table.doubleClicked.connect(self.edit_task)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Layout central com margins responsivos
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.addWidget(self.table)
        self.setCentralWidget(central)

        # Status bar com estatísticas
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()

        # Timer para atualização automática (30s)
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(30000)

    def _setup_shortcuts(self):
        # Atalhos já definidos nas actions
        pass

    def _get_selected_task(self) -> Task | None:
        indexes = self.table.selectionModel().selectedRows()
        if indexes:
            return self.model.get_task(indexes[0].row())
        return None

    def refresh_table(self):
        self.model.refresh()
        self.update_status_bar()

    def auto_refresh(self):
        """Atualização automática periódica (timer 30s).
        
        Só recarrega do service; não força reset do model
        para preservar seleção/ordenamento se possível.
        """
        self.model.refresh()

    def apply_filters(self):
        """Aplica filtros do FilterWidget recarregando model.
        
        Usa begin/endResetModel para notificar view da mudança
        completa de dados (filtros alteram linhas inteiras).
        """
        filters = self.filter_widget.get_filters()
        self.model.beginResetModel()
        self.model.tasks = self.service.list(**filters)
        self.model.endResetModel()
        self.update_status_bar()

    def update_status_bar(self):
        """Atualiza statusbar com estatísticas do service."""
        stats = self.service.stats()
        self.status_bar.showMessage(
            f"Total: {stats['total']} | "
            f"Pendentes: {stats['pending']} | "
            f"Em andamento: {stats['in_progress']} | "
            f"Concluídas: {stats['done']} | "
            f"Vencidas: {stats['overdue']}"
        )

    @override
    def resizeEvent(self, event):
        # Ajusta larguras das colunas Stretch proporcionalmente
        super().resizeEvent(event)

    def _show_context_menu(self, pos):
        """Menu de contexto ao clicar com botão direito na tabela.
        
        Ações dinâmicas baseadas no status da tarefa:
        - PENDING: Iniciar, Concluir
        - IN_PROGRESS: Concluir, Reabrir
        - DONE: Reabrir
        Sempre: Editar, Excluir
        """
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        task = self.model.get_task(index.row())
        if not task:
            return

        menu = QMenu(self)

        # Ações baseadas no status atual
        if task.status == TaskStatus.DONE:
            reopen_action = menu.addAction("🔄 Reabrir")
            reopen_action.triggered.connect(lambda: self._reopen_task(task.id))
        elif task.status == TaskStatus.IN_PROGRESS:
            complete_action = menu.addAction("✅ Concluir")
            complete_action.triggered.connect(lambda: self._complete_task(task.id))
            reopen_action = menu.addAction("🔄 Reabrir")
            reopen_action.triggered.connect(lambda: self._reopen_task(task.id))
        else:  # PENDING
            start_action = menu.addAction("▶️ Iniciar")
            start_action.triggered.connect(lambda: self._start_task(task.id))
            done_action = menu.addAction("✅ Concluir")
            done_action.triggered.connect(lambda: self._complete_task(task.id))

        menu.addSeparator()

        edit_action = menu.addAction("✏️ Editar")
        edit_action.triggered.connect(lambda: self.edit_task())

        delete_action = menu.addAction("🗑️ Excluir")
        delete_action.triggered.connect(lambda: self.delete_task())

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _start_task(self, task_id: str):
        """Marca tarefa como 'em andamento' via context menu."""
        try:
            self.service.start(task_id)
            self.refresh_table()
        except ValidationError as e:
            QMessageBox.warning(self, "Erro", str(e))

    def _complete_task(self, task_id: str):
        """Marca tarefa como 'concluída' via context menu."""
        try:
            self.service.complete(task_id)
            self.refresh_table()
        except ValidationError as e:
            QMessageBox.warning(self, "Erro", str(e))

    def _reopen_task(self, task_id: str):
        """Reabre tarefa concluída via context menu."""
        try:
            self.service.reopen(task_id)
            self.refresh_table()
        except ValidationError as e:
            QMessageBox.warning(self, "Erro", str(e))

    def add_task(self):
        """Abre dialog para nova tarefa e persiste no service."""
        dialog = AddTaskDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_task_data()
            try:
                self.service.add(**data)
                self.refresh_table()
            except ValidationError as e:
                QMessageBox.warning(self, "Erro", str(e))

    def edit_task(self):
        """Abre dialog para editar tarefa selecionada.
        
        Atualiza todos os campos: título, descrição, prioridade,
        data vencimento, tags (remove todas e re-adiciona).
        """
        task = self._get_selected_task()
        if not task:
            return
        dialog = AddTaskDialog(self, task)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_task_data()
            try:
                self.service.update_title(task.id, data["title"])
                self.service.update_description(task.id, data["description"])
                self.service.set_priority(task.id, data["priority"])
                self.service.set_due_date(task.id, data["due_date"])
                self.service.clear_tags(task.id)
                for tag in data["tags"]:
                    self.service.add_tag(task.id, tag)
                self.refresh_table()
            except ValidationError as e:
                QMessageBox.warning(self, "Erro", str(e))

    def delete_task(self):
        """Deleta tarefa selecionada com confirmação."""
        task = self._get_selected_task()
        if not task:
            return
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deletar '{task.title}'? Esta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.service.delete(task.id)
                self.refresh_table()
            except TaskNotFoundError:
                QMessageBox.warning(self, "Erro", "Tarefa não encontrada")

    def toggle_done(self):
        """Alterna status Done/Pending (ou Reabre se Done)."""
        task = self._get_selected_task()
        if not task:
            return
        try:
            if task.status == TaskStatus.DONE:
                self.service.reopen(task.id)
            else:
                self.service.complete(task.id)
            self.refresh_table()
        except ValidationError as e:
            QMessageBox.warning(self, "Erro", str(e))

    def toggle_start(self):
        """Alterna entre Iniciar/Concluir (para tarefas em andamento)."""
        task = self._get_selected_task()
        if not task:
            return
        try:
            if task.status == TaskStatus.IN_PROGRESS:
                self.service.complete(task.id)
            else:
                self.service.start(task.id)
            self.refresh_table()
        except ValidationError as e:
            QMessageBox.warning(self, "Erro", str(e))

    def toggle_reopen(self):
        """Reabre tarefa concluída (volta para Pendente)."""
        task = self._get_selected_task()
        if not task:
            return
        try:
            self.service.reopen(task.id)
            self.refresh_table()
        except ValidationError as e:
            QMessageBox.warning(self, "Erro", str(e))

    def export_dialog(self):
        """Abre dialog de exportação (JSON/CSV/Markdown)."""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Tarefas", "",
            "JSON (*.json);;CSV (*.csv);;Markdown (*.md)"
        )
        if file_path:
            try:
                if file_path.endswith(".json"):
                    content = self.service.export_json()
                elif file_path.endswith(".csv"):
                    content = self.service.export_csv()
                else:
                    content = self.service.export_markdown()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                QMessageBox.information(self, "Sucesso", f"Exportado para {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar: {e}")

    @override
    def closeEvent(self, event):
        """Para timer de auto-refresh ao fechar janela."""
        self.timer.stop()
        super().closeEvent(event)


def run_gui():
    """Entry point para a GUI.
    
    Cria QApplication, configura tema Fusion (cross-platform),
    instancia MainWindow e inicia event loop.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Todo CLI")
    app.setApplicationVersion("0.1.0")

    # Tema Fusion - nativo cross-platform, visual moderno
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
