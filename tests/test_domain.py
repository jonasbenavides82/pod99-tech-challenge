import pytest
from decimal import Decimal
from src.domain.entities import Contrato
from src.domain.exceptions import LimiteInsuficienteError

def test_reservar_limite_com_sucesso():
    contrato = Contrato(
        id_contrato="123",
        id_conta="abc",
        limite_total=Decimal("1000.00"),
        limite_disponivel=Decimal("500.00"),
        versao=1
    )
    
    contrato.reservar_limite(Decimal("100.00"))
    assert contrato.limite_disponivel == Decimal("400.00")

def test_reservar_limite_insuficiente():
    contrato = Contrato(
        id_contrato="123",
        id_conta="abc",
        limite_total=Decimal("1000.00"),
        limite_disponivel=Decimal("100.00"),
        versao=1
    )
    
    with pytest.raises(LimiteInsuficienteError):
        contrato.reservar_limite(Decimal("200.00"))

def test_reservar_limite_valor_negativo():
    contrato = Contrato(
        id_contrato="123",
        id_conta="abc",
        limite_total=Decimal("1000.00"),
        limite_disponivel=Decimal("500.00"),
        versao=1
    )
    
    with pytest.raises(ValueError):
        contrato.reservar_limite(Decimal("-10.00"))
