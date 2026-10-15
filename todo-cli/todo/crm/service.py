"""Camada de serviço do módulo CRM: lógica de negócio e regras.

Esta camada NÃO sabe como dados são salvos (CrmStorage) nem como são exibidos (CLI).
Ela apenas coordena: valida entrada, aplica regras, chama storage.
"""

from datetime import datetime

from ..config import get_config
from .models import Customer, CustomerStatus, Deal, DealStatus
from .storage import CrmStorage


class CrmServiceError(Exception):
    """Exceção base para erros de regra de negócio do CRM."""
    pass


class CustomerNotFoundError(CrmServiceError):
    """Lançada quando um cliente não é encontrado pelo ID."""
    pass


class DealNotFoundError(CrmServiceError):
    """Lançada quando um deal não é encontrado pelo ID."""
    pass


class CrmValidationError(CrmServiceError):
    """Lançada quando dados de entrada são inválidos."""
    pass


class CrmService:
    """Orquestra operações de CRM: clientes, deals, pipeline.

    Responsabilidades:
    - Validar dados de entrada (tamanho, obrigatoriedade)
    - Aplicar regras de negócio (transições de status, bloqueio de delete)
    - Delegar persistência ao CrmStorage
    - Retornar objetos de domínio (Customer, Deal) ou levantar exceções claras
    """

    def __init__(self, storage: CrmStorage | None = None):
        """Inicializa o service com um storage (injeção de dependência).

        Args:
            storage: Instância de CrmStorage. Se None, cria uma usando config.
        """
        if storage is None:
            config = get_config()
            storage = CrmStorage(file_path=config.get_crm_path())
        self._storage = storage
        # Cache em memória para evitar ler disco a cada operação
        self._customers: list[Customer] = []
        self._deals: list[Deal] = []
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Carrega dados do disco se ainda não carregou (lazy loading)."""
        if not self._loaded:
            data = self._storage.load()
            self._customers = data["customers"]
            self._deals = data["deals"]
            self._loaded = True

    def _persist(self) -> None:
        """Salva o estado atual no disco."""
        self._storage.save(self._customers, self._deals)

    def _find_customer_by_id(self, customer_id: str) -> Customer:
        """Busca cliente por ID (prefixo mínimo 3 chars).

        Raises:
            CustomerNotFoundError: Se não encontrar ou ID ambíguo.
        """
        if len(customer_id) < 3:
            raise CrmValidationError("ID deve ter pelo menos 3 caracteres")

        matches = [c for c in self._customers if c.id.startswith(customer_id.lower())]

        if not matches:
            raise CustomerNotFoundError(f"Cliente '{customer_id}' não encontrado")
        if len(matches) > 1:
            raise CustomerNotFoundError(
                f"ID '{customer_id}' é ambíguo (encontrados {len(matches)} clientes). "
                "Use mais caracteres."
            )
        return matches[0]

    def _find_deal_by_id(self, deal_id: str) -> Deal:
        """Busca deal por ID (prefixo mínimo 3 chars).

        Raises:
            DealNotFoundError: Se não encontrar ou ID ambíguo.
        """
        if len(deal_id) < 3:
            raise CrmValidationError("ID deve ter pelo menos 3 caracteres")

        matches = [d for d in self._deals if d.id.startswith(deal_id.lower())]

        if not matches:
            raise DealNotFoundError(f"Deal '{deal_id}' não encontrado")
        if len(matches) > 1:
            raise DealNotFoundError(
                f"ID '{deal_id}' é ambíguo (encontrados {len(matches)} deals). "
                "Use mais caracteres."
            )
        return matches[0]

    def _validate_customer_payload(
        self, name: str, email: str = "", phone: str = "", company: str = "", notes: str = ""
    ) -> dict:
        """Valida e normaliza dados de cliente."""
        name = name.strip()
        if not name:
            raise CrmValidationError("Nome é obrigatório")
        if len(name) > 200:
            raise CrmValidationError("Nome deve ter no máximo 200 caracteres")

        email = email.strip()
        if email and "@" not in email:
            raise CrmValidationError("Email inválido (deve conter @)")

        phone = phone.strip()
        company = company.strip()
        notes = notes.strip()
        if len(notes) > 1000:
            raise CrmValidationError("Notas devem ter no máximo 1000 caracteres")

        return {"name": name, "email": email, "phone": phone, "company": company, "notes": notes}

    def _validate_deal_payload(self, title: str, value: float) -> dict:
        """Valida e normaliza dados de deal."""
        title = title.strip()
        if not title:
            raise CrmValidationError("Título é obrigatório")
        if len(title) > 200:
            raise CrmValidationError("Título deve ter no máximo 200 caracteres")

        if value < 0:
            raise CrmValidationError("Valor não pode ser negativo")

        return {"title": title, "value": value}

    # ===== CUSTOMERS =====

    def add_customer(
        self,
        name: str,
        email: str = "",
        phone: str = "",
        company: str = "",
        notes: str = "",
        status: CustomerStatus = CustomerStatus.LEAD,
    ) -> Customer:
        """Cria um novo cliente.

        Args:
            name: Nome obrigatório (1-200 chars).
            email: Email opcional (validação básica com @).
            phone: Telefone opcional.
            company: Empresa opcional.
            notes: Notas livres (máx 1000 chars).
            status: Status inicial (padrão: lead).

        Returns:
            Customer criado.

        Raises:
            CrmValidationError: Se nome vazio, email inválido ou notas longas demais.
        """
        self._ensure_loaded()
        data = self._validate_customer_payload(name, email, phone, company, notes)

        customer = Customer(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            company=data["company"],
            notes=data["notes"],
            status=status,
        )
        self._customers.append(customer)
        self._persist()
        return customer

    def list_customers(
        self,
        status: CustomerStatus | None = None,
        search: str | None = None,
    ) -> list[Customer]:
        """Lista clientes com filtros opcionais.

        Args:
            status: Filtrar por status (lead, active, inactive).
            search: Busca textual em name, email, company (case-insensitive).

        Returns:
            Lista de clientes filtrados (mais recentes primeiro).
        """
        self._ensure_loaded()
        customers = self._customers

        if status:
            customers = [c for c in customers if c.status == status]

        if search:
            search_lower = search.lower()
            customers = [
                c for c in customers
                if search_lower in c.name.lower()
                or search_lower in c.email.lower()
                or search_lower in c.company.lower()
            ]

        customers.sort(key=lambda c: c.updated_at, reverse=True)
        return customers

    def get_customer(self, customer_id: str) -> Customer:
        """Obtém um cliente pelo ID (ou prefixo)."""
        self._ensure_loaded()
        return self._find_customer_by_id(customer_id)

    def update_customer(
        self,
        customer_id: str,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None,
        notes: str | None = None,
    ) -> Customer:
        """Atualiza campos de um cliente (apenas os informados).

        Raises:
            CustomerNotFoundError: Se ID não encontrado.
            CrmValidationError: Se nome vazio ou email inválido.
        """
        self._ensure_loaded()
        customer = self._find_customer_by_id(customer_id)

        if name is not None:
            name_stripped = name.strip()
            if not name_stripped:
                raise CrmValidationError("Nome não pode ser vazio")
            if len(name_stripped) > 200:
                raise CrmValidationError("Nome deve ter no máximo 200 caracteres")
            customer.name = name_stripped

        if email is not None:
            email_stripped = email.strip()
            if email_stripped and "@" not in email_stripped:
                raise CrmValidationError("Email inválido (deve conter @)")
            customer.email = email_stripped

        if phone is not None:
            customer.phone = phone.strip()

        if company is not None:
            customer.company = company.strip()

        if notes is not None:
            notes_stripped = notes.strip()
            if len(notes_stripped) > 1000:
                raise CrmValidationError("Notas devem ter no máximo 1000 caracteres")
            customer.notes = notes_stripped

        customer.updated_at = datetime.now()
        self._persist()
        return customer

    def set_customer_status(self, customer_id: str, status: CustomerStatus) -> Customer:
        """Atualiza o status do cliente.

        Raises:
            CustomerNotFoundError: Se ID não encontrado.
        """
        self._ensure_loaded()
        customer = self._find_customer_by_id(customer_id)
        customer.set_status(status)
        self._persist()
        return customer

    def delete_customer(self, customer_id: str) -> None:
        """Remove um cliente permanentemente.

        Regra: bloqueia se o cliente possuir deals vinculados.

        Raises:
            CustomerNotFoundError: Se ID não encontrado.
            CrmValidationError: Se cliente possui deals.
        """
        self._ensure_loaded()
        customer = self._find_customer_by_id(customer_id)

        has_deals = any(d.customer_id == customer.id for d in self._deals)
        if has_deals:
            raise CrmValidationError(
                f"Cliente '{customer.name}' possui deals vinculados. "
                "Remova ou reatribua os deals antes de deletar."
            )

        self._customers.remove(customer)
        self._persist()

    # ===== DEALS =====

    def add_deal(
        self,
        title: str,
        customer_id: str,
        value: float = 0.0,
        currency: str = "BRL",
        notes: str = "",
        status: DealStatus = DealStatus.OPEN,
    ) -> Deal:
        """Cria um novo deal vinculado a um cliente.

        Args:
            title: Título obrigatório (1-200 chars).
            customer_id: ID (ou prefixo) do cliente vinculado.
            value: Valor monetário (>= 0).
            currency: Moeda (padrão BRL).
            notes: Notas livres (máx 1000 chars).
            status: Status inicial (padrão: open).

        Returns:
            Deal criado.

        Raises:
            CustomerNotFoundError: Se customer_id não encontrado.
            CrmValidationError: Se título vazio, valor negativo ou notas longas.
        """
        self._ensure_loaded()
        customer = self._find_customer_by_id(customer_id)
        data = self._validate_deal_payload(title, value)

        notes = notes.strip()
        if len(notes) > 1000:
            raise CrmValidationError("Notas devem ter no máximo 1000 caracteres")

        deal = Deal(
            title=data["title"],
            customer_id=customer.id,
            value=data["value"],
            currency=currency.strip().upper() or "BRL",
            notes=notes,
            status=status,
        )
        self._deals.append(deal)
        self._persist()
        return deal

    def list_deals(
        self,
        status: DealStatus | None = None,
        customer_id: str | None = None,
        search: str | None = None,
    ) -> list[Deal]:
        """Lista deals com filtros opcionais.

        Args:
            status: Filtrar por status (open, proposal, won, lost).
            customer_id: Filtrar por cliente (ID ou prefixo).
            search: Busca textual em title e notes (case-insensitive).

        Returns:
            Lista de deals filtrados (mais recentes primeiro).
        """
        self._ensure_loaded()
        deals = self._deals

        if status:
            deals = [d for d in deals if d.status == status]

        if customer_id:
            customer = self._find_customer_by_id(customer_id)
            deals = [d for d in deals if d.customer_id == customer.id]

        if search:
            search_lower = search.lower()
            deals = [
                d for d in deals
                if search_lower in d.title.lower() or search_lower in d.notes.lower()
            ]

        deals.sort(key=lambda d: d.updated_at, reverse=True)
        return deals

    def get_deal(self, deal_id: str) -> Deal:
        """Obtém um deal pelo ID (ou prefixo)."""
        self._ensure_loaded()
        return self._find_deal_by_id(deal_id)

    def update_deal_status(self, deal_id: str, status: DealStatus) -> Deal:
        """Atualiza o status do deal com regras de transição.

        Regras:
        - won/lost são estados finais; só podem ser alterados via reopen.
        - won e lost setam closed_at; open/proposal limpa closed_at.

        Raises:
            DealNotFoundError: Se ID não encontrado.
            CrmValidationError: Se tentar alterar status de deal won/lost.
        """
        self._ensure_loaded()
        deal = self._find_deal_by_id(deal_id)

        if deal.is_closed() and status != deal.status:
            raise CrmValidationError(
                f"Deal '{deal.title}' já está {'won' if deal.status == DealStatus.WON else 'lost'}. "
                "Use 'reopen' para reabrir antes de mudar o status."
            )

        deal.set_status(status)
        self._persist()
        return deal

    def reopen_deal(self, deal_id: str) -> Deal:
        """Reabre um deal won/lost (volta para open, limpa closed_at).

        Raises:
            DealNotFoundError: Se ID não encontrado.
            CrmValidationError: Se deal já está open ou proposal.
        """
        self._ensure_loaded()
        deal = self._find_deal_by_id(deal_id)

        if not deal.is_closed():
            raise CrmValidationError(
                f"Deal '{deal.title}' não está fechado (won/lost)."
            )

        deal.reopen()
        self._persist()
        return deal

    def update_deal(
        self,
        deal_id: str,
        title: str | None = None,
        value: float | None = None,
        currency: str | None = None,
        notes: str | None = None,
    ) -> Deal:
        """Atualiza campos de um deal (apenas os informados).

        Raises:
            DealNotFoundError: Se ID não encontrado.
            CrmValidationError: Se título vazio, valor negativo ou deal fechado.
        """
        self._ensure_loaded()
        deal = self._find_deal_by_id(deal_id)

        if deal.is_closed():
            raise CrmValidationError(
                f"Deal '{deal.title}' está fechado (won/lost). "
                "Use 'reopen' para reabrir antes de editar."
            )

        if title is not None:
            title_stripped = title.strip()
            if not title_stripped:
                raise CrmValidationError("Título não pode ser vazio")
            if len(title_stripped) > 200:
                raise CrmValidationError("Título deve ter no máximo 200 caracteres")
            deal.title = title_stripped

        if value is not None:
            if value < 0:
                raise CrmValidationError("Valor não pode ser negativo")
            deal.value = value

        if currency is not None:
            deal.currency = currency.strip().upper()

        if notes is not None:
            notes_stripped = notes.strip()
            if len(notes_stripped) > 1000:
                raise CrmValidationError("Notas devem ter no máximo 1000 caracteres")
            deal.notes = notes_stripped

        deal.updated_at = datetime.now()
        self._persist()
        return deal

    def delete_deal(self, deal_id: str) -> None:
        """Remove um deal permanentemente.

        Raises:
            DealNotFoundError: Se ID não encontrado.
        """
        self._ensure_loaded()
        deal = self._find_deal_by_id(deal_id)
        self._deals.remove(deal)
        self._persist()

    # ===== RELATÓRIOS =====

    def pipeline(self) -> dict:
        """Retorna o funil de vendas: contagem e valor somado por status.

        Returns:
            Dict com:
            - "by_status": lista de dicts (status, count, total_value) para open/proposal/won/lost
            - "total_value": soma dos valores de todos os deals
            - "won_value": soma dos valores de deals won
            - "open_value": soma dos valores de deals open + proposal
        """
        self._ensure_loaded()

        by_status = []
        for status in (DealStatus.OPEN, DealStatus.PROPOSAL, DealStatus.WON, DealStatus.LOST):
            status_deals = [d for d in self._deals if d.status == status]
            by_status.append({
                "status": status.value,
                "count": len(status_deals),
                "total_value": sum(d.value for d in status_deals),
            })

        total_value = sum(d.value for d in self._deals)
        won_value = sum(d.value for d in self._deals if d.status == DealStatus.WON)
        open_value = sum(
            d.value for d in self._deals if d.status in (DealStatus.OPEN, DealStatus.PROPOSAL)
        )

        return {
            "by_status": by_status,
            "total_value": total_value,
            "won_value": won_value,
            "open_value": open_value,
        }

    def stats(self) -> dict:
        """Retorna estatísticas rápidas de clientes e deals."""
        self._ensure_loaded()

        customers_by_status = {
            "lead": sum(1 for c in self._customers if c.status == CustomerStatus.LEAD),
            "active": sum(1 for c in self._customers if c.status == CustomerStatus.ACTIVE),
            "inactive": sum(1 for c in self._customers if c.status == CustomerStatus.INACTIVE),
        }

        deals_by_status = {
            "open": sum(1 for d in self._deals if d.status == DealStatus.OPEN),
            "proposal": sum(1 for d in self._deals if d.status == DealStatus.PROPOSAL),
            "won": sum(1 for d in self._deals if d.status == DealStatus.WON),
            "lost": sum(1 for d in self._deals if d.status == DealStatus.LOST),
        }

        pipeline_data = self.pipeline()

        return {
            "total_customers": len(self._customers),
            "customers_by_status": customers_by_status,
            "total_deals": len(self._deals),
            "deals_by_status": deals_by_status,
            "pipeline": pipeline_data,
        }
