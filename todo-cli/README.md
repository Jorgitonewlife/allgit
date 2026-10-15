# Todo CLI

Gerenciador de tarefas em linha de comando (CLI) — projeto didático em Python, com módulo CRM/Sales.

## Funcionalidades

- ✅ Adicionar tarefas com título e descrição
- 📋 Listar tarefas (com filtros por status e busca textual)
- ▶️ Iniciar tarefa (marcar como "em andamento")
- ✅ Concluir tarefa
- 🔄 Reabrir tarefa concluída
- ✏️ Editar título e/ou descrição
- 🗑️ Deletar tarefa
- 📊 Estatísticas (total, pendentes, em andamento, concluídas)
- 🧹 Limpar tarefas concluídas
- 💾 Persistência automática em JSON (`~/.todo_cli_tasks.json`)
- 🔍 Busca por ID com prefixo (mínimo 3 caracteres)

### Módulo CRM/Sales

- 👥 **Clientes**: criar, listar (filtros por status e busca), editar, mudar status (`lead`/`active`/`inactive`)
- 💼 **Negócios (Deals)**: criar vinculado a cliente, valores monetários, status (`open`/`proposal`/`won`/`lost`), `reopen`
- 📈 **Pipeline**: funil de vendas com contagem e valor por status
- 📊 **Stats**: resumo de clientes e deals
- 🔒 Regra: não é possível deletar cliente com deals vinculados (bloqueio)
- 💾 Persistência em JSON separado (`~/.todo_cli_crm.json`), configurável via `TODO_CRM_FILE`

## Instalação

```bash
# Clone o repositório
cd todo-cli

# (Opcional) Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Instale em modo desenvolvimento
pip install -e .
# Ou com dependências de dev:
pip install -e ".[dev]"
```

## Uso

```bash
# Adicionar tarefa
todo add "Estudar Python" -d "Fazer exercícios de lista"

# Listar todas
todo list
todo ls

# Filtrar por status
todo list --status pending
todo list --status in_progress
todo list --status done

# Busca textual
todo list --search python

# Marcar como concluída
todo done abc123

# Iniciar (em andamento)
todo start abc123

# Reabrir
todo reopen abc123

# Editar
todo edit abc123 -t "Novo título" -d "Nova descrição"

# Deletar
todo delete abc123
todo rm abc123 -y  # sem confirmação

# Estatísticas
todo stats

# Limpar concluídas
todo clear-done -y

# Ajuda
todo --help
todo add --help
```

## Uso do Módulo CRM

```bash
# Clientes
todo crm customer add "Acme Corp" --email contato@acme.com --company "Acme LTDA"
todo crm customer add "Beta SA" --status active
todo crm customer list
todo crm customer list --status lead --search acme
todo crm customer get abc123
todo crm customer edit abc123 --email novo@acme.com --phone 1199999
todo crm customer status abc123 active
todo crm customer rm abc123 -y

# Negócios (Deals)
todo crm deal add "Proposta site" --customer abc123 --value 5000
todo crm deal add "Consultoria" --customer abc123 --value 12000 --currency BRL
todo crm deal list --status open
todo crm deal list --customer abc123 --customer-id
todo crm deal get def456
todo crm deal status def456 proposal
todo crm deal status def456 won
todo crm deal reopen def456
todo crm deal edit def456 --value 6000
todo crm deal rm def456 -y

# Relatórios
todo crm pipeline
todo crm stats
```

## Arquitetura

```
todo/
├── __init__.py      # Exports públicos
├── models.py        # Task, TaskStatus (dataclasses + Enum)
├── storage.py       # Persistência JSON (Storage)
├── service.py       # Lógica de negócio (TodoService)
├── cli.py           # Interface argparse (TodoCLI)
└── crm/             # Módulo CRM (Customers & Deals)
    ├── __init__.py  # Exports do módulo
    ├── models.py    # Customer, Deal, enums
    ├── storage.py   # CrmStorage (JSON atômico)
    └── service.py   # CrmService (regras de negócio)
```

**Princípios:**
- **Separação de responsabilidades**: Models ↔ Storage ↔ Service ↔ CLI
- **Injeção de dependência**: Service recebe Storage, CLI recebe Service
- **Testável**: Core (models, storage, service) testado isoladamente
- **Type hints**: Tipagem completa (Python 3.10+)
- **Zero dependências runtime**: Apenas stdlib

## Testes

```bash
# Rodar todos
pytest

# Com cobertura
pytest --cov=todo

# Verboso
pytest -v
```

## Qualidade de Código

```bash
# Lint (ruff)
ruff check .

# Format (black)
black .

# Type check (mypy)
mypy todo/
```

## Estrutura do Projeto

```
todo-cli/
├── todo/                 # Pacote principal
│   ├── __init__.py
│   ├── models.py
│   ├── storage.py
│   ├── service.py
│   ├── cli.py
│   └── crm/              # Módulo CRM
│       ├── __init__.py
│       ├── models.py
│       ├── storage.py
│       └── service.py
├── tests/
│   ├── test_service.py   # 32 testes cobrindo service
│   ├── test_cli.py       # Testes da CLI de tarefas
│   ├── test_crm_service.py  # 59 testes do service CRM
│   └── test_crm_cli.py   # 28 testes da CLI CRM
├── main.py               # Entry point
├── pyproject.toml        # Configuração moderna (build, lint, test)
├── requirements.txt      # Runtime (vazio - só stdlib)
├── requirements-dev.txt  # Dev tools
└── README.md
```

## Conceitos Demonstrados

| Conceito | Onde |
|----------|------|
| Dataclasses + `field(default_factory=...)` | `models.py` |
| Enum com `str` para serialização JSON | `models.py` |
| `@classmethod` para factory (`from_dict`) | `models.py` |
| Pathlib para caminhos cross-platform | `storage.py` |
| Escrita atômica (tmp + rename) | `storage.py` |
| Lazy loading + cache em memória | `service.py` |
| Exceções customizadas hierárquicas | `service.py` |
| Injeção de dependência | `service.py`, `cli.py` |
| argparse com subcomandos + aliases | `cli.py` |
| Detecção de suporte Unicode no terminal | `cli.py` |
| Fixtures pytest + tempfile | `tests/test_service.py` |
| pyproject.toml moderno (PEP 621) | `pyproject.toml` |
| ruff + black + mypy config | `pyproject.toml` |

## Próximos Passos (Roadmap)

- [x] Testes para CLI (`tests/test_cli.py`)
- [x] Adicionar `due_date` (data de vencimento)
- [x] Prioridade (alta/média/baixa)
- [x] Tags/categorias
- [x] Exportar/importar (CSV, Markdown)
- [x] Configuração via arquivo (TOML/YAML)
- [x] Shell interativo (REPL)
- [x] TUI com `textual` ou `rich`
- [x] Módulo CRM/Sales (Customers & Deals)
- [ ] Empacotamento para PyPI

## Licença

MIT