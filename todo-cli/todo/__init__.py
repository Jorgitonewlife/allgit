"""Todo CLI - Gerenciador de tarefas em linha de comando.

Pacote principal contendo:
- models: Tipos de dados (Task, TaskStatus)
- storage: Persistência em JSON
- service: Lógica de negócio (TodoService)
- cli: Interface de linha de comando (argparse)
- crm: Módulo CRM (Customers & Deals)
"""

__version__ = "0.2.0"

from .crm.models import Customer, CustomerStatus, Deal, DealStatus
from .crm.service import (
    CrmService,
    CrmServiceError,
    CrmValidationError,
    CustomerNotFoundError,
    DealNotFoundError,
)
from .crm.storage import CrmStorage, CrmStorageError
from .models import Task, TaskStatus
from .service import ServiceError, TaskNotFoundError, TodoService, ValidationError
from .storage import Storage, StorageError

__all__ = [
    "Task",
    "TaskStatus",
    "TodoService",
    "ServiceError",
    "TaskNotFoundError",
    "ValidationError",
    "Storage",
    "StorageError",
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
