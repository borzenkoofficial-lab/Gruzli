from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ai_provider: str = "mock"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"
    max_iterations: int = 8
    network_mode: str = "research"
    network_max_bytes: int = 2_000_000
    network_timeout: float = 15.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
