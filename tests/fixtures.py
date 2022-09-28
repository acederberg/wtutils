import pytest
from wtsettings import ApiConfiguration, Database


@pytest.fixture
def configuration():

    return ApiConfiguration()


@pytest.fixture
def database_(configuration):

    return Database(configuration=configuration)


@pytest.fixture
def database(database_):

    database_.drop_tables(unsafe=True)
    database_.create_tables()
    yield database_
