import pytest

from aggrey.config import ConfigError, load_settings


@pytest.mark.usefixtures("clean_env")
def test_missing_database_url_fails_with_variable_name() -> None:
    with pytest.raises(ConfigError, match="DATABASE_URL: Field required"):
        load_settings()


@pytest.mark.usefixtures("clean_env")
def test_invalid_value_is_named_but_not_echoed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/d")
    monkeypatch.setenv("DB_CONNECT_TIMEOUT_S", "hunter2-not-a-number")

    with pytest.raises(ConfigError) as excinfo:
        load_settings()

    message = str(excinfo.value)
    assert "DB_CONNECT_TIMEOUT_S" in message
    assert "hunter2" not in message


@pytest.mark.usefixtures("clean_env")
def test_pool_min_above_max_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/d")
    monkeypatch.setenv("DB_POOL_MIN_SIZE", "6")
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "2")

    with pytest.raises(ConfigError, match="DB_POOL_MIN_SIZE must not exceed DB_POOL_MAX_SIZE"):
        load_settings()


@pytest.mark.usefixtures("clean_env")
def test_valid_settings_hide_the_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:secret-pw@h/d")

    settings = load_settings()

    assert settings.database_url.get_secret_value() == "postgresql://u:secret-pw@h/d"
    assert "secret-pw" not in repr(settings)
    assert settings.db_statement_timeout_ms == 5000
