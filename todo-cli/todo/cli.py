"""Interface de linha de comando (CLI) usando argparse.

Define comandos, argumentos, ajuda e formatação de saída.
Não contém lógica de negócio — delega tudo para TodoService.
"""

import sys
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from datetime import datetime

from .config import get_config
from .crm.models import Customer, CustomerStatus, Deal, DealStatus
from .crm.service import (
    CrmService,
    CrmServiceError,
    CrmValidationError,
    CustomerNotFoundError,
    DealNotFoundError,
)
from .models import Task, TaskPriority, TaskStatus
from .service import ServiceError, TaskNotFoundError, TodoService, ValidationError


# Cores ANSI para terminal (funciona no Windows 10+, Linux, macOS)
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def _get_display_config() -> dict:
    """Obtém configuração de exibição (cacheada)."""
    if not hasattr(_get_display_config, "_cache"):
        _get_display_config._cache = get_config().get_display_config()
    return _get_display_config._cache


def _supports_unicode() -> bool:
    """Verifica se o terminal suporta Unicode e config permite."""
    if not _get_display_config().get("unicode", True):
        return False
    try:
        "✓".encode(sys.stdout.encoding or "utf-8")
        return True
    except (UnicodeEncodeError, AttributeError):
        return False


def _colors_enabled() -> bool:
    """Verifica se cores estão habilitadas na config e terminal suporta."""
    if not _get_display_config().get("colors", True):
        return False
    return sys.stdout.isatty()


# Ícones por status (Unicode se suportado, senão ASCII)
def _get_status_icons() -> dict:
    if _supports_unicode():
        return {
            TaskStatus.PENDING: "○",
            TaskStatus.IN_PROGRESS: "◐",
            TaskStatus.DONE: "●",
        }
    return {
        TaskStatus.PENDING: "[ ]",
        TaskStatus.IN_PROGRESS: "[>]",
        TaskStatus.DONE: "[x]",
    }


def _get_check_cross() -> tuple[str, str]:
    if _supports_unicode():
        return "✓", "✗"
    return "[OK]", "[ERRO]"


def _check() -> str:
    return _get_check_cross()[0]


def _cross() -> str:
    return _get_check_cross()[1]


def _get_priority_icons() -> dict:
    if _supports_unicode():
        return {
            TaskPriority.LOW: "▼",
            TaskPriority.MEDIUM: "■",
            TaskPriority.HIGH: "▲",
        }
    return {
        TaskPriority.LOW: "[LOW]",
        TaskPriority.MEDIUM: "[MED]",
        TaskPriority.HIGH: "[HIGH]",
    }


PRIORITY_COLOR = {
    TaskPriority.LOW: Colors.GREEN,
    TaskPriority.MEDIUM: Colors.YELLOW,
    TaskPriority.HIGH: Colors.RED,
}


STATUS_COLOR = {
    TaskStatus.PENDING: Colors.YELLOW,
    TaskStatus.IN_PROGRESS: Colors.BLUE,
    TaskStatus.DONE: Colors.GREEN,
}


def colorize(text: str, color: str) -> str:
    """Aplica cor se saída for terminal (TTY) e config permite."""
    if _colors_enabled():
        return f"{color}{text}{Colors.RESET}"
    return text


def format_task(task: Task, show_id: bool = True, show_dates: bool = False, show_priority: bool = True) -> str:
    """Formata uma tarefa para exibição no terminal."""
    status_icons = _get_status_icons()
    icon = status_icons[task.status]
    color = STATUS_COLOR[task.status]

    # Prioridade
    pri_icons = _get_priority_icons()
    pri_icon = pri_icons[task.priority]
    pri_color = PRIORITY_COLOR[task.priority]

    parts = []

    if show_id:
        parts.append(colorize(f"[{task.id}]", Colors.GRAY))

    if show_priority:
        parts.append(colorize(pri_icon, pri_color))

    parts.append(colorize(f"{icon} {task.title}", color))

    if task.description:
        parts.append(colorize(f"  -> {task.description}", Colors.DIM))

    # Tags
    if task.tags:
        tags_str = " ".join(f"#{t}" for t in task.tags)
        parts.append(colorize(f"  [{tags_str}]", Colors.CYAN))

    # Due date
    if task.due_date:
        due_str = task.due_date.strftime("%d/%m/%Y")
        is_overdue = task.is_overdue()
        due_color = Colors.RED if is_overdue else Colors.BLUE
        parts.append(colorize(f"  [due:{due_str}]", due_color))

    if show_dates:
        parts.append(colorize(f"  (criada: {task.created_at.strftime('%d/%m/%Y %H:%M')})", Colors.DIM))
        if task.completed_at:
            parts.append(colorize(f"  (concluída: {task.completed_at.strftime('%d/%m/%Y %H:%M')})", Colors.GREEN))

    return " ".join(parts)


def print_tasks(tasks: list[Task], show_id: bool = True, show_dates: bool = False, show_priority: bool = True) -> None:
    """Imprime lista de tarefas formatada."""
    if not tasks:
        print(colorize("Nenhuma tarefa encontrada.", Colors.DIM))
        return

    for i, task in enumerate(tasks, 1):
        prefix = colorize(f"{i:2d}.", Colors.GRAY) if show_id else ""
        task_str = format_task(task, show_id=show_id, show_dates=show_dates, show_priority=show_priority)
        print(f"{prefix} {task_str}")


def print_stats(stats: dict) -> None:
    """Imprime estatísticas formatadas."""
    print(colorize("\n[STATS] Estatisticas:", Colors.BOLD))
    print(f"  Total:       {colorize(str(stats['total']), Colors.CYAN)}")
    print(f"  Pendentes:   {colorize(str(stats['pending']), Colors.YELLOW)}")
    print(f"  Em andamento: {colorize(str(stats['in_progress']), Colors.BLUE)}")
    print(f"  Concluídas:  {colorize(str(stats['done']), Colors.GREEN)}")
    if "overdue" in stats:
        print(f"  Vencidas:    {colorize(str(stats['overdue']), Colors.RED)}")
    if "by_priority" in stats:
        bp = stats["by_priority"]
        print(f"  Prioridade:  {colorize(str(bp['high']), Colors.RED)} alta | {colorize(str(bp['medium']), Colors.YELLOW)} média | {colorize(str(bp['low']), Colors.GREEN)} baixa")


