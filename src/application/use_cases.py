import uuid
from decimal import Decimal
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from src.domain.entities import EventoTransacaoAutorizada
from src.domain.exceptions import ContratoNaoEncontradoError
from src.application.ports import ContratoRepository, EventPublisher

@dataclass
class AutorizacaoRequest:
    id_contrato: str
    id_conta: str
    valor: Decimal
    moeda: str
    tipo_operacao: str
    id_estabelecimento: Optional[str] = None
    metadata: Optional[dict] = None
    correlation_id: str = ""

@dataclass
class AutorizacaoResponse:
    id_autorizacao: str
    saldo_reservado: Decimal

class AutorizarTransacaoUseCase:
    def __init__(self, contrato_repo: ContratoRepository, event_publisher: EventPublisher):
        self.contrato_repo = contrato_repo
        self.event_publisher = event_publisher

    def executar(self, request: AutorizacaoRequest) -> AutorizacaoResponse:
        # 1. Buscar contrato
        contrato = self.contrato_repo.buscar_por_id(request.id_contrato)
        if not contrato:
            raise ContratoNaoEncontradoError(f"Contrato {request.id_contrato} não encontrado")

        # 2. Reservar Limite (Regra de Domínio)
        contrato.reservar_limite(request.valor)
        
        id_autorizacao = str(uuid.uuid4())

        # 3. Persistir novo estado (Garantia de concorrência)
        self.contrato_repo.salvar(contrato)

        # 4. Publicar evento
        evento = EventoTransacaoAutorizada(
            event_id=str(uuid.uuid4()),
            event_type="TransacaoAutorizada",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc).isoformat(),
            id_autorizacao=id_autorizacao,
            id_contrato=contrato.id_contrato,
            valor=request.valor,
            saldo_reservado=contrato.limite_disponivel,
            correlation_id=request.correlation_id
        )
        self.event_publisher.publicar(evento)

        return AutorizacaoResponse(
            id_autorizacao=id_autorizacao,
            saldo_reservado=contrato.limite_disponivel
        )
