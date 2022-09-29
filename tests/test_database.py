from typing import Tuple

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.expression import text
from wtsettings.database import Database, User

Base = Database.Base


class DatabaseHelpers:
    @staticmethod
    def get_tables(connection: Connection) -> Tuple[str, ...]:
        return tuple(connection.execute(text("SHOW TABLES;")).scalars())


class TestDatabase:
    @staticmethod
    def test_create_engine(database_):

        engine = database_.create_engine()
        assert isinstance(engine, Engine)

        # Make sure that the connection works.
        with engine.connect() as connection:
            DatabaseHelpers.get_tables(connection)

    @staticmethod
    def test_exec_(database_):

        # results = database_.exec_(select())
        ...

    @staticmethod
    def test_scalars(database_):
        ...

    @staticmethod
    def test_serial(database_):
        ...

    @staticmethod
    def test_create_tables(database_):

        with database_.engine.connect() as connection:

            # Remove any existing tables. In case of running this on a production database_ (which is stupid),
            # you should make sure that your apps sql users
            results = tuple(
                connection.execute(f"DROP TABLE {table};")
                for table in DatabaseHelpers.get_tables(connection)
            )

            results = DatabaseHelpers.get_tables(connection)
            assert len(results) == 0, "There should be no tables at this point."

            # Recreate tables. Again if this fails check you sql users permissions.
            database_.create_tables()

        # Start a new context since the SHOW TABLE results will be cached otherwise
        with database_.engine.connect() as connection:

            # Verify the number of tables create matches the number of tables specified in the connection.
            results = DatabaseHelpers.get_tables(connection)
            assert len(results) == len(database_.Base.metadata.sorted_tables)

    @staticmethod
    def test_drop_tables(database_):

        # Create tables to ensure there are any tables to drop
        database_.create_tables()
        with database_.engine.connect() as connection:

            # Verify the number of tables create matches the number of tables specified in the connection.
            results = DatabaseHelpers.get_tables(connection)
            assert len(results) == len(database_.Base.metadata.sorted_tables)

        # Drop tables, verify none are left. New context to kill cache.
        database_.drop_tables(unsafe=True)
        with database_.engine.connect() as connection:

            results = DatabaseHelpers.get_tables(connection)
            assert len(results) == 0

    @staticmethod
    def test_create_create_dummies_functionality(database):

        # Attempt to create some dummy users.
        print(database)
        with database.sessionmaker() as session:

            create_dummy_users = User.create_create_dummies(database)
            dummy_users = create_dummy_users(10)
            session.add_all(dummy_users)
            session.commit()

        # Read the users generated, make obvious assertions
        users = database.scalars(select(User))
        assert len(users) == 10
