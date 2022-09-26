import abc
import logging
import secrets
from datetime import date, datetime
from functools import wraps
from secrets import token_urlsafe
from sys import exit
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.engine import URL, Engine, create_engine
from sqlalchemy.engine.result import ChunkedIteratorResult, Result
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import registry, sessionmaker
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.sql.schema import Column, ForeignKey
from typing_extensions import Self

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

    def __init__(self, configuration: Optional[ApiConfiguration] = None):

        self.configuration: ApiConfiguration = (
            configuration if configuration is not None else ApiConfiguration()
        )
        self.engine: Engine = create_engine(self.configuration)
        self.sessionmaker: sessionmaker = sessionmaker(self.engine)

    def create_tables(self) -> None:
        """Instantiate orm registry tables."""

        with self.engine.connect() as connection:
            logging.info(
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
                    logging.info("User did not consent to dropping tables.")
                    exit(1)
                else:
                    logging.info("User consented to dropping tables.")
            else:
                logging.info("User consent bypassed.")

            logging.info(msg)
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

    def serial(self, stmt, serializer: Callable[[Any], Dict]) -> Tuple[Dict]:

        return tuple(serializer(item) for item in self.exec_(stmt).scalars())


class Objects:
    class Base(
        declarative_base(
            metaclass=type(
                "DeclarativeABCMeta",
                (
                    DeclarativeMeta,
                    abc.ABCMeta,
                ),
                {},
            ),
        )
    ):
        """A tool for generating dummy data. This is helpful for tests.

        :meth with_fields: A decorator to aid in genating values for the various fields.
        :meth create_dummies: An abstract method for dummy generation.
        """

        __abstract__ = True

        @classmethod
        def create_dummy_field_function(cls, column: Column) -> Callable[[], Any]:
            def split(column: Column) -> Union[str, List[str]]:
                field = str(column).split("(")
                return (
                    field[0]
                    if len(field) == 1
                    else (
                        field[0],
                        field[1].replace(")", ""),
                    )
                )

            matchable = split(column.type)
            logging.info(f"Matching column `{column}` with deconstruction {matchable}.")

            match matchable:
                case "DATETIME" | "DATE":
                    return lambda: datetime.fromtimestamp(
                        2 * datetime.timestamp(datetime.now())
                    )
                case "INTEGER":
                    return lambda: random.randint()
                case ["VARCHAR", length]:
                    return lambda: token_urlsafe(length // 2)
                case _:
                    logging.fatal(f"Undefined dummy field {column}.")
                    raise Exception(f"Undefined dummy field {column}.")

        @classmethod
        def create_dummy_fields(cls) -> Dict[str, Callable[[], Any]]:

            raw_fields = inspect(cls).attrs

            return {
                column_name: cls.create_dummy_field_function(
                    column.columns[0]
                )  # cls.__dummy_methods__[]
                for column_name, column in raw_fields.items()
            }

        @classmethod
        def with_fields(
            cls, overrider: Dict[str, Callable[[], Any]]
        ) -> Callable[[Callable], Callable]:
            """Decorate a ``create_dummies`` method by prodiving it with a function to generate
            each of the various fields.
            """

            def wrapper_wrapper(
                func: Callable[[Dict], List[Self]]
            ) -> Callable[[], List[Self]]:

                fields = cls.create_dummy_fields()
                fields.update(overrider)

                @wraps
                def wrapper():

                    return func(fields)

                return wrapper

            return wrapper_wrapper

        @abc.abstractclassmethod
        def create_create_dummies(cls) -> List[Self]:

            ...

    class User(Base):
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

        @classmethod
        def create_create_dummies(
            cls, overriders: Dict[str, Callable[[], Any]] = {}
        ) -> Callable[[], Tuple[Self]]:
            @cls.with_fields(overriders)
            def create_dummies(fields: Dict[str, Callable[[], Any]], length: int):
                return tuple(cls(**cls.fields(fields)) for _ in range(length))

            return create_dummies

    class Permission(Base):
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
        permissionCreated = Column(DateTime, default=date.today)
        permissionLastUpdated = Column(DateTime, default=date.today)


if __name__ == "__main__":
    print(Objects.User.create_create_dummies())
