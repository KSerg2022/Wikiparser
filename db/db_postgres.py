"""Module initialization database and adding data to db."""
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from db.data import tables
from settings import database_name


def init_db():
    """
    First connection to create database.
    :return: If connected - connection, if not connected - exit from program.
    """
    connection = None
    try:
        connection = psycopg2.connect(host='127.0.0.1', user='postgres', password='1qa2ws3ed', port='5432')
    except Exception as error:
        print(error)
        exit(0)

    if connection is not None:
        return connection
    else:
        print('Connection not established to Postgres')
        exit()


def create_db(db_name: str) -> bool:
    """
    Create database with given name.
    param db_name: name of database
    :return: if database was created - True, if not - False.
    """
    connection = init_db()
    if connection:
        if not check_db_exist(connection, db_name):
            try:
                connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                cursor = connection.cursor()
                sql_create_database = f"CREATE DATABASE {db_name}"
                cursor.execute(sql_create_database)
                cursor.close()
            except (Exception, Error) as error:
                print(f'PostgresSQL: {error}')
                connection.rollback()

            connection.close()
            return True

        connection.close()
        return False


def check_db_exist(connection, db_name: str) -> bool:
    """
    Check if is there database with given name.
    :param connection: connection with database
    :param db_name: name of database
    :return: if database with given name exist - True, if not - False.
    """
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    check_query = f"SELECT datname FROM pg_database;"
    cursor.execute(check_query)
    db_names = cursor.fetchall()

    cursor.close()
    db_names = [list(db_name)[0] for db_name in db_names]
    if db_name in db_names:
        return True
    return False


def connect_to_db():
    """
    Connecting to database for do operations.
    :return: If connected - connection, if not connected - exit from program.
    """
    connection = None
    try:
        connection = psycopg2.connect(host='127.0.0.1', user='postgres', password='1qa2ws3ed', port='5432',
                                      database='wiki')
    except Exception as error:
        print(error)
        exit(0)

    if connection is not None:
        return connection
    else:
        print('Connection not established to Postgres')
        exit()


def create_table(tables_to_add):
    """
    Create tables in database.
    param tables: tables to be created in the database
    :return: If tables created - True, if not created - error.
    """
    connection = connect_to_db()
    if connection:
        for table in tables_to_add:
            try:
                cursor = connection.cursor()
                create_table_query = table
                cursor.execute(create_table_query)
                connection.commit()
                cursor.close()
            except (Exception, Error) as error:
                print(f'Table {table[:25]} ?? PostgresSQ {error}')
                connection.rollback()

        connection.close()
        return True


def insert_data_in_table_link(links: list[tuple] | tuple) -> bool:
    """
    Adding data in database in the table 'links'.
    :param links: links and title articles
    :return: if data added in database - True, if not - error.
    """
    if not isinstance(links, list):
        links = [links]
    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()
        for link in links:
            try:
                insert_query = f"INSERT INTO links(link, title_article) VALUES {link};"
                cursor.execute(insert_query)
                connection.commit()
            except (Exception, Error) as error:
                # print(f'When adding data {link} in PostgresSQ {error}')
                connection.rollback()
                update_query = f"UPDATE links SET link = '{list(link)[0]}' WHERE title_article = '{list(link)[1]}'" \
                               f"AND NOT EXISTS (SELECT link FROM links WHERE link = '{list(link)[0]}')"
                cursor.execute(update_query)
                connection.commit()

        cursor.close()
    connection.close()
    return True


def insert_data_in_table_link_to_link(id_links: list[tuple] | tuple):
    """
    Adding data in database in the table 'link_to_link'.
    :param id_links: pairs of id_links
    :return: if data added in database - True, if not - error.
    """
    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()
        for link in id_links:
            try:
                insert_query = f'INSERT INTO link_to_link(link_left, link_right) VALUES {link}'
                cursor.execute(insert_query)
                connection.commit()
            except (Exception, Error) as error:
                # print(f'When adding data {link} in PostgresSQL {error}')
                connection.rollback()

        cursor.close()
    connection.close()
    return True


def main():
    """Controller for initialization database and create tables."""
    create_db(database_name)
    create_table(tables)
