"""Camada de persistência: salva e carrega tarefas em arquivo JSON.

Responsabilidade única: saber *onde* e *como* gravar dados.
Não contém lógica de negócio (regras, validações) — isso fica no Service.
"""

import json
from pathlib import Path

from .models import Task

# Caminho padrão do arquivo de dados (pode ser sobrescrito via variável de ambiente)
DEFAULT_DATA_FILE = Path.home() / ".todo_cli_tasks.json"


class StorageError(Exception):
    """Exceção base para erros de persistência."""
    pass


class Storage:
    """Gerencia leitura/escrita de tarefas em disco (JSON).

    Princípios:
    - Falha explícita: lança exceção se não conseguir ler/escrever
    - Atomicidade: escreve em arquivo temporário e renomeia (evita corrupção)
    - Encoding UTF-8 sempre
    """

    def __init__(self, file_path: Path | None = None):
        """Inicializa o storage.

        Args:
            file_path: Caminho do arquivo JSON. Se None, usa DEFAULT_DATA_FILE.
        """
        self.file_path = Path(file_path) if file_path else DEFAULT_DATA_FILE

    def _ensure_file_exists(self) -> None:
        """Cria arquivo vazio (lista []) se não existir.

        'mkdir(parents=True, exist_ok=True)' cria diretórios pais se necessário.
        'touch()' cria o arquivo vazio.
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def load(self) -> list[Task]:
        """Carrega todas as tarefas do arquivo JSON.

        Returns:
            Lista de objetos Task (pode ser vazia).

        Raises:
            StorageError: Se arquivo não existe, JSON inválido ou erro de I/O.
        """
        self._ensure_file_exists()

        try:
            content = self.file_path.read_text(encoding="utf-8")
        except OSError as e:
            raise StorageError(f"Erro ao ler arquivo de tarefas: {e}") from e

        if not content.strip():
            return []  # Arquivo vazio -> lista vazia

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise StorageError(f"Arquivo de tarefas corrompido (JSON inválido): {e}") from e

        # Converte cada dict em objeto Task
        tasks = []
        for item in data:
            try:
                task = Task.from_dict(item)
                tasks.append(task)
            except (KeyError, ValueError, TypeError) as e:
                # Item corrompido: loga e pula (não quebra tudo)
                # Em produção, usaríamos logging estruturado
                print(f"Aviso: tarefa inválida ignorada: {item} ({e})")

        return tasks

    def save(self, tasks: list[Task]) -> None:
        """Salva a lista de tarefas no arquivo JSON (escrita atômica).

        Args:
            tasks: Lista de objetos Task a persistir.

        Raises:
            StorageError: Se erro de serialização ou I/O.
        """
        # Converte cada Task para dict serializável
        data = [task.to_dict() for task in tasks]

        try:
            # Serializa com indentação legível (indent=2)
            json_content = json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as e:
            raise StorageError(f"Erro ao serializar tarefas para JSON: {e}") from e

        # Escrita atômica: escreve em .tmp e renomeia
        # Isso evita arquivo corrompido se o processo morrer no meio da escrita
        tmp_path = self.file_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(json_content, encoding="utf-8")
            tmp_path.replace(self.file_path)  # Atômico no POSIX e Windows (Python 3.3+)
        except OSError as e:
            # Limpa arquivo temporário se falhou
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise StorageError(f"Erro ao salvar arquivo de tarefas: {e}") from e

    def clear(self) -> None:
        """Remove todas as tarefas (salva lista vazia)."""
        self.save([])
