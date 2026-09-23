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
    """
    DTO (Data Transfer Object) contendo os dados de entrada para a requisição de autorização.
    """
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
    """
    DTO (Data Transfer Object) contendo o resultado da operação de autorização.
    """
    id_autorizacao: str
    saldo_reservado: Decimal

class AutorizarTransacaoUseCase:
    """
    Caso de Uso principal responsável por orquestrar a autorização de uma transação.
    Aplica as regras de domínio, persiste o estado via portas (Repositórios)
    e propaga eventos de domínio.
    """
    def __init__(self, contrato_repo: ContratoRepository, event_publisher: EventPublisher):
        self.contrato_repo = contrato_repo
        self.event_publisher = event_publisher

    def executar(self, request: AutorizacaoRequest) -> AutorizacaoResponse:
        """
        Executa o fluxo de autorização.
        
        Fluxo:
        1. Busca o contrato no banco de dados.
        2. Tenta reservar o limite usando a regra de domínio (Domain Driven Design).
        3. Persiste a alteração no repositório.
        4. Publica um evento assíncrono para notificação de sistemas downstream.

        Args:
            request (AutorizacaoRequest): Dados da transação.

        Returns:
            AutorizacaoResponse: O UUID da autorização e o saldo que foi reservado.
            
        Raises:
            ContratoNaoEncontradoError: Se o contrato não existir na base.
            LimiteInsuficienteError: Se o saldo for inferior ao solicitado.
        """
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
