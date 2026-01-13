from enum import StrEnum, auto

from injection import constant
from pydantic import BaseModel, Field, Secret, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Profile(StrEnum):
    # Write your profiles here.
    ...


class Scope(StrEnum):
    LIFESPAN = auto()
    REQUEST = auto()


class _DatabaseSettings(BaseModel):
    name: SecretStr
    user: SecretStr = Field(default=SecretStr("root"))
    password: SecretStr = Field(default=SecretStr("root"))
    host: SecretStr = Field(default=SecretStr("localhost"))
    port: Secret[int] = Field(default=Secret(5432))

    def get_url(self, custom_name: str | None = None) -> str:
        name = custom_name or self.name.get_secret_value()
        user = self.user.get_secret_value()
        password = self.password.get_secret_value()
        host = self.host.get_secret_value()
        port = self.port.get_secret_value()
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


@constant
class Settings(BaseSettings):
    profile: Profile | None = Field(default=None)
    allow_origins: tuple[str, ...] = Field(default=("*",))
    debug: bool = Field(default=False)
    db: _DatabaseSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )
