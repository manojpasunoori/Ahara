from app.core.config import Settings


def test_settings_parses_comma_separated_cors_origins() -> None:
    settings = Settings(database_url="postgresql+psycopg://user:pass@localhost/db", redis_url="redis://localhost:6379/0", cors_origins="http://localhost:3000,http://localhost:3001")
    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:3001"]
