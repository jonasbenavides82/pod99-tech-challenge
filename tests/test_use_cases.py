import pytest
from decimal import Decimal
from typing import Optional

from src.domain.entities import Contrato, EventoTransacaoAutorizada
from src.domain.exceptions import ContratoNaoEncontradoError, LimiteInsuficienteError
from src.application.ports import ContratoRepository, EventPublisher
from src.application.use_cases import AutorizarTransacaoUseCase, AutorizacaoRequest

class MockContratoRepository(ContratoRepository):
    def __init__(self):
        self.contratos = {}
        self.salvou = False

    def buscar_por_id(self, id_contrato: str) -> Optional[Contrato]:
        return self.contratos.get(id_contrato)

    def salvar(self, contrato: Contrato) -> None:
        self.salvou = True
        self.contratos[contrato.id_contrato] = contrato

class MockEventPublisher(EventPublisher):
    def __init__(self):
        self.eventos = []

    def publicar(self, evento: EventoTransacaoAutorizada) -> None:
        self.eventos.append(evento)

@pytest.fixture
def repo():
    return MockContratoRepository()

@pytest.fixture
def publisher():
    return MockEventPublisher()

@pytest.fixture
def use_case(repo, publisher):
    return AutorizarTransacaoUseCase(repo, publisher)

def test_autorizar_transacao_sucesso(use_case, repo, publisher):
    repo.contratos["123"] = Contrato(
        id_contrato="123",
        id_conta="abc",
        limite_total=Decimal("1000.00"),
        limite_disponivel=Decimal("500.00"),
        versao=1
    )
    
    req = AutorizacaoRequest(
        id_contrato="123",
        id_conta="abc",
        valor=Decimal("100.00"),
        moeda="BRL",
        tipo_operacao="CREDITO"
    )
    
    resp = use_case.executar(req)
    
    assert resp.saldo_reservado == Decimal("400.00")
    assert repo.salvou is True
    assert len(publisher.eventos) == 1
    
    evento = publisher.eventos[0]
    assert evento.id_contrato == "123"
    assert evento.valor == Decimal("100.00")
    assert evento.saldo_reservado == Decimal("400.00")

def test_autorizar_transacao_contrato_nao_encontrado(use_case):
    req = AutorizacaoRequest(
        id_contrato="999",
        id_conta="abc",
        valor=Decimal("100.00"),
        moeda="BRL",
        tipo_operacao="CREDITO"
    )
    
    with pytest.raises(ContratoNaoEncontradoError):
        use_case.executar(req)
