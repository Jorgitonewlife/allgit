"""Camada de persistência do módulo CRM: salva e carrega dados em JSON.

Responsabilidade única: saber *onde* e *como* gravar clientes e negócios.
Não contém lógica de negócio (regras, validações) — isso fica no Service.
"""

import json
from pathlib import Path

from .models import Customer, Deal

# Caminho padrão do arquivo de dados do CRM (pode ser sobrescrito via config)
DEFAULT_CRM_FILE = Path.home() / ".todo_cli_crm.json"


class CrmStorageError(Exception):
    """Exceção base para erros de persistência do CRM."""
    pass


class CrmStorage:
    """Gerencia leitura/escrita de clientes e negócios em disco (JSON).

    Princípios (idênticos ao Storage de tarefas):
    - Falha explícita: lança exceção se não conseguir ler/escrever
    - Atomicidade: escreve em arquivo temporário e renomeia
    - Encoding UTF-8 sempre
    """

    def __init__(self, file_path: Path | None = None):
        """Inicializa o storage.

        Args:
            file_path: Caminho do arquivo JSON. Se None, usa DEFAULT_CRM_FILE.
        """
        self.file_path = Path(file_path) if file_path else DEFAULT_CRM_FILE

    def _ensure_file_exists(self) -> None:
        """Cria arquivo vazio (dict com listas vazias) se não existir."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text('{"customers": [], "deals": []}', encoding="utf-8")

    def load(self) -> dict[str, list]:
        """Carrega clientes e negócios do arquivo JSON.

        Returns:
            Dict com chaves "customers" (list[Customer]) e "deals" (list[Deal]).
            Pode conter listas vazias.

        Raises:
            CrmStorageError: Se JSON inválido ou erro de I/O.
        """
        self._ensure_file_exists()

        try:
            content = self.file_path.read_text(encoding="utf-8")
        except OSError as e:
            raise CrmStorageError(f"Erro ao ler arquivo do CRM: {e}") from e

        if not content.strip():
            return {"customers": [], "deals": []}

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise CrmStorageError(f"Arquivo do CRM corrompido (JSON inválido): {e}") from e

        customers = []
        for item in data.get("customers", []):
            try:
                customers.append(Customer.from_dict(item))
            except (KeyError, ValueError, TypeError) as e:
                print(f"Aviso: cliente inválido ignorado: {item} ({e})")

        deals = []
        for item in data.get("deals", []):
            try:
                deals.append(Deal.from_dict(item))
            except (KeyError, ValueError, TypeError) as e:
                print(f"Aviso: deal inválido ignorado: {item} ({e})")

        return {"customers": customers, "deals": deals}

    def save(self, customers: list[Customer], deals: list[Deal]) -> None:
        """Salva clientes e negócios no arquivo JSON (escrita atômica).

        Args:
            customers: Lista de objetos Customer a persistir.
            deals: Lista de objetos Deal a persistir.

        Raises:
            CrmStorageError: Se erro de serialização ou I/O.
        """
        data = {
            "customers": [c.to_dict() for c in customers],
            "deals": [d.to_dict() for d in deals],
        }

        try:
            json_content = json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as e:
            raise CrmStorageError(f"Erro ao serializar CRM para JSON: {e}") from e

        # Escrita atômica: escreve em .tmp e renomeia
        tmp_path = self.file_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(json_content, encoding="utf-8")
            tmp_path.replace(self.file_path)
        except OSError as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise CrmStorageError(f"Erro ao salvar arquivo do CRM: {e}") from e

    def clear(self) -> None:
        """Remove todos os clientes e negócios (salva estrutura vazia)."""
        self.save([], [])
