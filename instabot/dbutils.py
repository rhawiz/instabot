# -*- coding: utf-8 -*-
#
# Address Learning Machine - Database helper utilities
# Contains helper functions for reading, writing and updating SQLite databases


import os

import sqlite3

from utils import print_progress

def insert_row(db_path, table_name, row):
    """Insert a list or tuple of items into a sqlite database table

    Parameters
    ----------
    db_path: string
        path to sqlite database
    table_name: string
        Name of the rable
    row: List or tuple
        List or tuple of items to insert into the table

    Returns
    -------
        True if successfully inserted into row, false if error occurred.

    """
    connection = sqlite3.connect(db_path)
    connection.text_factory = str
    cursor = connection.cursor()
    value_placeholders = ''
    values = []
    for i in row:
        values.append(str(i))
        value_placeholders = "{}?, ".format(value_placeholders)

    value_placeholders = value_placeholders[:-2]
    try:
        insert_sql = 'INSERT INTO {} VALUES ({})'.format(table_name, value_placeholders)
        cursor.execute(insert_sql, tuple(values))
        connection.commit()
        connection.close()
        return True
    except Exception, e:
        print e
        connection.close()
        return False

def create_database(db_path, table_name, columns):
    """
    Create sqlite database and tables
    Parameters
    ----------
    db_path: str
        Database path
    table_name: str
        Table name
    columns: list<str>
        Column surnames

    Returns
    -------

    """
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    columns_sql = ''
    for column in columns:
        columns_sql = "{}{} TEXT, ".format(columns_sql, column)
    columns_sql = "({})".format(columns_sql[:-2])
    create_table_sql = '''CREATE TABLE {} {}'''.format(table_name, columns_sql)

    try:
        cursor.execute(create_table_sql)
        connection.commit()
        return True
    except sqlite3.OperationalError, e:
        # If the table exists check if the columns invalid_samples with the input columns
        #   if they are the same return True. If they don't match return False.
        cursor = connection.execute('SELECT * FROM {}'.format(table_name))
        existing_columns_hash = hash(''.join([description[0] for description in cursor.description]))
        columns_hash = hash(''.join(columns))
        if columns_hash == existing_columns_hash:
            return True
        return False
    finally:
        connection.close()


def execute_query(db_path, sql_query):
    """
    Execute sql query on a sqlite database

    Parameters
    ----------
    db_path: str
        file path to sqlite database

    sql_query: str
        query to execute

    Returns
    -------
        bool/list<tuple>/none depending on the query

    """
    connection = sqlite3.connect(db_path)
    connection.text_factory = str
    cursor = connection.cursor()
    cursor.execute(sql_query)
    connection.commit()
    data = cursor.fetchall()
    connection.close()
    return data
