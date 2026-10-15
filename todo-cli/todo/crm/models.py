"""Modelos de dados do módulo CRM (Customers & Deals).

Define as estruturas centrais: Customer (cliente), Deal (negócio),
CustomerStatus e DealStatus (estados controlados).
Segue as mesmas convenções de models.py: dataclasses + Enum.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CustomerStatus(str, Enum):
    """Estados possíveis de um cliente.

    lead -> active -> inactive (transições lógicas, validadas no service).
    """
    LEAD = "lead"          # Potencial cliente (não qualificado)
    ACTIVE = "active"      # Cliente ativo
    INACTIVE = "inactive"  # Cliente inativo


class DealStatus(str, Enum):
    """Estados possíveis de um negócio (deal).

    open -> proposal -> won/lost. won/lost são estados finais.
    """
    OPEN = "open"          # Em negociação inicial
    PROPOSAL = "proposal"  # Proposta enviada
    WON = "won"            # Ganho (closed_at preenchido)
    LOST = "lost"          # Perdido (closed_at preenchido)


@dataclass
class Customer:
    """Representa um cliente no CRM.

    Campos obrigatórios: name. Opcional: email, phone, company, notes.
    """
    name: str                                  # Nome obrigatório (1-200 chars)
    email: str = ""                            # Email opcional (validação básica)
    phone: str = ""                            # Telefone opcional
    company: str = ""                          # Empresa opcional
    notes: str = ""                            # Notas livres
    status: CustomerStatus = CustomerStatus.LEAD  # Estado inicial: lead
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])  # ID curto
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def set_status(self, status: CustomerStatus) -> None:
        """Atualiza o status do cliente."""
        self.status = status
        self.updated_at = datetime.now()

    def update_name(self, new_name: str) -> None:
        """Atualiza o nome do cliente."""
        if not new_name or not new_name.strip():
            raise ValueError("Nome não pode ser vazio")
        self.name = new_name.strip()
        self.updated_at = datetime.now()

    def update_email(self, new_email: str) -> None:
        """Atualiza o email do cliente."""
        self.email = new_email.strip()
        self.updated_at = datetime.now()

    def update_phone(self, new_phone: str) -> None:
        """Atualiza o telefone do cliente."""
        self.phone = new_phone.strip()
        self.updated_at = datetime.now()

    def update_company(self, new_company: str) -> None:
        """Atualiza a empresa do cliente."""
        self.company = new_company.strip()
        self.updated_at = datetime.now()

    def update_notes(self, new_notes: str) -> None:
        """Atualiza as notas do cliente."""
        self.notes = new_notes.strip()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Converte Customer para dicionário serializável (JSON)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "notes": self.notes,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Customer":
        """Reconstrói Customer a partir de dicionário (vindo do JSON)."""
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            id=data["id"],
            name=data["name"],
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            company=data.get("company", ""),
            notes=data.get("notes", ""),
            status=CustomerStatus(data.get("status", "lead")),
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class Deal:
    """Representa um negócio (oportunidade de venda) no CRM.

    Campos obrigatórios: title, customer_id, value.
    """
    title: str                                 # Título obrigatório (1-200 chars)
    customer_id: str                           # ID do cliente vinculado
    value: float = 0.0                         # Valor monetário (>= 0)
    currency: str = "BRL"                      # Moeda (padrão BRL)
    status: DealStatus = DealStatus.OPEN       # Estado inicial: open
    notes: str = ""                            # Notas livres
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    closed_at: datetime | None = None          # Preenchido quando won/lost

    def mark_won(self) -> None:
        """Marca o deal como ganho (won) e registra o horário."""
        self.status = DealStatus.WON
        self.updated_at = datetime.now()
        self.closed_at = datetime.now()

    def mark_lost(self) -> None:
        """Marca o deal como perdido (lost) e registra o horário."""
        self.status = DealStatus.LOST
        self.updated_at = datetime.now()
        self.closed_at = datetime.now()

    def reopen(self) -> None:
        """Reabre um deal concluído (won/lost) para open."""
        self.status = DealStatus.OPEN
        self.updated_at = datetime.now()
        self.closed_at = None

    def set_status(self, status: DealStatus) -> None:
        """Define o status diretamente (validação de transição no service)."""
        self.status = status
        self.updated_at = datetime.now()
        if status in (DealStatus.WON, DealStatus.LOST):
            self.closed_at = datetime.now()
        else:
            self.closed_at = None

    def update_title(self, new_title: str) -> None:
        """Atualiza o título do deal."""
        if not new_title or not new_title.strip():
            raise ValueError("Título não pode ser vazio")
        self.title = new_title.strip()
        self.updated_at = datetime.now()

    def update_value(self, new_value: float) -> None:
        """Atualiza o valor do deal (deve ser >= 0)."""
        if new_value < 0:
            raise ValueError("Valor não pode ser negativo")
        self.value = new_value
        self.updated_at = datetime.now()

    def update_currency(self, new_currency: str) -> None:
        """Atualiza a moeda do deal."""
        self.currency = new_currency.strip().upper()
        self.updated_at = datetime.now()

    def update_notes(self, new_notes: str) -> None:
        """Atualiza as notas do deal."""
        self.notes = new_notes.strip()
        self.updated_at = datetime.now()

    def is_closed(self) -> bool:
        """Verifica se o deal está fechado (won ou lost)."""
        return self.status in (DealStatus.WON, DealStatus.LOST)

    def to_dict(self) -> dict:
        """Converte Deal para dicionário serializável (JSON)."""
        return {
            "id": self.id,
            "title": self.title,
            "customer_id": self.customer_id,
            "value": self.value,
            "currency": self.currency,
            "status": self.status.value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Deal":
        """Reconstrói Deal a partir de dicionário (vindo do JSON)."""
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        closed_at = (
            datetime.fromisoformat(data["closed_at"])
            if data.get("closed_at")
            else None
        )

        return cls(
            id=data["id"],
            title=data["title"],
            customer_id=data["customer_id"],
            value=float(data.get("value", 0.0)),
            currency=data.get("currency", "BRL"),
            status=DealStatus(data.get("status", "open")),
            notes=data.get("notes", ""),
            created_at=created_at,
            updated_at=updated_at,
            closed_at=closed_at,
        )
