from functools import cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.common.config.prompts import PromptSettings
from src.features.auth.schemas import AccountDetails
from src.features.search.schemas import SearchQuery


class Settings(BaseSettings):
    """Main application settings module."""

    model_config = SettingsConfigDict(
        env_file=(".env.example", ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_nested_max_split=1,
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    debug: bool = False
    environment: str = "development"

    state_path: str = "playwright/.auth/state.json"
    default_timeout: int = 15000  # milliseconds
    concurrency: int = 1
    credentials: AccountDetails = Field(..., default_factory=AccountDetails)
    search_query: SearchQuery = Field(..., default_factory=SearchQuery)

    ollama_model: str = "gemma3"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_base_url: str = "http://localhost:11434"

    postgres_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/rag"
    default_resume_path: str | None = None

    prompts: PromptSettings = Field(..., default_factory=PromptSettings)

    # Cover letter
    default_cover_letter: str | None = None
    generate_cover_letter: bool = False
    apply_with_cover_letter: bool = True

    # Relocation
    apply_with_relocation: bool = True

    # Questions
    default_answers: dict[str, str] = {}
    generate_questions: bool = True
    apply_with_questions: bool = True


@cache
def get_app_settings() -> Settings:
    return Settings()
