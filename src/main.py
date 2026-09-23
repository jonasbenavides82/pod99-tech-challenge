from fastapi import FastAPI
from mangum import Mangum
from src.infrastructure.api_router import router

app = FastAPI(
    title="POD99 - Autorização de Transações",
    description="API de autorização de transações síncrona com validação de limites.",
    version="1.0.0"
)

app.include_router(router)

# Adapter for AWS Lambda
handler = Mangum(app)
