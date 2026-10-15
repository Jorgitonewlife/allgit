"""Módulo CRM (Customers & Deals) do Todo CLI.

Pacote com:
- models: Customer, Deal, CustomerStatus, DealStatus
- storage: CrmStorage (persistência em JSON)
- service: CrmService (lógica de negócio)
"""

from .models import Customer, CustomerStatus, Deal, DealStatus
from .service import (
    CrmService,
    CrmServiceError,
    CrmValidationError,
    CustomerNotFoundError,
    DealNotFoundError,
)
from .storage import CrmStorage, CrmStorageError

__all__ = [
    "Customer",
    "CustomerStatus",
    "Deal",
    "DealStatus",
    "CrmService",
    "CrmServiceError",
    "CrmValidationError",
    "CustomerNotFoundError",
    "DealNotFoundError",
    "CrmStorage",
    "CrmStorageError",
]
