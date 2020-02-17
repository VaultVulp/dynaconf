import os

import pytest
from fakeredis import FakeServer, FakeStrictRedis

from dynaconf import LazySettings
from dynaconf.loaders.redis_loader import delete, load, write


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    """
    Replace StrictRedis, that we rely on internally, with an instance of a FakeStrictRedis.

    This instance automatically cleans itself after each test.
    """

    class DynaconfFakeStrictRedis(FakeStrictRedis):
        fake_server = FakeServer()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, server=self.fake_server)

    mocker.patch("dynaconf.loaders.redis_loader.StrictRedis", DynaconfFakeStrictRedis)


@pytest.mark.integration
def test_redis_not_configured():
    with pytest.raises(RuntimeError) as excinfo:
        settings = LazySettings()
        write(settings, {"OTHER_SECRET": "redis_works"})
    assert "export REDIS_ENABLED_FOR_DYNACONF=true" in str(excinfo.value)


@pytest.mark.integration
def test_write_redis_without_data():
    os.environ["REDIS_ENABLED_FOR_DYNACONF"] = "1"
    os.environ["REDIS_HOST_FOR_DYNACONF"] = "localhost"
    os.environ["REDIS_PORT_FOR_DYNACONF"] = "6379"
    settings = LazySettings()
    with pytest.raises(AttributeError) as excinfo:
        write(settings)
    assert "Data must be provided" in str(excinfo.value)


@pytest.mark.integration
def test_write_to_redis():
    os.environ["REDIS_ENABLED_FOR_DYNACONF"] = "1"
    os.environ["REDIS_HOST_FOR_DYNACONF"] = "localhost"
    os.environ["REDIS_PORT_FOR_DYNACONF"] = "6379"
    settings = LazySettings()

    write(settings, {"SECRET": "redis_works_with_docker"})
    load(settings, key="SECRET")
    assert settings.get("SECRET") == "redis_works_with_docker"


@pytest.mark.integration
def test_load_from_redis_with_key():
    os.environ["REDIS_ENABLED_FOR_DYNACONF"] = "1"
    os.environ["REDIS_HOST_FOR_DYNACONF"] = "localhost"
    os.environ["REDIS_PORT_FOR_DYNACONF"] = "6379"
    settings = LazySettings()
    write(settings, {"SECRET": "redis_works_with_docker"})
    load(settings, key="SECRET")
    assert settings.get("SECRET") == "redis_works_with_docker"


@pytest.mark.integration
def test_write_and_load_from_redis_without_key():
    os.environ["REDIS_ENABLED_FOR_DYNACONF"] = "1"
    os.environ["REDIS_HOST_FOR_DYNACONF"] = "localhost"
    os.environ["REDIS_PORT_FOR_DYNACONF"] = "6379"
    settings = LazySettings()
    write(settings, {"SECRET": "redis_works_perfectly"})
    load(settings)
    assert settings.get("SECRET") == "redis_works_perfectly"


@pytest.mark.integration
def test_delete_from_redis():
    os.environ["REDIS_ENABLED_FOR_DYNACONF"] = "1"
    os.environ["REDIS_HOST_FOR_DYNACONF"] = "localhost"
    os.environ["REDIS_PORT_FOR_DYNACONF"] = "6379"
    settings = LazySettings()
    write(settings, {"OTHER_SECRET": "redis_works"})
    load(settings)
    assert settings.get("OTHER_SECRET") == "redis_works"
    delete(settings, key="OTHER_SECRET")
    assert load(settings, key="OTHER_SECRET") is None


@pytest.mark.integration
def test_delete_all_from_redis():
    settings = LazySettings()
    delete(settings)
    assert load(settings, key="OTHER_SECRET") is None