CUSTOMER_STATUS_COLOR = {
    CustomerStatus.LEAD: Colors.CYAN,
    CustomerStatus.ACTIVE: Colors.GREEN,
    CustomerStatus.INACTIVE: Colors.GRAY,
}

DEAL_STATUS_COLOR = {
    DealStatus.OPEN: Colors.BLUE,
    DealStatus.PROPOSAL: Colors.YELLOW,
    DealStatus.WON: Colors.GREEN,
    DealStatus.LOST: Colors.RED,
}


def _format_money(value: float, currency: str = "BRL") -> str:
    """Formata valor monetário simples."""
    return f"{currency} {value:,.2f}"


def format_customer(customer: Customer, show_id: bool = True, show_dates: bool = False) -> str:
    """Formata um cliente para exibição no terminal."""
    status_color = CUSTOMER_STATUS_COLOR[customer.status]

    parts = []

    if show_id:
        parts.append(colorize(f"[{customer.id}]", Colors.GRAY))

    parts.append(colorize(f"{customer.name}", Colors.BOLD))
    parts.append(colorize(f"({customer.status.value})", status_color))

    if customer.email:
        parts.append(colorize(f"  <{customer.email}>", Colors.CYAN))
    if customer.phone:
        parts.append(colorize(f"  tel:{customer.phone}", Colors.DIM))
    if customer.company:
        parts.append(colorize(f"  [{customer.company}]", Colors.YELLOW))
    if customer.notes:
        parts.append(colorize(f"  -> {customer.notes}", Colors.DIM))

    if show_dates:
        parts.append(colorize(f"  (criado: {customer.created_at.strftime('%d/%m/%Y %H:%M')})", Colors.DIM))

    return " ".join(parts)


def format_deal(deal: Deal, show_id: bool = True, show_customer: bool = False) -> str:
    """Formata um deal para exibição no terminal."""
    status_color = DEAL_STATUS_COLOR[deal.status]

    parts = []

    if show_id:
        parts.append(colorize(f"[{deal.id}]", Colors.GRAY))

    parts.append(colorize(deal.title, Colors.BOLD))
    parts.append(colorize(f"({deal.status.value})", status_color))
    parts.append(colorize(_format_money(deal.value, deal.currency), Colors.GREEN))

    if show_customer:
        parts.append(colorize(f"  cliente:{deal.customer_id}", Colors.CYAN))

    if deal.notes:
        parts.append(colorize(f"  -> {deal.notes}", Colors.DIM))

    if deal.closed_at:
        parts.append(colorize(f"  (fechado: {deal.closed_at.strftime('%d/%m/%Y %H:%M')})", Colors.DIM))

    return " ".join(parts)


def print_customers(customers: list[Customer], show_dates: bool = False) -> None:
    """Imprime lista de clientes formatada."""
    if not customers:
        print(colorize("Nenhum cliente encontrado.", Colors.DIM))
        return

    for i, customer in enumerate(customers, 1):
        prefix = colorize(f"{i:2d}.", Colors.GRAY)
        print(f"{prefix} {format_customer(customer, show_dates=show_dates)}")


def print_deals(deals: list[Deal], show_customer: bool = False) -> None:
    """Imprime lista de deals formatada."""
    if not deals:
        print(colorize("Nenhum deal encontrado.", Colors.DIM))
        return

    for i, deal in enumerate(deals, 1):
        prefix = colorize(f"{i:2d}.", Colors.GRAY)
        print(f"{prefix} {format_deal(deal, show_customer=show_customer)}")


def print_pipeline(pipeline: dict) -> None:
    """Imprime o funil de vendas formatado."""
    print(colorize("\n[PIPELINE] Funil de Vendas:", Colors.BOLD))
    for item in pipeline["by_status"]:
        status = item["status"]
        color = DEAL_STATUS_COLOR[DealStatus(status)]
        print(
            f"  {colorize(status.upper().ljust(10), color)} "
            f"{item['count']:3d} deals  "
            f"{colorize(_format_money(item['total_value']), Colors.GREEN)}"
        )
    print(f"  {'Total:'.ljust(11)} {colorize(_format_money(pipeline['total_value']), Colors.CYAN)}")
    print(f"  {'Ganho:'.ljust(11)} {colorize(_format_money(pipeline['won_value']), Colors.GREEN)}")
    print(f"  {'Em aberto:'.ljust(11)} {colorize(_format_money(pipeline['open_value']), Colors.YELLOW)}")


def print_crm_stats(stats: dict) -> None:
    """Imprime estatísticas do CRM formatadas."""
    print(colorize("\n[STATS] Estatísticas do CRM:", Colors.BOLD))
    print(f"  Clientes total: {colorize(str(stats['total_customers']), Colors.CYAN)}")
    cs = stats["customers_by_status"]
    print(
        f"    Lead: {colorize(str(cs['lead']), Colors.CYAN)} | "
        f"Ativo: {colorize(str(cs['active']), Colors.GREEN)} | "
        f"Inativo: {colorize(str(cs['inactive']), Colors.GRAY)}"
    )
    print(f"  Deals total: {colorize(str(stats['total_deals']), Colors.CYAN)}")
    ds = stats["deals_by_status"]
    print(
        f"    Open: {colorize(str(ds['open']), Colors.BLUE)} | "
        f"Proposal: {colorize(str(ds['proposal']), Colors.YELLOW)} | "
        f"Won: {colorize(str(ds['won']), Colors.GREEN)} | "
        f"Lost: {colorize(str(ds['lost']), Colors.RED)}"
    )
    p = stats["pipeline"]
    print(f"  Pipeline: {colorize(_format_money(p['total_value']), Colors.CYAN)}")
    print(f"  Ganho: {colorize(_format_money(p['won_value']), Colors.GREEN)}")
    print(f"  Em aberto: {colorize(_format_money(p['open_value']), Colors.YELLOW)}")


