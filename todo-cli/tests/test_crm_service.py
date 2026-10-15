"""Testes automatizados para o CrmService.

Cobre: criação/listagem de clientes e deals, transições de status,
bloqueio de delete, pipeline, persistência.
"""

import os
import tempfile
from pathlib import Path

import pytest

from todo.crm.models import CustomerStatus, DealStatus
from todo.crm.service import (
    CrmService,
    CrmValidationError,
    CustomerNotFoundError,
    DealNotFoundError,
)
from todo.crm.storage import CrmStorage


@pytest.fixture
def temp_storage():
    """Fixture que cria um CrmStorage em arquivo temporário."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    storage = CrmStorage(file_path=Path(tmp_path))
    yield storage
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def service(temp_storage):
    """Fixture que cria um CrmService com storage temporário."""
    return CrmService(storage=temp_storage)


class TestAddCustomer:
    """Testes de adição de clientes."""

    def test_add_basic(self, service):
        customer = service.add_customer("Acme Corp")
        assert customer.name == "Acme Corp"
        assert customer.email == ""
        assert customer.status == CustomerStatus.LEAD
        assert len(customer.id) == 8

    def test_add_with_all_fields(self, service):
        customer = service.add_customer(
            "Acme Corp", email="a@a.com", phone="1199", company="Acme LTDA", notes="Cliente bom"
        )
        assert customer.email == "a@a.com"
        assert customer.phone == "1199"
        assert customer.company == "Acme LTDA"
        assert customer.notes == "Cliente bom"

    def test_add_strips_whitespace(self, service):
        customer = service.add_customer("  Acme Corp  ", email="  a@a.com  ")
        assert customer.name == "Acme Corp"
        assert customer.email == "a@a.com"

    def test_add_empty_name_raises(self, service):
        with pytest.raises(CrmValidationError, match="obrigatório"):
            service.add_customer("")
        with pytest.raises(CrmValidationError, match="obrigatório"):
            service.add_customer("   ")

    def test_add_name_too_long_raises(self, service):
        with pytest.raises(CrmValidationError, match="200"):
            service.add_customer("x" * 201)

    def test_add_invalid_email_raises(self, service):
        with pytest.raises(CrmValidationError, match="Email"):
            service.add_customer("Acme", email="invalido")

    def test_add_notes_too_long_raises(self, service):
        with pytest.raises(CrmValidationError, match="1000"):
            service.add_customer("Acme", notes="x" * 1001)

    def test_add_with_status(self, service):
        customer = service.add_customer("Acme", status=CustomerStatus.ACTIVE)
        assert customer.status == CustomerStatus.ACTIVE


class TestListCustomers:
    """Testes de listagem de clientes."""

    def test_list_empty(self, service):
        assert service.list_customers() == []

    def test_list_all(self, service):
        service.add_customer("Cliente 1")
        service.add_customer("Cliente 2")
        customers = service.list_customers()
        assert len(customers) == 2
        # Mais recentes primeiro
        assert customers[0].name == "Cliente 2"

    def test_list_filter_by_status(self, service):
        c1 = service.add_customer("Lead", status=CustomerStatus.LEAD)
        c2 = service.add_customer("Ativo", status=CustomerStatus.ACTIVE)

        leads = service.list_customers(status=CustomerStatus.LEAD)
        actives = service.list_customers(status=CustomerStatus.ACTIVE)
        assert len(leads) == 1
        assert leads[0].id == c1.id
        assert len(actives) == 1
        assert actives[0].id == c2.id

    def test_list_search_name(self, service):
        service.add_customer("Acme Corp")
        service.add_customer("Outra Empresa")
        service.add_customer("ACME Ltda")

        results = service.list_customers(search="acme")
        assert len(results) == 2

    def test_list_search_email(self, service):
        service.add_customer("Cliente 1", email="contato@acme.com")
        service.add_customer("Cliente 2", email="info@outra.com")

        results = service.list_customers(search="acme")
        assert len(results) == 1
        assert results[0].name == "Cliente 1"

    def test_list_search_company(self, service):
        service.add_customer("Fulano", company="ACME LTDA")
        service.add_customer("Beltrano", company="Outra SA")

        results = service.list_customers(search="acme")
        assert len(results) == 1


class TestGetCustomer:
    """Testes de busca por ID."""

    def test_get_by_full_id(self, service):
        customer = service.add_customer("Acme")
        found = service.get_customer(customer.id)
        assert found.id == customer.id

    def test_get_by_prefix(self, service):
        customer = service.add_customer("Acme")
        found = service.get_customer(customer.id[:4])
        assert found.id == customer.id

    def test_prefix_too_short_raises(self, service):
        customer = service.add_customer("Acme")
        with pytest.raises(CrmValidationError, match="3 caracteres"):
            service.get_customer(customer.id[:2])

    def test_not_found_raises(self, service):
        with pytest.raises(CustomerNotFoundError):
            service.get_customer("naoexiste")


class TestUpdateCustomer:
    """Testes de atualização de clientes."""

    def test_update_name(self, service):
        customer = service.add_customer("Acme")
        updated = service.update_customer(customer.id, name="Acme Corp")
        assert updated.name == "Acme Corp"

    def test_update_email(self, service):
        customer = service.add_customer("Acme")
        updated = service.update_customer(customer.id, email="novo@acme.com")
        assert updated.email == "novo@acme.com"

    def test_update_partial(self, service):
        customer = service.add_customer("Acme", email="antigo@acme.com")
        updated = service.update_customer(customer.id, phone="1199")
        assert updated.name == "Acme"  # não alterado
        assert updated.email == "antigo@acme.com"  # não alterado
        assert updated.phone == "1199"  # alterado

    def test_update_empty_name_raises(self, service):
        customer = service.add_customer("Acme")
        with pytest.raises(CrmValidationError, match="vazio"):
            service.update_customer(customer.id, name="   ")

    def test_update_invalid_email_raises(self, service):
        customer = service.add_customer("Acme")
        with pytest.raises(CrmValidationError, match="Email"):
            service.update_customer(customer.id, email="invalido")


class TestCustomerStatus:
    """Testes de mudança de status do cliente."""

    def test_set_status(self, service):
        customer = service.add_customer("Acme")
        updated = service.set_customer_status(customer.id, CustomerStatus.ACTIVE)
        assert updated.status == CustomerStatus.ACTIVE

    def test_set_status_lead_to_inactive(self, service):
        customer = service.add_customer("Acme")
        updated = service.set_customer_status(customer.id, CustomerStatus.INACTIVE)
        assert updated.status == CustomerStatus.INACTIVE


class TestDeleteCustomer:
    """Testes de deleção de clientes."""

    def test_delete_without_deals(self, service):
        customer = service.add_customer("Acme")
        service.delete_customer(customer.id)
        assert service.list_customers() == []

    def test_delete_with_deals_blocked(self, service):
        customer = service.add_customer("Acme")
        service.add_deal("Proposta", customer_id=customer.id, value=100.0)

        with pytest.raises(CrmValidationError, match="possui deals"):
            service.delete_customer(customer.id)

    def test_delete_after_removing_deals(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        service.delete_deal(deal.id)
        service.delete_customer(customer.id)  # não deve levantar erro
        assert service.list_customers() == []

    def test_delete_nonexistent_raises(self, service):
        with pytest.raises(CustomerNotFoundError):
            service.delete_customer("inexistente")


class TestAddDeal:
    """Testes de adição de deals."""

    def test_add_basic(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta site", customer_id=customer.id, value=5000.0)
        assert deal.title == "Proposta site"
        assert deal.customer_id == customer.id
        assert deal.value == 5000.0
        assert deal.status == DealStatus.OPEN
        assert deal.currency == "BRL"
        assert deal.closed_at is None

    def test_add_with_invalid_customer_raises(self, service):
        with pytest.raises(CustomerNotFoundError):
            service.add_deal("Proposta", customer_id="inexistente", value=100.0)

    def test_add_empty_title_raises(self, service):
        customer = service.add_customer("Acme")
        with pytest.raises(CrmValidationError, match="Título"):
            service.add_deal("", customer_id=customer.id)

    def test_add_negative_value_raises(self, service):
        customer = service.add_customer("Acme")
        with pytest.raises(CrmValidationError, match="negativo"):
            service.add_deal("Proposta", customer_id=customer.id, value=-100.0)

    def test_add_zero_value_ok(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=0.0)
        assert deal.value == 0.0

    def test_add_custom_currency(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0, currency="USD")
        assert deal.currency == "USD"


class TestListDeals:
    """Testes de listagem de deals."""

    def test_list_empty(self, service):
        assert service.list_deals() == []

    def test_list_all(self, service):
        customer = service.add_customer("Acme")
        service.add_deal("Deal 1", customer_id=customer.id, value=100.0)
        service.add_deal("Deal 2", customer_id=customer.id, value=200.0)
        assert len(service.list_deals()) == 2

    def test_list_filter_by_status(self, service):
        customer = service.add_customer("Acme")
        d1 = service.add_deal("Open", customer_id=customer.id, value=100.0)
        d2 = service.add_deal("Won", customer_id=customer.id, value=200.0)
        service.update_deal_status(d2.id, DealStatus.WON)

        opens = service.list_deals(status=DealStatus.OPEN)
        won = service.list_deals(status=DealStatus.WON)
        assert len(opens) == 1
        assert opens[0].id == d1.id
        assert len(won) == 1
        assert won[0].id == d2.id

    def test_list_filter_by_customer(self, service):
        c1 = service.add_customer("Cliente 1")
        c2 = service.add_customer("Cliente 2")
        d1 = service.add_deal("Deal 1", customer_id=c1.id, value=100.0)
        service.add_deal("Deal 2", customer_id=c2.id, value=200.0)

        deals_c1 = service.list_deals(customer_id=c1.id)
        assert len(deals_c1) == 1
        assert deals_c1[0].id == d1.id

    def test_list_search(self, service):
        customer = service.add_customer("Acme")
        service.add_deal("Proposta site", customer_id=customer.id, value=100.0)
        service.add_deal("Outro deal", customer_id=customer.id, value=200.0)

        results = service.list_deals(search="proposta")
        assert len(results) == 1


class TestDealStatusTransitions:
    """Testes de transições de status de deals."""

    def test_open_to_proposal(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        updated = service.update_deal_status(deal.id, DealStatus.PROPOSAL)
        assert updated.status == DealStatus.PROPOSAL
        assert updated.closed_at is None  # proposal não é estado final

    def test_open_to_won(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        updated = service.update_deal_status(deal.id, DealStatus.WON)
        assert updated.status == DealStatus.WON
        assert updated.closed_at is not None

    def test_open_to_lost(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        updated = service.update_deal_status(deal.id, DealStatus.LOST)
        assert updated.status == DealStatus.LOST
        assert updated.closed_at is not None

    def test_won_cannot_change_status(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        service.update_deal_status(deal.id, DealStatus.WON)

        with pytest.raises(CrmValidationError, match="won"):
            service.update_deal_status(deal.id, DealStatus.OPEN)

    def test_lost_cannot_change_status(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        service.update_deal_status(deal.id, DealStatus.LOST)

        with pytest.raises(CrmValidationError, match="lost"):
            service.update_deal_status(deal.id, DealStatus.PROPOSAL)

    def test_reopen_won(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        service.update_deal_status(deal.id, DealStatus.WON)

        reopened = service.reopen_deal(deal.id)
        assert reopened.status == DealStatus.OPEN
        assert reopened.closed_at is None

    def test_reopen_lost(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        service.update_deal_status(deal.id, DealStatus.LOST)

        reopened = service.reopen_deal(deal.id)
        assert reopened.status == DealStatus.OPEN

    def test_reopen_open_deal_raises(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)

        with pytest.raises(CrmValidationError, match="não está fechado"):
            service.reopen_deal(deal.id)


class TestUpdateDeal:
    """Testes de atualização de deals."""

    def test_update_title(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        updated = service.update_deal(deal.id, title="Nova Proposta")
        assert updated.title == "Nova Proposta"

    def test_update_value(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        updated = service.update_deal(deal.id, value=200.0)
        assert updated.value == 200.0

    def test_update_closed_deal_raises(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        service.update_deal_status(deal.id, DealStatus.WON)

        with pytest.raises(CrmValidationError, match="fechado"):
            service.update_deal(deal.id, value=200.0)

    def test_update_negative_value_raises(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        with pytest.raises(CrmValidationError, match="negativo"):
            service.update_deal(deal.id, value=-100.0)


class TestDeleteDeal:
    """Testes de deleção de deals."""

    def test_delete_deal(self, service):
        customer = service.add_customer("Acme")
        deal = service.add_deal("Proposta", customer_id=customer.id, value=100.0)
        service.delete_deal(deal.id)
        assert service.list_deals() == []

    def test_delete_nonexistent_raises(self, service):
        with pytest.raises(DealNotFoundError):
            service.delete_deal("inexistente")


class TestPipeline:
    """Testes do funil de vendas."""

    def test_pipeline_empty(self, service):
        p = service.pipeline()
        assert p["total_value"] == 0.0
        assert p["won_value"] == 0.0
        assert p["open_value"] == 0.0
        assert len(p["by_status"]) == 4

    def test_pipeline_with_deals(self, service):
        customer = service.add_customer("Acme")
        service.add_deal("Open", customer_id=customer.id, value=100.0)
        d2 = service.add_deal("Proposal", customer_id=customer.id, value=200.0)
        d3 = service.add_deal("Won", customer_id=customer.id, value=300.0)
        d4 = service.add_deal("Lost", customer_id=customer.id, value=400.0)

        service.update_deal_status(d2.id, DealStatus.PROPOSAL)
        service.update_deal_status(d3.id, DealStatus.WON)
        service.update_deal_status(d4.id, DealStatus.LOST)

        p = service.pipeline()
        assert p["total_value"] == 1000.0
        assert p["won_value"] == 300.0
        assert p["open_value"] == 300.0  # open(100) + proposal(200)

        by_status = {item["status"]: item for item in p["by_status"]}
        assert by_status["open"]["count"] == 1
        assert by_status["open"]["total_value"] == 100.0
        assert by_status["proposal"]["count"] == 1
        assert by_status["proposal"]["total_value"] == 200.0
        assert by_status["won"]["count"] == 1
        assert by_status["won"]["total_value"] == 300.0
        assert by_status["lost"]["count"] == 1
        assert by_status["lost"]["total_value"] == 400.0


class TestStats:
    """Testes de estatísticas."""

    def test_stats_empty(self, service):
        stats = service.stats()
        assert stats["total_customers"] == 0
        assert stats["total_deals"] == 0
        assert stats["customers_by_status"] == {"lead": 0, "active": 0, "inactive": 0}
        assert stats["deals_by_status"] == {"open": 0, "proposal": 0, "won": 0, "lost": 0}

    def test_stats_mixed(self, service):
        service.add_customer("Lead 1", status=CustomerStatus.LEAD)
        service.add_customer("Ativo 1", status=CustomerStatus.ACTIVE)
        c3 = service.add_customer("Inativo 1", status=CustomerStatus.INACTIVE)

        service.add_deal("D1", customer_id=c3.id, value=100.0)
        service.add_deal("D2", customer_id=c3.id, value=200.0)

        stats = service.stats()
        assert stats["total_customers"] == 3
        assert stats["customers_by_status"]["lead"] == 1
        assert stats["customers_by_status"]["active"] == 1
        assert stats["customers_by_status"]["inactive"] == 1
        assert stats["total_deals"] == 2
        assert stats["deals_by_status"]["open"] == 2


class TestPersistence:
    """Testes de persistência (recarregar do disco)."""

    def test_data_persists_across_services(self, temp_storage):
        s1 = CrmService(storage=temp_storage)
        c1 = s1.add_customer("Acme Persistida")
        s1.add_deal("Deal Persistido", customer_id=c1.id, value=500.0)

        s2 = CrmService(storage=temp_storage)
        customers = s2.list_customers()
        deals = s2.list_deals()
        assert len(customers) == 1
        assert customers[0].name == "Acme Persistida"
        assert len(deals) == 1
        assert deals[0].title == "Deal Persistido"
        assert deals[0].value == 500.0
