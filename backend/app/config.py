from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql://sos:sos@localhost:5432/sosvision"
    REDIS_URL: str = "redis://localhost:6379/0"
    PUBLIC_BASE_URL: str = "http://localhost:8000"   # URL pública do backend/API
    PUBLIC_APP_URL: str = "http://localhost:5173"    # URL pública do frontend (Sala + PWAs)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5180,http://localhost:5181"

    # Mensageria — MVP usa Evolution; pós-MVP migra p/ Cloud API oficial (Meta).
    MESSAGING_CHANNEL: str = "simulator"  # simulator | evolution | cloud
    # Evolution API (MVP)
    EVOLUTION_URL: str = ""        # ex: https://evo.seu-dominio.com
    EVOLUTION_KEY: str = ""        # apikey global/instância
    EVOLUTION_INSTANCE: str = ""   # nome da instância conectada ao número
    # WhatsApp Cloud API (pós-MVP)
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "troque-este-token"

    # IA — usa OpenAI se OPENAI_API_KEY; senão Anthropic; senão heurístico.
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    CLASSIFIER_MODEL: str = ""  # vazio = default por provedor (OpenAI: gpt-4o-mini)

    # Roteamento ("Traçar rota"). Sem chave, usa OSRM público (fallback).
    ORS_API_KEY: str = ""   # OpenRouteService — habilita avoid de vias bloqueadas (fase 2)

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
