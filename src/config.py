from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "warden"
    app_env: str = "local"
    app_port: int = 8000
    database_url: str = "sqlite:///./warden.db"
    llm_mode: str = "mock"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    history_limit: int = 5
    confidence_threshold: float = 0.7
    orchestrator_url: str = "http://mock-orchestrator:8001"
    notifier_url: str = "http://mock-notifier:8002"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
