import os
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from src.application.use_cases import AutorizacaoRequest, AutorizarTransacaoUseCase
from src.infrastructure.dynamo_repository import DynamoDBContratoRepository
from src.infrastructure.eventbridge_publisher import EventBridgePublisher
from src.domain.exceptions import ContratoNaoEncontradoError, LimiteInsuficienteError, DomainError

router = APIRouter()

# Dependency Injection setup
contrato_repo = DynamoDBContratoRepository()
event_publisher = EventBridgePublisher()
use_case = AutorizarTransacaoUseCase(contrato_repo, event_publisher)

class AutorizacaoRequestDTO(BaseModel):
    id_conta: str
    valor: Decimal = Field(..., gt=0)
    moeda: str
    tipo_operacao: str
    id_estabelecimento: Optional[str] = None
    metadata: Optional[dict] = None

class AutorizacaoResponseDTO(BaseModel):
    id_autorizacao: str
    saldo_reservado: Decimal

@router.post("/v1/contratos/{id_contrato}/autorizacoes", response_model=AutorizacaoResponseDTO, status_code=201)
async def autorizar(
    id_contrato: str,
    payload: AutorizacaoRequestDTO,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    """
    Endpoint para autorizar transações financeiras.
    
    Aplica validação de regras de domínio e persiste as alterações no banco de dados.
    Utiliza tratamento global de exceções, respondendo com:
    - 201: Criado com sucesso
    - 402: Limite insuficiente (Payment Required)
    - 404: Contrato não encontrado
    - 409: Conflito de versão no banco de dados (Optimistic Locking)
    - 422: Regra de negócio violada
    - 500: Erro interno
    """
    # Idempotency is usually handled by AWS Lambda Powertools at the handler level.
    # In this FastAPI wrapper, the request simply passes the idempotency_key for tracing.
    req = AutorizacaoRequest(
        id_contrato=id_contrato,
        id_conta=payload.id_conta,
        valor=payload.valor,
        moeda=payload.moeda,
        tipo_operacao=payload.tipo_operacao,
        id_estabelecimento=payload.id_estabelecimento,
        metadata=payload.metadata,
        correlation_id=idempotency_key
    )

    # Execução do caso de uso.
    # As exceções de domínio lançadas aqui serão interceptadas 
    # pelos @app.exception_handler no main.py, limpando o código da rota.
    response = use_case.executar(req)
    
    return AutorizacaoResponseDTO(
        id_autorizacao=response.id_autorizacao,
        saldo_reservado=response.saldo_reservado
    )
