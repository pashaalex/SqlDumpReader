from decimal import Decimal
import enum

class SqlDataType(object):
    tokens = None
    def __init__(self):
        self.tokens = []
    
    def append(self, obj):
        self.tokens.append(obj)
        
    def first(self):
        return self.tokens[0].name

    def __repr__(self): 
        return self.first()

class IterWrapper:
    _gen = None
    stack = []
    def __init__(self, gen):
        self.n = 0
        self._gen = gen

    def __iter__(self):
        return self
    
    def back(self, obj):
        self.stack.append(obj)

    def __next__(self):
        if len(self.stack) > 0:
            return self.stack.pop()
        else:
            return next(self._gen)

class SqlTokenType(enum.Enum):
    state_none = 0
    state_symb = 1
    state_comment = 2    
    state_string = 3 # starts with '
    state_backtrick = 4 # starts with `    
    state_identifier = 5 # starts with [
    state_token = 6
    state_punct = 7
    
class SqlToken:
    name = None,
    token_type = SqlTokenType.state_none
    def __init__(self, name, token_type):
        self.name = name
        self.token_type = token_type
    def __repr__(self): 
        return '[' + self.token + ' ' + str(self.token_type) + ']'
    
class SqlSimpleLexer:
    punct = ['.', ';', ',', '(', ')', '=', '/', '*', '-']
    
    def tokenize(self, lines):
        for line in lines:
            line = line.strip()
            i1 = 0
            i2 = 0
            state = SqlTokenType.state_none
            while i2 < len(line):
                symb = line[i2]
                if i2 > 0:
                    prevSymb = line[i2-1]
                else:
                    prevSymb = ''
                  
                if state == SqlTokenType.state_none:
                    # state = None
                    if symb in self.punct:
                        i1 = i2 + 1
                        yield SqlToken(symb, SqlTokenType.state_punct)
                    elif symb == '`':
                        i1 = i2 + 1
                        state = SqlTokenType.state_backtrick
                    elif symb == '\'':
                        i1 = i2 + 1
                        state = SqlTokenType.state_string
                    elif symb == '[':
                        i1 = i2 + 1
                        state = SqlTokenType.state_identifier
                    elif symb != ' ':
                        i1 = i2
                        state = SqlTokenType.state_token
                elif state == SqlTokenType.state_comment:
                    # state = Comment
                    if symb == '/' and prevSymb == '*':
                        state = SqlTokenType.state_none
                elif state == SqlTokenType.state_string:
                    if symb == '\'' and prevSymb != '\\':
                        state = SqlTokenType.state_none                        
                        yield SqlToken(line[i1:i2], SqlTokenType.state_string)
                        i1 = i2 + 1
                elif state == SqlTokenType.state_backtrick:
                    if symb == '`':
                        state = SqlTokenType.state_none                        
                        yield SqlToken(line[i1:i2], SqlTokenType.state_backtrick)
                        i1 = i2 + 1
                elif state == SqlTokenType.state_identifier:
                    if symb == ']':
                        state = SqlTokenType.state_none                        
                        yield SqlToken(line[i1:i2], SqlTokenType.state_identifier)
                        i1 = i2 + 1                        
                elif state == SqlTokenType.state_token:
                    if symb == '-' and prevSymb == '-':
                        state = SqlTokenType.state_none
                        break # this line is whole comment, so go next line
                    if symb == '\'':                        
                        yield SqlToken(line[i1:i2], SqlTokenType.state_token) 
                        i1 = i2 + 1
                        state = SqlTokenType.state_string
                    elif symb == '*' and prevSymb == '/':
                        state = SqlTokenType.state_comment
                    elif symb == ' ':
                        state = SqlTokenType.state_none
                        yield SqlToken(line[i1:i2], SqlTokenType.state_token)
                        i1 = i2 + 1
                    elif symb in self.punct:
                        i2 = i2 - 1
                        state = SqlTokenType.state_none
                        yield SqlToken(line[i1:i2+1], SqlTokenType.state_token)
                i2 = i2 + 1
            if state == SqlTokenType.state_token and i2 > i1:
                yield SqlToken(line[i1:], SqlTokenType.state_token)

