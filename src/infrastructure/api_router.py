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

    try:
        response = use_case.executar(req)
        return AutorizacaoResponseDTO(
            id_autorizacao=response.id_autorizacao,
            saldo_reservado=response.saldo_reservado
        )
    except ContratoNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LimiteInsuficienteError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except DomainError as e:
        if "concorrência" in str(e).lower():
            raise HTTPException(status_code=409, detail="Conflito de estado. Tente novamente.")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
