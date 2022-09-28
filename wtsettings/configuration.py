from os import path
from typing import Dict, Optional

from pydantic import BaseModel, BaseSettings
from pydantic.env_settings import SettingsSourceCallable
from yaml import safe_load

ENV_FILE = path.realpath(path.join(path.dirname(__file__), "..", ".env.yaml"))


def yaml_settings(settings: SettingsSourceCallable) -> Dict:

    with open(ENV_FILE, "r") as file:
        return safe_load(file)


class ApiConfiguration(BaseSettings):
    """Settings for FastApi, Uvicorn, and MySQL.

    :attr mysql: Setting for mysql.
    """

    class Config:
        env_prefix = "WTSETTINGS_"
        env_nested_delimiter = "__"

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:

            return env_settings, init_settings, yaml_settings

    class MySqlConfiguration(BaseModel):
        """Settings for the MySQL database connection.

        :attr drivername: The driver to be used by sqlalchemy.
        :attr url: The url specification for the database connection.
        :attr use_ssl: Should the connection use SSL or not.
        :attr ssl_ca: A path to a certificate authority file, for instance you might want to use this
            with a connection to an azure mysql instance where the certifacte authority file is to be
            held locally.
        """

        class MySqlUrlConfiguration(BaseModel):
            """Url specification for the database connection. Drivername is not in here since it must be
            specified as a separate argument to the url constructor.

            :attr host: The hostname for the sqlinstance, for instance an ip address.
            :attr port: The port on the host to which mysql should connect.
            :attr username: The username for the user to be used on this host.
            :attr password: The corresponding password for this username.
            """

            host: str
            port: Optional[int]
            username: str
            password: str
            database: str

        drivername: str
        url: MySqlUrlConfiguration
        use_ssl: bool = False
        echo: bool = False
        ssl_ca: Optional[str]

    mysql: MySqlConfiguration


def main():

    from json import dumps
    from shutil import get_terminal_size

    sep = get_terminal_size().columns * "="

    print(sep)
    print(dumps(ApiConfiguration().dict(), indent=2))
    print(sep)


if __name__ == "__main__":
    main()
