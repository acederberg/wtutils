from typing import Optional

from pydantic import BaseModel, BaseSettings


class ApiConfiguration(BaseSettings):
    """Settings for FastApi, Uvicorn, and MySQL.

    :attr mysql: Setting for mysql.
    """

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

        drivername: str
        url: MySqlUrlConfiguration
        use_ssl: bool = False
        ssl_ca: Optional[str]

    mysql: MySqlConfiguration
