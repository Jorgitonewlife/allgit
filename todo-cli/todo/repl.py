"""REPL (Read-Eval-Print Loop) interativo para o Todo CLI.

Permite usar o todo de forma interativa com histórico, autocomplete e ajuda.
"""

import cmd
import shlex

from .cli import TodoCLI


class TodoREPL(cmd.Cmd):
    """Shell interativo para o Todo CLI."""

    intro = """
+--------------------------------------------------------------+
|                    TODO CLI - REPL Interativo                 |
|                                                              |
|  Digite 'help' para lista de comandos                        |
|  Digite 'quit' ou 'exit' para sair                           |
|  Use TAB para autocomplete                                   |
|  Use setas cima/baixo para historico                         |
+--------------------------------------------------------------+
"""
    prompt = "todo> "
    file = None

    def __init__(self, cli: TodoCLI) -> None:
        super().__init__()
        self.cli = cli
        # Comandos disponíveis para autocomplete
        self._commands = [
            "add", "list", "ls", "done", "start", "reopen",
            "edit", "delete", "rm", "stats", "clear-done",
            "priority", "due-date", "due", "tag",
            "export", "import", "config", "tui",
            "crm", "customer", "deal", "pipeline",
            "help", "quit", "exit", "history"
        ]

    def default(self, line: str) -> bool:
        """Executa comandos não reconhecidos pelo cmd.Cmd."""
        if not line.strip():
            return False

        try:
            argv = shlex.split(line)
            exit_code = self.cli.run(argv)
            if exit_code != 0:
                print(f"[Exit code: {exit_code}]")
        except Exception as e:
            print(f"Erro: {e}")
        return False

    def do_quit(self, arg: str) -> bool:
        """Sai do REPL."""
        print("Até logo!")
        return True

    def do_exit(self, arg: str) -> bool:
        """Sai do REPL (alias para quit)."""
        return self.do_quit(arg)

    def do_history(self, arg: str) -> bool:
        """Mostra histórico de comandos."""
        try:
            import readline
            for i in range(readline.get_current_history_length()):
                print(f"  {i+1}:  {readline.get_history_item(i+1)}")
        except ImportError:
            print("Histórico não disponível (readline não instalado)")
        return False

    def complete(self, text: str, state: int) -> str | None:
        """Autocomplete para comandos."""
        options = [cmd for cmd in self._commands if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    def precmd(self, line: str) -> str:
        """Chamado antes de executar comando."""
        return line

    def postcmd(self, stop: bool, line: str) -> bool:
        """Chamado depois de executar comando."""
        return stop

    def emptyline(self) -> bool:
        """Linha vazia - não faz nada."""
        return False


def run_repl() -> None:
    """Entry point para executar o REPL."""
    import sys
    # Verifica se --help foi passado antes de iniciar o REPL
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
+--------------------------------------------------------------+
|                    TODO CLI - REPL Interativo                 |
|                                                              |
|  Uso: todo-repl [opcoes]                                     |
|                                                              |
|  Opcoes:                                                     |
|    -h, --help     Mostra esta ajuda e sai                    |
|                                                              |
|  Dentro do REPL:                                             |
|    help           Lista comandos disponiveis                 |
|    quit / exit    Sai do REPL                                |
|    history        Mostra historico de comandos               |
|    TAB            Autocomplete de comandos                   |
|    setas          Navega historico (cima/baixo)              |
|                                                              |
|  Exemplos:                                                   |
|    todo> add "Estudar Python" -p high --due 2026-12-31       |
|    todo> list --status pending                               |
|    todo> done abc123                                         |
|    todo> tag abc123 trabalho,urgente                         |
|    todo> export json -o backup.json                          |
|    todo> config set display.show_priority false              |
+--------------------------------------------------------------+
""")
        return

    cli = TodoCLI()
    repl = TodoREPL(cli)
    try:
        repl.cmdloop()
    except KeyboardInterrupt:
        print("\nAte logo!")
    except EOFError:
        print("\nAte logo!")


if __name__ == "__main__":
    run_repl()
