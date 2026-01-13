from injection.testing import test_constant

from src.settings import Settings


@test_constant
def _settings_test_factory() -> Settings:
    return Settings(_env_file=".env.test")  # type: ignore[reportCallIssue]