class SqlSimpleDumpParser:
    table_descriptions = {}
    data_config = None
    table_data = {}
    max_row_count = -1
    custom_data_convert_function = None
    custom_iterate_function = None
    
    def parse_table_def(self, tokenizer):
        keywords = ['PRIMARY', 'UNIQUE', 'KEY', 'CONSTRAINT', 'FOREIGN']
        table_def = {}
        table_name_tokens = []
        token = next(tokenizer)              
        while token.name != '(':
            table_name_tokens.append(token.name)
            token = next(tokenizer)
        table_name = ''.join(table_name_tokens)
        while (True):
            token = next(tokenizer)
            field_name = token.name
            data_type = SqlDataType()
            if field_name not in keywords:
                token = next(tokenizer)
                data_type.append(token)
                table_def[field_name] = data_type
            ccnt = 0
            while not (token.name == ',' and ccnt == 0):
                token = next(tokenizer)
                data_type.append(token)
                if token.name == '(' : ccnt = ccnt + 1
                if token.name == ')' : ccnt = ccnt - 1
                if ccnt < 0: break
            if token.name == ')':
                break
        
        return table_name, table_def
    
    def convert_data_type(self, obj_tokens, data_type):
        if obj_tokens == None: return None, True
        obj = ''.join([t.name for t in obj_tokens])
        if obj.upper() == 'NULL': return None, True
        if data_type.first() == 'tinyint' or data_type.first() == 'int' or data_type.first() == 'smallint': return int(obj), True
        if data_type.first() == 'double' or data_type.first() == 'float': return float(obj), True
        if data_type.first() == 'decimal' : return float(Decimal(obj)), True
        return obj, False
    
    def run_to_end_bracket(self, tokenizer):
        ccnt = 0
        while ccnt >= 0:
            token = next(tokenizer)
            if token.name == '(' : ccnt = ccnt + 1
            if token.name == ')' : ccnt = ccnt - 1

    def get_to_delimeter(self, tokenizer, delimeter):
        tokens = []
        ccnt = 0
        while ccnt >= 0:
            token = next(tokenizer)
            tokens.append(token)
            if token.name == '(' : ccnt = ccnt + 1
            if token.name == ')' and ccnt == 0:
                tokens.pop()
                tokenizer.back(token)
                return tokens
            if token.name == ')' : ccnt = ccnt - 1
            if ccnt == 0 and token.name == delimeter:
                tokens.pop()
                return tokens
        
    def run_to_end_insert_clause(self, tokenizer):
        token = next(tokenizer)
        while token.name.upper() != 'VALUES':
            token = next(tokenizer)
        while(True):
            while token.name != '(':
                token = next(tokenizer)
            self.run_to_end_bracket(tokenizer)
            token = next(tokenizer)
            if token.name != ',':
                tokenizer.back(token)
                break
    
    def parse_insert(self, tokenizer, callback = None):
        token = next(tokenizer)
        if token.name.upper() != 'INTO':
            tokenizer.back(token)
            
        if callback == None:
            self.run_to_end_insert_clause(tokenizer)
            return
        
        table_name_tokens = []
        token = next(tokenizer)
        while token.name != '(' and token.name.upper() != 'VALUES':
            table_name_tokens.append(token.name)
            token = next(tokenizer)
        table_name = ''.join(table_name_tokens)
        field_names = []
        table_def = self.table_descriptions[table_name]
        if token.name == '(':
        # insert into TBL (field names) values (...)
            token = next(tokenizer)
            while token.name != ')':
                if token.name != ',':
                    field_names.append(token.name)
                token = next(tokenizer)
        else:
        # insert into TBL values (...)
            field_names = list(table_def.keys())
            
        state = 0
        
        while token != ';':
            token = next(tokenizer)
            if token.name != ',' and token.name != '(' and token.name.upper() != 'VALUES':
                tokenizer.back(token)
                break;
            if token.name == '(':
                row_raw = []
                joint_token = ''
                while True:
                    tokens = self.get_to_delimeter(tokenizer, ',')
                    #str_tokens = ''.join([t.name for t in tokens])
                    row_raw.append(tokens)
                    token = next(tokenizer)
                    if token.name == ')':
                        tokenizer.back(token)
                        break
                    else:
                        tokenizer.back(token)
                row = []
                need_fields = []
                if self.data_config != None:
                    need_fields = self.data_config.get(table_name, [])
                if len(need_fields) == 0:
                    need_fields = list(table_def.keys())

                row_dict = {}
                for field_name, obj in zip(field_names, row_raw):
                    row_dict[field_name] = obj
                
                for field_name in need_fields:
                    obj = row_dict.get(field_name, None)
                    data_type = table_def[field_name]
                    res = False
                    converted_obj = None
                    if self.custom_data_convert_function != None:                        
                        converted_obj, res = self.custom_data_convert_function(obj, data_type)
                    if not res:
                        converted_obj, res = self.convert_data_type(obj, data_type)
                    row.append(converted_obj)
                
                if self.data_config == None or table_name in self.data_config:
                    callback(table_name, row, need_fields)
                token = next(tokenizer) # ")" after tokens

    def default_insert_callback(self, table_name, row, field_names):
        table_data_list = self.table_data[table_name]
        if self.max_row_count == -1 or len(table_data_list) < self.max_row_count:
            self.table_data[table_name].append(row)

    def parse_lines(self, lines):
        lexer = SqlSimpleLexer()
        tokenizer = IterWrapper(lexer.tokenize(lines))
        try:
            prevToken = ''
            while True:
                token = next(tokenizer)
                token_str = token.name.upper()
                if prevToken == 'CREATE' and token_str == 'TABLE':
                    table_name, table_def = self.parse_table_def(tokenizer)
                    self.table_descriptions[table_name] = table_def
                    if self.data_config == None or table_name in self.data_config:
                        self.table_data[table_name] = []

                if token_str == 'INSERT':
                    if self.custom_iterate_function != None:
                        self.parse_insert(tokenizer, self.custom_iterate_function)
                    else:
                        self.parse_insert(tokenizer, self.default_insert_callback)
                prevToken = token_str
        except StopIteration:
            pass
        
    def parse_tables(self, lines, data = None, max_row_count = -1, custom_iterate_function = None, custom_data_convert_function = None):
        self.custom_data_convert_function = custom_data_convert_function
        self.custom_iterate_function = custom_iterate_function
        self.data_config = data
        self.table_descriptions = {}
        self.table_data = {}
        self.max_row_count = max_row_count
        self.parse_lines(lines)
        return self.table_data
    
    def parse_tables_struct(self, lines):
        self.parse_tables(lines, {})
        return self.table_descriptions

