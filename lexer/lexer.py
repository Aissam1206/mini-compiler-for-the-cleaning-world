import re
import sys

# ======================================================================
#                        TOKEN DEFINITIONS
# ======================================================================

token_specification = [
    # --- FEEDBACK FIX: World Definition ---
    ("GRID",       r'\bgrid\b'),

    # Keywords
    ("PROGRAM",    r'\bprogram\b'),
    ("CONST",      r'\bconst\b'),
    ("VAR",        r'\bvar\b'),
    
    # Types 
    ("TYPE_INT",   r'\bint\b'),
    ("TYPE_BOOL",  r'\bbool\b'),
    ("TYPE_DIRECTION", r'\bdirection\b'),
    
    # Control Flow
    ("WHILE",      r'\bwhile\b'),
    ("IF",         r'\bif\b'),
    ("ELSE",       r'\belse\b'),
    
    # Agent Actions 
    ("MOVE",       r'\bmove\b'),
    ("TURN_LEFT",  r'\bturnLeft\b'),  
    ("TURN_RIGHT", r'\bturnRight\b'), 
    ("SENSE",      r'\bsense\b'),
    ("CLEAN",      r'\bclean\b'),
    
    # Literals 
    ("BOOL_LITERAL", r'\b(true|false)\b'), 
    ("DIRECTION_LITERAL", r'\b(north|south|east|west)\b'), 
    
    # --- FEEDBACK FIX: String Literals (for "Kitchen") ---
    ("STRING_LITERAL", r'\"[a-zA-Z0-9_ ]*\"'),

    # Logical Operators 
    ("AND",        r'\band\b'), 
    ("OR",         r'\bor\b'),  
    ("NOT",        r'\bnot\b'), 
    
    # Numeric Literal 
    ("INT_LITERAL", r'\d+'),   

    # Operators and Punctuation
    ("EQ",         r'=='),
    ("NEQ",        r'!='),
    ("LE",         r'<='),
    ("GE",         r'>='),
    ("LT",         r'<'),
    ("GT",         r'>'),
    ("ASSIGN",     r'='),
    ("PLUS",       r'\+'),
    ("MINUS",      r'-'),
    ("MUL",        r'\*'),
    ("DIV",        r'/'),
    ("LPAREN",     r'\('),
    ("RPAREN",     r'\)'),
    ("LBRACE",     r'\{'),
    ("RBRACE",     r'\}'),
    ("SEMICOLON",  r';'),
    ("COLON",      r':'),
    # --- FEEDBACK FIX: Comma Separator ---
    ("COMMA",      r','),
    
    # Ignored Tokens (Comments)
    ("COMMENT",    r'#.*'),
    
    # Identifier (Must be after all keywords)
    ("ID",         r'[A-Za-z_][A-Za-z0-9_]*'), 
    
    # Special "Tokens" for internal handling
    ("NEWLINE",    r'\n'),       # Used to increment line_num
    ("SKIP",       r'[ \t]+'),   # Ignored whitespace
    ("MISMATCH",   r'.'),        # Catches any other character as an error
]

# ======================================================================
#                        LEXER IMPLEMENTATION
# ======================================================================

tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
get_token = re.compile(tok_regex).match

def get_token_stream(code):
    """
    Analyzes the code string and returns a list of tokens.
    Used by the Parser.
    
    Returns:
        List of tuples: [(TOKEN_TYPE, VALUE, LINE_NUM), ...]
    """
    tokens = []
    line_num = 1
    pos = 0
    mo = get_token(code, pos)

    while mo is not None:
        kind = mo.lastgroup 
        value = mo.group()
        
        if kind == "NEWLINE":
            line_num += 1
        elif kind == "SKIP" or kind == "COMMENT":
            pass
        elif kind == "MISMATCH":
            print(f"Lexical Error at Line {line_num}: Unexpected character '{value}'")
        else:
            # Add to token list for the Parser
            tokens.append((kind, value, line_num))
                
        pos = mo.end() 
        mo = get_token(code, pos)
        
    return tokens

def print_lexer_output(tokens):
    """
    Helper function to print tables 
    """
    symbol_table = set()
    literal_table = set()

    print("----- TOKEN STREAM -----\n")
    for kind, value, line_num in tokens:
        print(f"Line {line_num}: {kind}({value})")
        
        if kind == "ID":
            symbol_table.add(value)
        elif kind == "INT_LITERAL" or kind == "STRING_LITERAL":
            literal_table.add(value)

    print("\n----- SYMBOL TABLE -----")
    for sym in sorted(symbol_table): 
        print(sym)
        
    print("\n----- LITERAL TABLE -----")
    # Sort carefully to handle mixed strings/ints
    for lit in sorted(literal_table, key=lambda x: str(x)): 
        print(lit)

def lexer(filename):
    """
    Main entry point for CLI usage.
    """
    try:
        with open(filename, 'r') as file:
            code = file.read()
    except FileNotFoundError:
        print(f"Error: File not found '{filename}'")
        return

    # Get the raw tokens (Logic)
    tokens = get_token_stream(code)
    
    # Print them 
    print_lexer_output(tokens)

# ======================================================================
#                        SCRIPT EXECUTION
# ======================================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python lexer.py <filename>")
    else:
        lexer(sys.argv[1])
