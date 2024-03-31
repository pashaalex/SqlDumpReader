import pytest  
from sql_dump_parser import SqlSimpleLexer
from sql_dump_parser import SqlSimpleDumpParser

@pytest.mark.parametrize( "input_strings, expected_tokens",  
    [  
        (['abc=\'eee\''], ['abc', '=', 'eee']),
        (['abc=\'e e\''], ['abc', '=', 'e e']),
    ]) 
def test_lexer_smoke_test(input_strings, expected_tokens):
    lexer = SqlSimpleLexer()
    real_tokens = [a.name for a in lexer.tokenize(input_strings)]
    assert len(real_tokens) == len(expected_tokens)
    assert all([a == b for a, b in zip(real_tokens, expected_tokens)])

def test_parser_smoke_test():
        sample_lines = [
            'create table TBL1 (id1 int, id2 int, id3 int);',
            'insert into TBL1 (id2, id1) values (1, 2)'
            ]
        sql_parser = SqlSimpleDumpParser()
        data = sql_parser.parse_tables(sample_lines)
        table_names = list(data.keys())
        assert len(table_names) == 1
        assert table_names[0] == 'TBL1'
