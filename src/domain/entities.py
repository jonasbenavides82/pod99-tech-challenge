import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from decimal import Decimal

@dataclass
class Contrato:
    id_contrato: str
    id_conta: str
    limite_total: Decimal
    limite_disponivel: Decimal
    versao: int

    def reservar_limite(self, valor: Decimal) -> None:
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero")
        if self.limite_disponivel < valor:
            from .exceptions import LimiteInsuficienteError
            raise LimiteInsuficienteError(f"Limite insuficiente para o contrato {self.id_contrato}")
        
        self.limite_disponivel -= valor

@dataclass
class Transacao:
    id_transacao: str
    id_contrato: str
    id_conta: str
    valor: Decimal
    moeda: str
    tipo_operacao: str
    id_estabelecimento: str
    metadata: dict
    data_hora: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class EventoTransacaoAutorizada:
    event_id: str
    event_type: str
    event_version: str
    occurred_at: str
    id_autorizacao: str
    id_contrato: str
    valor: Decimal
    saldo_reservado: Decimal
    correlation_id: str
