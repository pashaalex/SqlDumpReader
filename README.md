# Simple use:
```
from sql_dump_parser import SqlSimpleDumpParser

sample_lines = [
    'create table TBL1 (id1 int, id2 int, id3 int);',
    'insert into TBL1 (id2, id1) values (1, 2)',
    'insert into TBL1 values (3, 4, 5)'
    ]

sql_parser = SqlSimpleDumpParser()
data = sql_parser.parse_tables(sample_lines)
print(data)
print(sql_parser.table_descriptions)
```
output:
```
{'TBL1': [[2, 1, None], [3, 4, 5]]}
{'TBL1': {'id1': int, 'id2': int, 'id3': int}}
```

# Read files:
```
from sql_dump_parser import SqlSimpleDumpParser
sql_parser = SqlSimpleParser()
with open("sample_data\\dump01.sql", "r", encoding='UTF-8') as file_in:
    data = sql_parser.parse_tables(file_in)
```

# Convert to Pandas:
```
from sql_dump_parser import SqlSimpleDumpParser
import pandas as pd

sample_lines = [
    'create table TBL1 (id1 int, id2 int, id3 int);',
    'insert into TBL1 (id1, id2, id3) values (1, 2, 3)',
    'insert into TBL1 values (4, 5, 6)'
    ]

sql_parser = SqlSimpleDumpParser()
data = sql_parser.parse_tables(sample_lines)    
data_frame = pd.DataFrame(data['TBL1'], columns=list(sql_parser.table_descriptions['TBL1'].keys()))
print(data_frame.head())
```
Output:
```
   id1  id2  id3
0    1    2    3
1    4    5    6
```

# Customize data convertion
```
from sql_dump_parser import SqlSimpleDumpParser
import datetime

sample_lines = [
    'create table TBL1 (id1 int, dt datetime);',
    'insert into TBL1 (id1, dt) values (1, \'20240101\')'    
    ]

def custom_data_convert_function(obj_tokens, data_type):
    if data_type.first().upper() == 'DATETIME':        
         return datetime.datetime.strptime(obj_tokens[0].name, "%Y%m%d").date(), True
    return obj_tokens, False

sql_parser = SqlSimpleDumpParser()
data = sql_parser.parse_tables(sample_lines, custom_data_convert_function=custom_data_convert_function)
print(data)
```
output:
```
{'TBL1': [[1, datetime.date(2024, 1, 1)]]}
```

# Multiple tables
```
from sql_dump_parser import SqlSimpleDumpParser

sample_lines = [
    'create table TBL1 (id1 int, id2 int);',
    'insert into TBL1  values (1, 2), (3, 4)',
    'create table TBL2 (id3 int, id4 int);',
    'insert into TBL2  values (4, 5), (6, 7)'   
    ]

sql_parser = SqlSimpleDumpParser()
data = sql_parser.parse_tables(sample_lines)
print(data)
print(sql_parser.table_descriptions)
```
Output:
```
{'TBL1': [[1, 2], [3, 4]], 'TBL2': [[4, 5], [6, 7]]}
{'TBL1': {'id1': int, 'id2': int}, 'TBL2': {'id3': int, 'id4': int}}
```

# Specify tables to import
```
from sql_dump_parser import SqlSimpleDumpParser

sample_lines = [
    'create table TBL1 (id1 int, id2 int);',
    'insert into TBL1  values (1, 2), (3, 4)',
    'create table TBL2 (id3 int, id4 int);',
    'insert into TBL2  values (4, 5), (6, 7)'   
    ]

sql_parser = SqlSimpleDumpParser()
data = sql_parser.parse_tables(sample_lines, { 'TBL2': []})
print(data)
```
Output:
```
{'TBL2': [[4, 5], [6, 7]]}
```

# Specify columns to import:
```
from sql_dump_parser import SqlSimpleDumpParser

sample_lines = [
    'create table TBL1 (id1 int, id2 int, id3 int);',
    'insert into TBL1  values (1, 2, 3), (4, 5, 6)'
    ]

sql_parser = SqlSimpleDumpParser()
data = sql_parser.parse_tables(sample_lines, { 'TBL1': ['id1', 'id2']})
print(data)
```
Output:
```
{'TBL1': [[1, 2], [4, 5]]}
```

# Specify max row count for all imported table
```
from sql_dump_parser import SqlSimpleDumpParser

sample_lines = [
    'create table TBL1 (id1 int, id2 int, id3 int);',
    'insert into TBL1  values (1, 2, 3), (4, 5, 6), (7, 8, 9)'
    ]

sql_parser = SqlSimpleDumpParser()
data = sql_parser.parse_tables(sample_lines, max_row_count=2)
print(data)
```
Output:
```
{'TBL1': [[1, 2, 3], [4, 5, 6]]}
```
