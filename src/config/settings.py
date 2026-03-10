from functools import cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.auth.schemas import AccountDetails
from src.search.schemas import SearchQuery


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
    concurrency: int = 4
    credentials: AccountDetails = Field(...)
    search_query: SearchQuery = Field(...)


@cache
def get_app_settings() -> Settings:
    return Settings()
