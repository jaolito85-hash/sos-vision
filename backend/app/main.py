from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .config import settings
from .realtime import hub
from .routers import webhook, chamados, equipes, abrigos, eventos, rastreamento, ws, hidrologia


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await hub.start()
    yield
    await hub.stop()
    await db.close()


app = FastAPI(title="SOS VISION · Defesa Civil RS", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(chamados.router)
app.include_router(equipes.router)
app.include_router(abrigos.router)
app.include_router(eventos.router)
app.include_router(rastreamento.router)
app.include_router(hidrologia.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    tenant = await db.default_tenant_id()
    return {"status": "ok", "tenant": str(tenant) if tenant else None}
