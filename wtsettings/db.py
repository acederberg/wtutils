from datetime import date
from secrets import token_urlsafe
from sys import exit
from typing import Any, Callable, Dict, Optional, Tuple, Union

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.engine import URL, Engine, create_engine
from sqlalchemy.engine.result import ChunkedIteratorResult, Result
from sqlalchemy.orm import registry, sessionmaker
from sqlalchemy.sql.schema import Column, ForeignKey

from .configuration import ApiConfiguration


class Database:
    """Class for all of the inconvenient ``sqlalchemy`` stuff.

    :attr Registry:
    :attr Base:
    :attr engine:
    :attr sessionmaker:
    """

    Registry = registry()
    Base = Registry.generate_base()

    def __init__(self, logger, configuration: Optional[ApiConfiguration] = None):

        self.logger = logger
        self.configuration: ApiConfiguration = (
            configuration if configuration is not None else ApiConfiguration()
        )
        self.engine: Engine = create_engine(self.configuration)
        self.sessionmaker: sessionmaker = sessionmaker(self.engine)

    def create_tables(self) -> None:
        """Instantiate orm registry tables."""

        with self.engine.connect() as connection:
            self.logger.info(
                f"Creating database tables for {self.configuration.url.hostname}."
            )
            connection.create_tables(self.Base.metadata)

    def destroy_tables(self, unsafe: bool = False) -> None:
        """Destroy the database."""

        with self.engine.connect() as connection:
            msg: str = f"Destroying database {self.configuration.mysql.url.database} on host {self.configuration.mysql.url.host}."

            if not unsafe:
                yes = input(
                    f'{msg.replace("ing", "", count = 1)}? This will delete ALL tables and not just those made by the ORM. Enter `YES` to proceed.'
                )
                if yes != "YES":
                    self.logger.info("User did not consent to dropping tables.")
                    exit(1)
                else:
                    self.logger.info("User consented to dropping tables.")
            else:
                self.logger.info("User consent bypassed.")

            self.logger.info(msg)
            connection.execute(
                text(f"DROP DATABASE {self.confguration.mysql.url.database};")
            )

    def create_engine(self) -> Engine:

        return create_engine(
            URL(
                self.configuration.mysql.drivername,
                **self.configuration.mysql.url.dict(),
            ),
        )

    def exec_(self, stmt) -> Union[ChunkedIteratorResult, Result]:

        with self.sessionmaker() as session:

            results = session.execute(stmt)

        return results

    def scalars(self, stmt) -> Tuple:

        return tuple(self.exec_(stmt).scalars())

    def serial(self, stmt, serializer: Callable[Any, Dict]) -> Tuple[Dict]:

        return tuple(serializer(item) for item in self.exec_(stmt).scalars())


class Objects:
    class User(Database.Base):
        """Description of an application user.  THIS TABLE WILL NOT CONTAIN AUTHENTICATION
        INFORMATION!!! Authentication will be handled by auth0.

        :attr idUsers: Primary key.
        :attr userId: User alternative id.
        :attr userName: User handle.
        :attr userAlias: User display name.
        :attr userCreated: Datetime of user creation.
        :attr userDetails: User Bio.
        """

        __tablename__ = "wtsettings_users"

        idUsers = Column(Integer, primary_key=True)
        userId = Column(String(16), nullable=False, default=lambda: token_urlsafe(16))
        userName = Column(String(32), nullable=False)
        userAlias = Column(String(32), nullable=True)
        userCreated = Column(DateTime, default=date.today)
        userDetails = Column(String(32), nullable=True)

    class Permission(Database.Base):
        """Table to facilitate permisisons on collections.

        :attr idPermissions: Primary key.
        :attr permissionId: Permission public id.
        :attr idUsersIssuedBy: Who owns the resource.
        :attr idUsersIssuedTo: Who was granted access to the resource.
        :attr userIssuedToCanWrite: Can the user with granted permissions do RUD in CRUD.
        :attr userIssuedToCanRead: Can the user look at the resource?
        :attr userIssuedToIsAdmin: Can the user do admin stuff?
        """

        __tablename__ = "wtsettings_permissions"

        idPermissions = Column(Integer, primary_key=True)
        permissionId = Column(
            String(16), nullable=False, default=lambda: token_urlsafe(16)
        )
        idUsersIssuedBy = Column(Integer, ForeignKey("Users.idUsers"), primary_key=True)
        idUsersIssuedTo = Column(Integer, ForeignKey("Users.idUsers"), primary_key=True)
        userIssuedToCanWrite = Column(Boolean)
        userIssuedToCanRead = Column(Boolean)
        userIssuedToIsAdmin = Column(Boolean)