class TodoCLI:
    """Encapsula toda a lógica de parsing e execução de comandos."""

    def __init__(self, service: TodoService | None = None, crm_service: CrmService | None = None):
        self.service = service or TodoService()
        self.crm_service = crm_service or CrmService()
        self.parser = self._build_parser()

    def _build_parser(self) -> ArgumentParser:
        """Constrói o parser de argumentos com subcomandos."""
        parser = ArgumentParser(
            prog="todo",
            description="Gerenciador de tarefas simples e eficiente",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=colorize(
                """
Exemplos:
  todo add "Estudar Python" -d "Fazer exercícios de lista"
  todo list
  todo list --status pending
  todo list --search python
  todo done abc123
  todo start abc123
  todo reopen abc123
  todo edit abc123 -t "Novo título"
  todo delete abc123
  todo stats
  todo clear-done
                """,
                Colors.DIM,
            ),
        )
        parser.add_argument(
            "-v", "--version", action="version", version="todo 0.2.0"
        )

        # Subcomandos
        subparsers = parser.add_subparsers(dest="command", metavar="COMANDO")

        # ---- ADD ----
        p_add = subparsers.add_parser("add", help="Adiciona nova tarefa")
        p_add.add_argument("title", help="Título da tarefa")
        p_add.add_argument("-d", "--description", default="", help="Descrição opcional")
        p_add.add_argument("-p", "--priority", choices=[p.value for p in TaskPriority], default="medium", help="Prioridade (low, medium, high)")
        p_add.add_argument("--due", help="Data de vencimento (YYYY-MM-DD)")
        p_add.add_argument("--tags", help="Tags separadas por vírgula (ex: trabalho,urgente)")
        p_add.set_defaults(func=self.cmd_add)

        # ---- LIST ----
        p_list = subparsers.add_parser("list", aliases=["ls"], help="Lista tarefas")
        p_list.add_argument(
            "-s", "--status", choices=[s.value for s in TaskStatus],
            help="Filtrar por status (pending, in_progress, done)"
        )
        p_list.add_argument(
            "-p", "--priority", choices=[p.value for p in TaskPriority],
            help="Filtrar por prioridade (low, medium, high)"
        )
        p_list.add_argument(
            "--tag", help="Filtrar por tag"
        )
        p_list.add_argument(
            "--overdue", action="store_true", help="Mostrar apenas tarefas vencidas"
        )
        p_list.add_argument(
            "--no-overdue", action="store_true", help="Mostrar apenas tarefas não vencidas"
        )
        p_list.add_argument(
            "--search", "-q", help="Busca textual no título/descrição"
        )
        p_list.add_argument(
            "--dates", action="store_true", help="Mostrar datas de criação/conclusão"
        )
        p_list.add_argument(
            "--no-priority", action="store_true", help="Ocultar indicador de prioridade"
        )
        p_list.set_defaults(func=self.cmd_list)

        # ---- DONE / COMPLETE ----
        p_done = subparsers.add_parser("done", help="Marca tarefa como concluída")
        p_done.add_argument("id", help="ID da tarefa (prefixo mínimo 3 chars)")
        p_done.set_defaults(func=self.cmd_done)

        # ---- START ----
        p_start = subparsers.add_parser("start", help="Marca tarefa como 'em andamento'")
        p_start.add_argument("id", help="ID da tarefa")
        p_start.set_defaults(func=self.cmd_start)

        # ---- REOPEN ----
        p_reopen = subparsers.add_parser("reopen", help="Reabre tarefa concluída (volta para pendente)")
        p_reopen.add_argument("id", help="ID da tarefa")
        p_reopen.set_defaults(func=self.cmd_reopen)

        # ---- EDIT ----
        p_edit = subparsers.add_parser("edit", help="Edita título ou descrição")
        p_edit.add_argument("id", help="ID da tarefa")
        p_edit.add_argument("-t", "--title", help="Novo título")
        p_edit.add_argument("-d", "--description", help="Nova descrição")
        p_edit.set_defaults(func=self.cmd_edit)

        # ---- DELETE ----
        p_del = subparsers.add_parser("delete", aliases=["rm"], help="Remove tarefa permanentemente")
        p_del.add_argument("id", help="ID da tarefa")
        p_del.add_argument("-y", "--yes", action="store_true", help="Não pedir confirmação")
        p_del.set_defaults(func=self.cmd_delete)

        # ---- STATS ----
        p_stats = subparsers.add_parser("stats", help="Mostra estatísticas")
        p_stats.set_defaults(func=self.cmd_stats)

        # ---- CLEAR-DONE ----
        p_clear = subparsers.add_parser("clear-done", help="Remove todas as tarefas concluídas")
        p_clear.add_argument("-y", "--yes", action="store_true", help="Não pedir confirmação")
        p_clear.set_defaults(func=self.cmd_clear_done)

        # ---- PRIORITY ----
        p_priority = subparsers.add_parser("priority", help="Define prioridade da tarefa")
        p_priority.add_argument("id", help="ID da tarefa")
        p_priority.add_argument("level", choices=[p.value for p in TaskPriority], help="Prioridade (low, medium, high)")
        p_priority.set_defaults(func=self.cmd_priority)

        # ---- DUE-DATE ----
        p_due = subparsers.add_parser("due-date", aliases=["due"], help="Define data de vencimento")
        p_due.add_argument("id", help="ID da tarefa")
        p_due.add_argument("date", nargs="?", help="Data (YYYY-MM-DD) ou vazio para remover")
        p_due.set_defaults(func=self.cmd_due_date)

        # ---- TAG ----
        p_tag = subparsers.add_parser("tag", help="Gerencia tags da tarefa")
        p_tag.add_argument("id", help="ID da tarefa")
        p_tag.add_argument("tag", nargs="?", help="Tag para adicionar (ou remover com --remove)")
        p_tag.add_argument("-r", "--remove", action="store_true", help="Remove a tag em vez de adicionar")
        p_tag.add_argument("--clear", action="store_true", help="Remove todas as tags")
        p_tag.set_defaults(func=self.cmd_tag)

        # ---- EXPORT ----
        p_export = subparsers.add_parser("export", help="Exporta tarefas")
        p_export.add_argument("format", choices=["json", "csv", "md", "markdown"], help="Formato de saída")
        p_export.add_argument("-o", "--output", help="Arquivo de saída (padrão: stdout)")
        p_export.set_defaults(func=self.cmd_export)

        # ---- IMPORT ----
        p_import = subparsers.add_parser("import", help="Importa tarefas")
        p_import.add_argument("format", choices=["json", "csv"], help="Formato de entrada")
        p_import.add_argument("file", help="Arquivo de entrada (use - para stdin)")
        p_import.add_argument("--replace", action="store_true", help="Substitui todas as tarefas em vez de mesclar")
        p_import.set_defaults(func=self.cmd_import)

        # ---- CONFIG ----
        p_config = subparsers.add_parser("config", help="Gerencia configuração")
        p_config.add_argument("action", choices=["show", "get", "set", "path", "reset"], help="Ação a realizar")
        p_config.add_argument("key", nargs="?", help="Chave (ex: display.show_priority)")
        p_config.add_argument("value", nargs="?", help="Valor para set")
        p_config.set_defaults(func=self.cmd_config)

        # ---- TUI ----
        p_tui = subparsers.add_parser("tui", help="Interface textual interativa (Textual)")
        p_tui.set_defaults(func=self.cmd_tui)

        # ---- REPL ----
        p_repl = subparsers.add_parser("repl", help="Shell interativo (REPL) com histórico e autocomplete")
        p_repl.set_defaults(func=self.cmd_repl)

        # ---- GUI ----
        p_gui = subparsers.add_parser("gui", help="Interface gráfica (PySide6)")
        p_gui.set_defaults(func=self.cmd_gui)

        # ---- CRM ----
        p_crm = subparsers.add_parser(
            "crm", help="Módulo CRM (clientes e negócios)",
            formatter_class=RawDescriptionHelpFormatter,
            epilog="""Exemplos CRM:
  todo crm customer add "Acme" --email a@a.com --company "Acme LTDA"
  todo crm customer list --status lead
  todo crm customer get abc123
  todo crm customer edit abc123 --email novo@x.com
  todo crm customer status abc123 active
  todo crm customer rm abc123 -y

  todo crm deal add "Proposta site" --customer abc123 --value 5000
  todo crm deal list --status open
  todo crm deal get def456
  todo crm deal status def456 won
  todo crm deal reopen def456
  todo crm deal edit def456 --value 6000
  todo crm deal rm def456 -y

  todo crm pipeline
  todo crm stats
""",
        )
        p_crm.set_defaults(func=self.cmd_crm)
        crm_subparsers = p_crm.add_subparsers(dest="crm_command", metavar="COMANDO")

        # -- CRM CUSTOMER --
        p_crm_customer = crm_subparsers.add_parser("customer", aliases=["cli"], help="Gerencia clientes")
        p_crm_customer.set_defaults(func=self.cmd_crm_customer)
        customer_subparsers = p_crm_customer.add_subparsers(dest="customer_command", metavar="ACAO")

        # customer add
        p_cust_add = customer_subparsers.add_parser("add", help="Adiciona novo cliente")
        p_cust_add.add_argument("name", help="Nome do cliente")
        p_cust_add.add_argument("-e", "--email", default="", help="Email")
        p_cust_add.add_argument("--phone", default="", help="Telefone")
        p_cust_add.add_argument("--company", default="", help="Empresa")
        p_cust_add.add_argument("--notes", default="", help="Notas")
        p_cust_add.add_argument(
            "-s", "--status", choices=[s.value for s in CustomerStatus],
            default="lead", help="Status inicial (padrão: lead)"
        )
        p_cust_add.set_defaults(func=self.cmd_crm_customer_add)

        # customer list
        p_cust_list = customer_subparsers.add_parser("list", aliases=["ls"], help="Lista clientes")
        p_cust_list.add_argument(
            "-s", "--status", choices=[s.value for s in CustomerStatus],
            help="Filtrar por status"
        )
        p_cust_list.add_argument("--search", "-q", help="Busca em nome/email/empresa")
        p_cust_list.add_argument("--dates", action="store_true", help="Mostrar data de criação")
        p_cust_list.set_defaults(func=self.cmd_crm_customer_list)

        # customer get
        p_cust_get = customer_subparsers.add_parser("get", help="Obtém cliente pelo ID")
        p_cust_get.add_argument("id", help="ID do cliente (prefixo mínimo 3 chars)")
        p_cust_get.set_defaults(func=self.cmd_crm_customer_get)

        # customer edit
        p_cust_edit = customer_subparsers.add_parser("edit", help="Edita campos do cliente")
        p_cust_edit.add_argument("id", help="ID do cliente")
        p_cust_edit.add_argument("-n", "--name", help="Novo nome")
        p_cust_edit.add_argument("-e", "--email", help="Novo email")
        p_cust_edit.add_argument("--phone", help="Novo telefone")
        p_cust_edit.add_argument("--company", help="Nova empresa")
        p_cust_edit.add_argument("--notes", help="Novas notas")
        p_cust_edit.set_defaults(func=self.cmd_crm_customer_edit)

        # customer status
        p_cust_status = customer_subparsers.add_parser("status", help="Define status do cliente")
        p_cust_status.add_argument("id", help="ID do cliente")
        p_cust_status.add_argument("status", choices=[s.value for s in CustomerStatus], help="Novo status")
        p_cust_status.set_defaults(func=self.cmd_crm_customer_status)

        # customer rm
        p_cust_rm = customer_subparsers.add_parser("rm", aliases=["delete"], help="Remove cliente")
        p_cust_rm.add_argument("id", help="ID do cliente")
        p_cust_rm.add_argument("-y", "--yes", action="store_true", help="Não pedir confirmação")
        p_cust_rm.set_defaults(func=self.cmd_crm_customer_rm)

        # -- CRM DEAL --
        p_crm_deal = crm_subparsers.add_parser("deal", aliases=["neg"], help="Gerencia negócios")
        p_crm_deal.set_defaults(func=self.cmd_crm_deal)
        deal_subparsers = p_crm_deal.add_subparsers(dest="deal_command", metavar="ACAO")

        # deal add
        p_deal_add = deal_subparsers.add_parser("add", help="Adiciona novo deal")
        p_deal_add.add_argument("title", help="Título do deal")
        p_deal_add.add_argument("-c", "--customer", required=True, help="ID do cliente vinculado")
        p_deal_add.add_argument("-v", "--value", type=float, default=0.0, help="Valor (padrão 0)")
        p_deal_add.add_argument("--currency", default="BRL", help="Moeda (padrão BRL)")
        p_deal_add.add_argument("--notes", default="", help="Notas")
        p_deal_add.set_defaults(func=self.cmd_crm_deal_add)

        # deal list
        p_deal_list = deal_subparsers.add_parser("list", aliases=["ls"], help="Lista deals")
        p_deal_list.add_argument(
            "-s", "--status", choices=[s.value for s in DealStatus],
            help="Filtrar por status"
        )
        p_deal_list.add_argument("-c", "--customer", help="Filtrar por cliente (ID)")
        p_deal_list.add_argument("--search", "-q", help="Busca em título/notas")
        p_deal_list.add_argument("--customer-id", action="store_true", help="Mostrar ID do cliente")
        p_deal_list.set_defaults(func=self.cmd_crm_deal_list)

        # deal get
        p_deal_get = deal_subparsers.add_parser("get", help="Obtém deal pelo ID")
        p_deal_get.add_argument("id", help="ID do deal (prefixo mínimo 3 chars)")
        p_deal_get.set_defaults(func=self.cmd_crm_deal_get)

        # deal status
        p_deal_status = deal_subparsers.add_parser("status", help="Define status do deal")
        p_deal_status.add_argument("id", help="ID do deal")
        p_deal_status.add_argument("status", choices=[s.value for s in DealStatus], help="Novo status")
        p_deal_status.set_defaults(func=self.cmd_crm_deal_status)

        # deal reopen
        p_deal_reopen = deal_subparsers.add_parser("reopen", help="Reabre deal won/lost")
        p_deal_reopen.add_argument("id", help="ID do deal")
        p_deal_reopen.set_defaults(func=self.cmd_crm_deal_reopen)

        # deal edit
        p_deal_edit = deal_subparsers.add_parser("edit", help="Edita campos do deal")
        p_deal_edit.add_argument("id", help="ID do deal")
        p_deal_edit.add_argument("-t", "--title", help="Novo título")
        p_deal_edit.add_argument("-v", "--value", type=float, help="Novo valor")
        p_deal_edit.add_argument("--currency", help="Nova moeda")
        p_deal_edit.add_argument("--notes", help="Novas notas")
        p_deal_edit.set_defaults(func=self.cmd_crm_deal_edit)

        # deal rm
        p_deal_rm = deal_subparsers.add_parser("rm", aliases=["delete"], help="Remove deal")
        p_deal_rm.add_argument("id", help="ID do deal")
        p_deal_rm.add_argument("-y", "--yes", action="store_true", help="Não pedir confirmação")
        p_deal_rm.set_defaults(func=self.cmd_crm_deal_rm)

        # -- CRM PIPELINE --
        p_pipeline = crm_subparsers.add_parser("pipeline", help="Mostra funil de vendas")
        p_pipeline.set_defaults(func=self.cmd_crm_pipeline)

        # -- CRM STATS --
        p_crm_stats = crm_subparsers.add_parser("stats", help="Mostra estatísticas do CRM")
        p_crm_stats.set_defaults(func=self.cmd_crm_stats)

        return parser

    # ===== HANDLERS DE COMANDOS =====

    def cmd_add(self, args: Namespace) -> int:
        """Adiciona nova tarefa."""
        try:
            priority = TaskPriority(args.priority) if args.priority else TaskPriority.MEDIUM
            due_date = None
            if args.due:
                try:
                    due_date = datetime.strptime(args.due, "%Y-%m-%d")
                except ValueError:
                    print(colorize(f"{_cross()} Formato de data inválido. Use YYYY-MM-DD", Colors.RED), file=sys.stderr)
                    return 1
            tags = []
            if args.tags:
                tags = [t.strip().lower().replace(" ", "-") for t in args.tags.split(",") if t.strip()]

            task = self.service.add(args.title, args.description, priority, due_date, tags)
            print(colorize(f"{_check()} Tarefa criada: ", Colors.GREEN) + format_task(task))
            return 0
        except ValidationError as e:
            print(colorize(f"{_cross()} Erro de validação: {e}", Colors.RED), file=sys.stderr)
            return 1
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_list(self, args: Namespace) -> int:
        """Lista tarefas com filtros."""
        try:
            status = TaskStatus(args.status) if args.status else None
            priority = TaskPriority(args.priority) if args.priority else None
            overdue = None
            if args.overdue:
                overdue = True
            elif args.no_overdue:
                overdue = False

            tasks = self.service.list(
                status=status,
                search=args.search,
                priority=priority,
                tag=args.tag,
                overdue=overdue,
            )
            print_tasks(tasks, show_dates=args.dates, show_priority=not args.no_priority)
            return 0
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_done(self, args: Namespace) -> int:
        """Marca tarefa como concluída."""
        return self._update_status(args.id, "done", self.service.complete)

    def cmd_start(self, args: Namespace) -> int:
        """Marca tarefa como em andamento."""
        return self._update_status(args.id, "start", self.service.start)

    def cmd_reopen(self, args: Namespace) -> int:
        """Reabre tarefa."""
        return self._update_status(args.id, "reopen", self.service.reopen)

    def _update_status(self, task_id: str, action_name: str, action_fn) -> int:
        """Helper para comandos que alteram status."""
        try:
            task = action_fn(task_id)
            print(colorize(f"{_check()} Tarefa {action_name}: ", Colors.GREEN) + format_task(task))
            return 0
        except TaskNotFoundError as e:
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        except ValidationError as e:
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_edit(self, args: Namespace) -> int:
        """Edita título e/ou descrição."""
        if not args.title and not args.description:
            print(colorize(f"{_cross()} Nada para editar. Use --title ou --description", Colors.RED), file=sys.stderr)
            return 1

        try:
            task = self.service.get(args.id)
            if args.title:
                task = self.service.update_title(args.id, args.title)
            if args.description:
                task = self.service.update_description(args.id, args.description)
            print(colorize(f"{_check()} Tarefa atualizada: ", Colors.GREEN) + format_task(task))
            return 0
        except TaskNotFoundError as e:
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        except ValidationError as e:
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_delete(self, args: Namespace) -> int:
        """Remove tarefa."""
        try:
            task = self.service.get(args.id)  # Valida existência
            if not args.yes:
                confirm = input(f"Deletar '{task.title}'? [s/N] ").strip().lower()
                if confirm not in ("s", "sim", "y", "yes"):
                    print("Cancelado.")
                    return 0
            self.service.delete(args.id)
            print(colorize(f"{_check()} Tarefa removida.", Colors.GREEN))
            return 0
        except TaskNotFoundError as e:
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_stats(self, args: Namespace) -> int:
        """Mostra estatísticas."""
        try:
            stats = self.service.stats()
            print_stats(stats)
            return 0
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_clear_done(self, args: Namespace) -> int:
        """Remove todas as concluídas."""
        try:
            if not args.yes:
                confirm = input("Remover TODAS as tarefas concluídas? [s/N] ").strip().lower()
                if confirm not in ("s", "sim", "y", "yes"):
                    print("Cancelado.")
                    return 0
            count = self.service.clear_completed()
            print(colorize(f"{_check()} {count} tarefa(s) concluída(s) removida(s).", Colors.GREEN))
            return 0
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_priority(self, args: Namespace) -> int:
        """Define prioridade da tarefa."""
        try:
            priority = TaskPriority(args.level)
            task = self.service.set_priority(args.id, priority)
            print(colorize(f"{_check()} Prioridade definida: ", Colors.GREEN) + format_task(task))
            return 0
        except TaskNotFoundError as e:
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_due_date(self, args: Namespace) -> int:
        """Define ou remove data de vencimento."""
        try:
            due_date = None
            if args.date:
                try:
                    due_date = datetime.strptime(args.date, "%Y-%m-%d")
                except ValueError:
                    print(colorize(f"{_cross()} Formato de data inválido. Use YYYY-MM-DD", Colors.RED), file=sys.stderr)
                    return 1
            task = self.service.set_due_date(args.id, due_date)
            action = "definida" if due_date else "removida"
            print(colorize(f"{_check()} Data de vencimento {action}: ", Colors.GREEN) + format_task(task))
            return 0
        except TaskNotFoundError as e:
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_tag(self, args: Namespace) -> int:
        """Adiciona, remove ou limpa tags."""
        try:
            if args.clear:
                task = self.service.clear_tags(args.id)
                print(colorize(f"{_check()} Tags limpas: ", Colors.GREEN) + format_task(task))
                return 0

            if not args.tag:
                print(colorize(f"{_cross()} Informe uma tag ou use --clear", Colors.RED), file=sys.stderr)
                return 1

            if args.remove:
                task = self.service.remove_tag(args.id, args.tag)
                print(colorize(f"{_check()} Tag removida: ", Colors.GREEN) + format_task(task))
            else:
                task = self.service.add_tag(args.id, args.tag)
                print(colorize(f"{_check()} Tag adicionada: ", Colors.GREEN) + format_task(task))
            return 0
        except TaskNotFoundError as e:
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_export(self, args: Namespace) -> int:
        """Exporta tarefas para JSON, CSV ou Markdown."""
        try:
            if args.format == "json":
                output = self.service.export_json()
            elif args.format == "csv":
                output = self.service.export_csv()
            elif args.format in ("md", "markdown"):
                output = self.service.export_markdown()
            else:
                print(colorize(f"{_cross()} Formato não suportado: {args.format}", Colors.RED), file=sys.stderr)
                return 1

            if args.output:
                try:
                    with open(args.output, "w", encoding="utf-8") as f:
                        f.write(output)
                    print(colorize(f"{_check()} Exportado para {args.output}", Colors.GREEN))
                except OSError as e:
                    print(colorize(f"{_cross()} Erro ao escrever arquivo: {e}", Colors.RED), file=sys.stderr)
                    return 1
            else:
                print(output)
            return 0
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_import(self, args: Namespace) -> int:
        """Importa tarefas de JSON ou CSV."""
        try:
            # Lê arquivo ou stdin
            if args.file == "-":
                import sys
                content = sys.stdin.read()
            else:
                try:
                    with open(args.file, encoding="utf-8") as f:
                        content = f.read()
                except OSError as e:
                    print(colorize(f"{_cross()} Erro ao ler arquivo: {e}", Colors.RED), file=sys.stderr)
                    return 1

            merge = not args.replace

            if args.format == "json":
                count = self.service.import_json(content, merge=merge)
            elif args.format == "csv":
                count = self.service.import_csv(content, merge=merge)
            else:
                print(colorize(f"{_cross()} Formato não suportado: {args.format}", Colors.RED), file=sys.stderr)
                return 1

            action = "substituídas" if args.replace else "importadas"
            print(colorize(f"{_check()} {count} tarefa(s) {action} com sucesso", Colors.GREEN))
            return 0
        except ValidationError as e:
            print(colorize(f"{_cross()} Erro de validação: {e}", Colors.RED), file=sys.stderr)
            return 1
        except ServiceError as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_config(self, args: Namespace) -> int:
        """Gerencia configuração."""
        import json

        from .config import get_config, reset_config

        config = get_config()

        try:
            if args.action == "show":
                # Mostra toda a configuração
                print(json.dumps(config._data, indent=2, ensure_ascii=False))
                return 0

            elif args.action == "path":
                print(str(config.config_path))
                return 0

            elif args.action == "reset":
                reset_config()
                # Recria com defaults
                new_config = get_config()
                new_config.save()
                print(colorize(f"{_check()} Configuração resetada para padrões", Colors.GREEN))
                return 0

            elif args.action == "get":
                if not args.key:
                    print(colorize(f"{_cross()} Informe a chave (ex: display.show_priority)", Colors.RED), file=sys.stderr)
                    return 1
                # Navega na chave (ex: display.show_priority)
                parts = args.key.split(".")
                value = config._data
                for part in parts:
                    if part not in value:
                        print(colorize(f"{_cross()} Chave não encontrada: {args.key}", Colors.RED), file=sys.stderr)
                        return 1
                    value = value[part]
                print(json.dumps(value, ensure_ascii=False))
                return 0

            elif args.action == "set":
                if not args.key or args.value is None:
                    print(colorize(f"{_cross()} Informe chave e valor (ex: config set display.show_priority false)", Colors.RED), file=sys.stderr)
                    return 1
                # Navega e define
                parts = args.key.split(".")
                target = config._data
                for part in parts[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                # Converte valor
                val = args.value
                if val.lower() in ("true", "false"):
                    val = val.lower() == "true"
                elif val.isdigit():
                    val = int(val)
                target[parts[-1]] = val
                config.save()
                print(colorize(f"{_check()} Configuração salva: {args.key} = {val}", Colors.GREEN))
                return 0

        except Exception as e:
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1

        return 0

    def cmd_tui(self, args: Namespace) -> int:
        """Inicia a interface textual interativa (TUI)."""
        try:
            from .tui import run_tui
            run_tui()
            return 0
        except ImportError:
            print(colorize(f"{_cross()} Dependências da TUI não instaladas.", Colors.RED), file=sys.stderr)
            print(colorize("  Instale com: pip install 'todo-cli[tui]'", Colors.YELLOW), file=sys.stderr)
            return 1
        except Exception as e:
            print(colorize(f"{_cross()} Erro ao iniciar TUI: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_repl(self, args: Namespace) -> int:
        """Inicia o shell interativo (REPL)."""
        try:
            from .repl import run_repl
            run_repl()
            return 0
        except Exception as e:
            print(colorize(f"{_cross()} Erro ao iniciar REPL: {e}", Colors.RED), file=sys.stderr)
            return 1

    def cmd_gui(self, args: Namespace) -> int:
        """Inicia a interface gráfica (PySide6)."""
        try:
            from .gui import run_gui
            run_gui()
            return 0
        except ImportError:
            print(colorize(f"{_cross()} Dependências da GUI não instaladas.", Colors.RED), file=sys.stderr)
            print(colorize("  Instale com: pip install 'todo-cli[gui]'", Colors.YELLOW), file=sys.stderr)
            return 1
        except Exception as e:
            print(colorize(f"{_cross()} Erro ao iniciar GUI: {e}", Colors.RED), file=sys.stderr)
            return 1

    # ===== CRM HANDLERS =====

    def cmd_crm(self, args: Namespace) -> int:
        """Dispatch para subcomandos CRM."""
        if not args.crm_command:
            print(colorize("Uso: todo crm <comando>", Colors.BOLD))
            print(colorize("  Comandos: customer, deal, pipeline, stats", Colors.DIM))
            print(colorize("  Ex: todo crm customer add \"Acme\" --email a@a.com", Colors.DIM))
            print(colorize("  Use 'todo crm --help' para mais detalhes.", Colors.DIM))
            return 0
        return args.func(args)

    def cmd_crm_customer(self, args: Namespace) -> int:
        """Dispatch para subcomandos de cliente."""
        if not args.customer_command:
            print(colorize("Uso: todo crm customer <acao>", Colors.BOLD))
            print(colorize("  Ações: add, list, get, edit, status, rm", Colors.DIM))
            print(colorize("  Ex: todo crm customer add \"Acme\" --email a@a.com", Colors.DIM))
            return 0
        return args.func(args)

    def cmd_crm_deal(self, args: Namespace) -> int:
        """Dispatch para subcomandos de deal."""
        if not args.deal_command:
            print(colorize("Uso: todo crm deal <acao>", Colors.BOLD))
            print(colorize("  Ações: add, list, get, status, reopen, edit, rm", Colors.DIM))
            print(colorize("  Ex: todo crm deal add \"Proposta\" --customer abc123 --value 5000", Colors.DIM))
            return 0
        return args.func(args)

    def _handle_crm_error(self, e: Exception) -> int:
        """Helper para tratar erros comuns do CRM."""
        if isinstance(e, (CustomerNotFoundError, DealNotFoundError)):
            print(colorize(f"{_cross()} {e}", Colors.RED), file=sys.stderr)
            return 1
        if isinstance(e, CrmValidationError):
            print(colorize(f"{_cross()} Erro de validação: {e}", Colors.RED), file=sys.stderr)
            return 1
        if isinstance(e, CrmServiceError):
            print(colorize(f"{_cross()} Erro: {e}", Colors.RED), file=sys.stderr)
            return 1
        return 1

    # -- CRM CUSTOMER --

    def cmd_crm_customer_add(self, args: Namespace) -> int:
        """Adiciona novo cliente."""
        try:
            status = CustomerStatus(args.status)
            customer = self.crm_service.add_customer(
                name=args.name,
                email=args.email,
                phone=args.phone,
                company=args.company,
                notes=args.notes,
                status=status,
            )
            print(colorize(f"{_check()} Cliente criado: ", Colors.GREEN) + format_customer(customer))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_customer_list(self, args: Namespace) -> int:
        """Lista clientes com filtros."""
        try:
            status = CustomerStatus(args.status) if args.status else None
            customers = self.crm_service.list_customers(status=status, search=args.search)
            print_customers(customers, show_dates=args.dates)
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_customer_get(self, args: Namespace) -> int:
        """Obtém cliente pelo ID."""
        try:
            customer = self.crm_service.get_customer(args.id)
            print(format_customer(customer, show_dates=True))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_customer_edit(self, args: Namespace) -> int:
        """Edita campos do cliente."""
        try:
            customer = self.crm_service.update_customer(
                customer_id=args.id,
                name=args.name,
                email=args.email,
                phone=args.phone,
                company=args.company,
                notes=args.notes,
            )
            print(colorize(f"{_check()} Cliente atualizado: ", Colors.GREEN) + format_customer(customer))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_customer_status(self, args: Namespace) -> int:
        """Define status do cliente."""
        try:
            status = CustomerStatus(args.status)
            customer = self.crm_service.set_customer_status(args.id, status)
            print(colorize(f"{_check()} Status do cliente definido: ", Colors.GREEN) + format_customer(customer))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_customer_rm(self, args: Namespace) -> int:
        """Remove cliente."""
        try:
            customer = self.crm_service.get_customer(args.id)  # Valida existência
            if not args.yes:
                confirm = input(f"Deletar cliente '{customer.name}'? [s/N] ").strip().lower()
                if confirm not in ("s", "sim", "y", "yes"):
                    print("Cancelado.")
                    return 0
            self.crm_service.delete_customer(args.id)
            print(colorize(f"{_check()} Cliente removido.", Colors.GREEN))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    # -- CRM DEAL --

    def cmd_crm_deal_add(self, args: Namespace) -> int:
        """Adiciona novo deal."""
        try:
            deal = self.crm_service.add_deal(
                title=args.title,
                customer_id=args.customer,
                value=args.value,
                currency=args.currency,
                notes=args.notes,
            )
            print(colorize(f"{_check()} Deal criado: ", Colors.GREEN) + format_deal(deal, show_customer=True))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_deal_list(self, args: Namespace) -> int:
        """Lista deals com filtros."""
        try:
            status = DealStatus(args.status) if args.status else None
            deals = self.crm_service.list_deals(
                status=status,
                customer_id=args.customer,
                search=args.search,
            )
            print_deals(deals, show_customer=args.customer_id)
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_deal_get(self, args: Namespace) -> int:
        """Obtém deal pelo ID."""
        try:
            deal = self.crm_service.get_deal(args.id)
            print(format_deal(deal, show_customer=True))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_deal_status(self, args: Namespace) -> int:
        """Define status do deal."""
        try:
            status = DealStatus(args.status)
            deal = self.crm_service.update_deal_status(args.id, status)
            print(colorize(f"{_check()} Status do deal definido: ", Colors.GREEN) + format_deal(deal))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_deal_reopen(self, args: Namespace) -> int:
        """Reabre deal won/lost."""
        try:
            deal = self.crm_service.reopen_deal(args.id)
            print(colorize(f"{_check()} Deal reaberto: ", Colors.GREEN) + format_deal(deal))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_deal_edit(self, args: Namespace) -> int:
        """Edita campos do deal."""
        try:
            deal = self.crm_service.update_deal(
                deal_id=args.id,
                title=args.title,
                value=args.value,
                currency=args.currency,
                notes=args.notes,
            )
            print(colorize(f"{_check()} Deal atualizado: ", Colors.GREEN) + format_deal(deal))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_deal_rm(self, args: Namespace) -> int:
        """Remove deal."""
        try:
            deal = self.crm_service.get_deal(args.id)  # Valida existência
            if not args.yes:
                confirm = input(f"Deletar deal '{deal.title}'? [s/N] ").strip().lower()
                if confirm not in ("s", "sim", "y", "yes"):
                    print("Cancelado.")
                    return 0
            self.crm_service.delete_deal(args.id)
            print(colorize(f"{_check()} Deal removido.", Colors.GREEN))
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_pipeline(self, args: Namespace) -> int:
        """Mostra funil de vendas."""
        try:
            pipeline = self.crm_service.pipeline()
            print_pipeline(pipeline)
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    def cmd_crm_stats(self, args: Namespace) -> int:
        """Mostra estatísticas do CRM."""
        try:
            stats = self.crm_service.stats()
            print_crm_stats(stats)
            return 0
        except CrmServiceError as e:
            return self._handle_crm_error(e)

    # ===== ENTRY POINT =====

    def run(self, argv: list[str] | None = None) -> int:
        """Ponto de entrada principal.

        Args:
            argv: Lista de argumentos (sys.argv[1:]). Se None, usa sys.argv[1:].

        Returns:
            Exit code (0 = sucesso, !=0 = erro).
        """
        try:
            args = self.parser.parse_args(argv)
        except SystemExit as e:
            # argparse chama sys.exit(0) para --help e --version
            return e.code if isinstance(e.code, int) else 0

        if not args.command:
            self.parser.print_help()
            return 0

        return args.func(args)


def main() -> int:
    """Função principal chamada pelo entry point (pip install)."""
    cli = TodoCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
