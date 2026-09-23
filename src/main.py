from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from src.infrastructure.api_router import router
from src.domain.exceptions import DomainError, LimiteInsuficienteError, ContratoNaoEncontradoError

app = FastAPI(
    title="POD99 - Autorização de Transações",
    description="API de autorização de transações síncrona com validação de limites.",
    version="1.0.0"
)

# Configuração de CORS para permitir consumo via Front-ends distintos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers Globais (Limpa as regras do roteador)
@app.exception_handler(ContratoNaoEncontradoError)
async def contrato_nao_encontrado_handler(request: Request, exc: ContratoNaoEncontradoError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(LimiteInsuficienteError)
async def limite_insuficiente_handler(request: Request, exc: LimiteInsuficienteError):
    return JSONResponse(status_code=402, content={"detail": str(exc)})

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    # Se for erro de concorrência do DynamoDB, lançamos 409 Conflict
    if "concorrência" in str(exc).lower():
        return JSONResponse(status_code=409, content={"detail": "Conflito de estado. Tente novamente."})
    return JSONResponse(status_code=422, content={"detail": str(exc)})

# Rotas base
@app.get("/health", tags=["Health"])
def healthcheck():
    """
    Endpoint nativo para checagem de saúde da aplicação.
    Útil para Target Groups e Load Balancers na AWS.
    """
    return {"status": "ok"}

app.include_router(router)

# Adapter for AWS Lambda
handler = Mangum(app)
