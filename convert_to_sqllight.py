from sql_dump_parser import SqlSimpleDumpParser
from datetime import datetime
import sqlite3

database_path = 'my_database.db'
dump_path = "dump.sql"

connection = sqlite3.connect(database_path)
cursor = connection.cursor()

def custom_data_convert_function(obj_tokens, data_type):
    if data_type.first().upper() == 'DATETIME':        
         return datetime.fromisoformat(obj_tokens[0].name), True
    return obj_tokens, False

def create_table(tbdef, tb_name, cursor, connection):
    lines = []
    for col in tbdef.keys():
        dtype = tbdef[col]
        if dtype == 'char' or dtype == 'varchar' or dtype == 'longtext':
            dtype = 'TEXT'
        elif dtype == 'int' or dtype == 'tinyint':
            dtype = 'INTEGER'
        elif dtype == 'decimal' or dtype == 'float':
            dtype = 'REAL'
        elif dtype == 'datetime':
            dtype = 'timestamp'
        else: 
            dtype = 'TEXT'
        #if col == 'Id':
        #    dtype = dtype + ' PRIMARY KEY'
        lines.append(col + ' ' + dtype)
    expr = 'CREATE TABLE ' + tb_name + ' (' + ', \n'.join(lines) + ');'    
    cursor.execute(expr)
    connection.commit()
    
sql_parser = SqlSimpleDumpParser()
table_name_created = []
insert_count = 0

def line_insert_callback(table_name, row, field_names):
    global insert_count
    if table_name not in table_name_created:
        create_table(sql_parser.table_descriptions[table_name], table_name, cursor, connection)
        print(table_name)
        table_name_created.append(table_name)
    expr = 'INSERT INTO ' + table_name + ' (' + ', '.join(field_names) + ') VALUES (' + ', '.join (['?'] * len (field_names)) +');'
    cursor.execute(expr, row)
    insert_count = insert_count + 1
    if insert_count == 100:
        connection.commit()
        insert_count = 0

with open(dump_path, "r", encoding='UTF-8') as file_in:
    data = sql_parser.parse_tables(file_in, custom_iterate_function = line_insert_callback, custom_data_convert_function=custom_data_convert_function)
    print(sql_parser.table_descriptions)

connection.commit()
connection.close()