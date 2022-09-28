import abc
import logging
import random
import secrets
from collections import OrderedDict
from datetime import date, datetime
from functools import wraps
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
        def create_dummy_field_function(
            cls, database: "Database", column: Column
        ) -> Callable[[], Any]:
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

            # Assume that foreign keys are already populated and have all foreign keys less than
            # the max key in the associated table.
            if column.foreign_keys:
                match matchable:
                    case "INTEGER":
                        return lambda: random.randint(
                            max(database.scalars(select(column.foreign_keys)))
                        )
                    case _:
                        logging.fatal(f"Undefined dummy primary key field {column}.")
                        raise Exception(f"Undefined dummy primary key field {column}.")

            match matchable:
                case "DATETIME" | "DATE":
                    return lambda: datetime.fromtimestamp(
                        2 * datetime.timestamp(datetime.now())
                    )
                case "INTEGER":
                    return lambda: random.randint(0, 2**12)
                case ["VARCHAR", length_as_str]:
                    return lambda: secrets.token_urlsafe(int(length_as_str) // 2)
                case _:
                    logging.fatal(f"Undefined dummy field {column}.")
                    raise Exception(f"Undefined dummy field {column}.")

        @classmethod
        def create_dummy_fields(
            cls, database: "Database"
        ) -> Dict[str, Callable[[], Any]]:

            raw_fields = inspect(cls).attrs

            return {
                column_name: cls.create_dummy_field_function(
                    database, column.columns[0]
                )  # cls.__dummy_methods__[]
                for column_name, column in raw_fields.items()
            }

        @classmethod
        def with_fields(
            cls, database: "Database", overrider: Dict[str, Callable[[], Any]]
        ) -> Callable[[Callable], Callable]:
            """Decorate a ``create_dummies`` method by prodiving it with a function to generate
            each of the various fields.
            """

            def wrapper_wrapper(
                func: Callable[[Dict], List[Self]]
            ) -> Callable[[], List[Self]]:

                fields = cls.create_dummy_fields(database)
                fields.update(overrider)

                @wraps(func)
                def wrapper(*args, **kwargs):

                    return func(fields, *args, **kwargs)

                return wrapper

            return wrapper_wrapper

        @classmethod
        def invoke_fields(cls, fields: Dict[str, Callable[[], Any]]) -> Dict[str, Any]:

            return {
                field_name: create_field_value()
                for field_name, create_field_value in fields.items()
            }

        @classmethod
        def create_create_dummies(
            cls, database: "Database", overriders: Dict[str, Callable[[], Any]] = {}
        ) -> Callable[[], Tuple[Self]]:
            @cls.with_fields(database, overriders)
            def create_dummies(fields: Dict[str, Callable[[], Any]], length: int):
                return tuple(cls(**cls.invoke_fields(fields)) for _ in range(length))

            return create_dummies

    def __init__(self, configuration: Optional[ApiConfiguration] = None):

        self.configuration: ApiConfiguration = (
            configuration if configuration is not None else ApiConfiguration()
        )
        self.engine: Engine = self.create_engine()
        self.sessionmaker: sessionmaker = sessionmaker(self.engine)

    def create_engine(self) -> Engine:

        return create_engine(
            URL.create(
                self.configuration.mysql.drivername,
                **self.configuration.mysql.url.dict(),
            ),
            echo=self.configuration.mysql.echo,
        )

    def exec_(
        self, stmt, callback: Optional[Callable[[Result], Any]] = None
    ) -> Union[ChunkedIteratorResult, Result]:

        with self.sessionmaker() as session:

            results = session.execute(stmt)
            return results if callback is None else callback(results)

    def scalars(self, stmt) -> Tuple:

        return self.exec_(stmt, callback=lambda results: tuple(results.scalars()))

    def serial(
        self, stmt, serializer: Optional[Callable[[Any], Dict]] = None
    ) -> Tuple[Dict]:

        return self.exec_(
            stmt,
            callback=lambda results: tuple(
                serializer(item) for item in results.scalars()
            ),
        )

    def create_tables(self) -> None:
        """Instantiate orm registry tables."""

        with self.engine.connect() as connection:
            logging.info(
                f"Creating database tables for `{self.configuration.mysql.url.host}`."
            )
            self.Base.metadata.create_all(self.engine)

    def drop_tables(self, unsafe: bool = False) -> None:
        """Destroy the database."""

        msg: str = f"Destroying database {self.configuration.mysql.url.database} on host {self.configuration.mysql.url.host}."

        if not unsafe:
            yes = input(
                f'{msg.replace("ing", "", )}? This will delete ALL tables and not just those made by the ORM. Enter `YES` to proceed.'
            )
            if yes != "YES":
                logging.info("User did not consent to dropping tables.")
                exit(1)
            else:
                logging.info("User consented to dropping tables.")
        else:
            logging.info("User consent bypassed.")

        logging.info(msg)
        self.Base.metadata.drop_all(self.engine)


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
    permissionId = Column(String(16), nullable=False, default=lambda: token_urlsafe(16))
    idUsersIssuedBy = Column(
        Integer, ForeignKey("wtsettings_users.idUsers"), primary_key=True
    )
    idUsersIssuedTo = Column(
        Integer, ForeignKey("wtsettings_users.idUsers"), primary_key=True
    )
    userIssuedToCanWrite = Column(Boolean)
    userIssuedToCanRead = Column(Boolean)
    userIssuedToIsAdmin = Column(Boolean)
    permissionCreated = Column(DateTime, default=date.today)
    permissionLastUpdated = Column(DateTime, default=date.today)


class Objects:
    """
    :attr orderedmappedclasses: Mapped classes sorted into the order in which they are constructed
        by ``Database.Base.metadata.create_all``.
    :attr mapped_tablenames_orm: Mapped classes as indexed by their tablename.
    :attr mapped_plurals_orm: Mapped classes as indexed by their plural names.
    """

    def __init__(self):
        prefix = "wtsettings_"
        self.mapped_tablenames_orm = {
            item.__tablename__: item
            for item in (
                User,
                Permission,
            )
        }
        self.orderedtablenames = tuple(
            table.name for table in Database.Base.metadata.sorted_tables
        )
        self.mapped_tablenames_orm_ordered = OrderedDict(
            {
                table_name: mapped_tablenames_orm[table_name]
                for table_name in sorted(
                    mapped_tablenames_orm.values(),
                    key=lambda x: orderedtablenames.index(x.__tablename__),
                )
            }
        )
        self.mapped_plurals_orm = {
            key.replace(prefix, ""): value
            for key, value in mapped_tablenames_orm.items()
        }

    def create_dummy_data(self, database: Database) -> None:

        logging.info("Generating dummy data...")
        with database.sessionmaker() as session:

            session.add_all(
                (
                    item
                    for mapped in cls.mapped_tablenames_orm_ordered.values()
                    for item in mapped.create_create_dummies(database)(
                        random.randint(0, 1000)
                    )
                )
            )
            session.commit()

        return


if __name__ == "__main__":

    ...
