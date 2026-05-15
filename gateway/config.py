from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    GATEWAY_ADAPTER: str = "stub"
    BACKEND_BASE_URL: str = "http://mock-backend:8000"
    BACKEND_HEALTH_PATH: str = "/health"
    BACKEND_TIMEOUT_S: float = 30.0
    HEALTH_CHECK_INTERVAL_S: int = 15
    PORT: int = 8000
    GATEWAY_MODELS: str = "gpt-3.5-turbo,gpt-4"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    def model_list(self) -> list[str]:
        return [m.strip() for m in self.GATEWAY_MODELS.split(",") if m.strip()]


settings = Settings()
