import sys
import json
from lexer import get_token_stream
from cst import CSTNode

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else None

    # ==================================================================
    #                        HELPER METHODS
    # ==================================================================

    def eat(self, token_type):
        """
        Consumes the current token if it matches the expected type.
        Returns a CSTNode for the terminal.
        """
        if self.current_token and self.current_token[0] == token_type:
            # Create a leaf node for the token
            node = CSTNode("TERMINAL", value=self.current_token[1])
            self.advance()
            return node
        else:
            current_val = self.current_token if self.current_token else "EOF"
            raise SyntaxError(f"Expected {token_type} but found {current_val}")

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def peek(self):
        """Returns the type of the current token safely."""
        return self.current_token[0] if self.current_token else None

    # ==================================================================
    #                        PROGRAM STRUCTURE
    # ==================================================================

    def parse_program(self):
        # <program> ::= PROGRAM ID LBRACE <world_def> <declarations> <statements> RBRACE
        root = CSTNode("PROGRAM")
        
        root.add_child(self.eat("PROGRAM"))
        root.add_child(self.eat("ID"))
        root.add_child(self.eat("LBRACE"))
        
        root.add_child(self.parse_world_def())
        root.add_child(self.parse_declarations())
        root.add_child(self.parse_statements())
        
        root.add_child(self.eat("RBRACE"))
        return root

    def parse_world_def(self):
        # <world_def> ::= GRID LPAREN INT_LITERAL COMMA INT_LITERAL RPAREN SEMICOLON
        node = CSTNode("WORLD_DEF")
        node.add_child(self.eat("GRID"))
        node.add_child(self.eat("LPAREN"))
        node.add_child(self.eat("INT_LITERAL"))
        node.add_child(self.eat("COMMA"))
        node.add_child(self.eat("INT_LITERAL"))
        node.add_child(self.eat("RPAREN"))
        node.add_child(self.eat("SEMICOLON"))
        return node

    def parse_declarations(self):
        # <declarations> ::= { <declaration> }
        node = CSTNode("DECLARATIONS")
        while self.peek() in ["CONST", "VAR"]:
            node.add_child(self.parse_declaration())
        return node

    def parse_declaration(self):
        # <declaration> logic with Left Factoring
        node = CSTNode("DECLARATION")
        
        if self.peek() == "CONST":
            # CONST ID COLON <type> ASSIGN <expression> SEMICOLON
            node.add_child(self.eat("CONST"))
            node.add_child(self.eat("ID"))
            node.add_child(self.eat("COLON"))
            node.add_child(self.parse_type())
            node.add_child(self.eat("ASSIGN"))
            node.add_child(self.parse_expression())
            node.add_child(self.eat("SEMICOLON"))
            
        elif self.peek() == "VAR":
            # VAR ID COLON <type> <var_tail>
            node.add_child(self.eat("VAR"))
            node.add_child(self.eat("ID"))
            node.add_child(self.eat("COLON"))
            node.add_child(self.parse_type())
            node.add_child(self.parse_var_tail())
            
        else:
            raise SyntaxError("Expected CONST or VAR")
        return node

    def parse_var_tail(self):
        node = CSTNode("VAR_TAIL")
        if self.peek() == "SEMICOLON":
            node.add_child(self.eat("SEMICOLON"))
        elif self.peek() == "ASSIGN":
            node.add_child(self.eat("ASSIGN"))
            node.add_child(self.parse_expression())
            node.add_child(self.eat("SEMICOLON"))
        else:
            raise SyntaxError("Invalid Variable Declaration Tail")
        return node

    def parse_type(self):
        node = CSTNode("TYPE")
        if self.peek() in ["TYPE_INT", "TYPE_BOOL", "TYPE_DIRECTION"]:
            node.add_child(self.eat(self.peek()))
        else:
            raise SyntaxError(f"Expected Type, found {self.peek()}")
        return node

    # ==================================================================
    #                        STATEMENTS
    # ==================================================================

    def parse_statements(self):
        node = CSTNode("STATEMENTS")
        # Continue parsing while we see start of valid statements
        # Valid starts: ID (assignment), IF, WHILE, LBRACE, MOVE, TURN..., CLEAN, SENSE
        valid_starts = ["ID", "IF", "WHILE", "LBRACE", "MOVE", "TURN_LEFT", "TURN_RIGHT", "CLEAN", "SENSE"]
        
        while self.peek() in valid_starts:
            node.add_child(self.parse_statement())
        return node

    def parse_statement(self):
        token_type = self.peek()
        
        if token_type == "ID":
            return self.parse_assignment()
        elif token_type == "IF":
            return self.parse_if()
        elif token_type == "WHILE":
            return self.parse_while()
        elif token_type == "LBRACE":
            return self.parse_block()
        elif token_type in ["MOVE", "TURN_LEFT", "TURN_RIGHT", "CLEAN", "SENSE"]:
            return self.parse_action()
        else:
            raise SyntaxError(f"Unexpected token in statement: {token_type}")

    def parse_block(self):
        node = CSTNode("BLOCK")
        node.add_child(self.eat("LBRACE"))
        node.add_child(self.parse_statements())
        node.add_child(self.eat("RBRACE"))
        return node

    def parse_assignment(self):
        # <assignment> ::= ID ASSIGN <expression> SEMICOLON
        node = CSTNode("ASSIGNMENT")
        node.add_child(self.eat("ID"))
        node.add_child(self.eat("ASSIGN"))
        node.add_child(self.parse_expression())
        node.add_child(self.eat("SEMICOLON"))
        return node

    def parse_if(self):
        # <if_statement> ::= IF LPAREN <condition> RPAREN <block> <else_part>
        node = CSTNode("IF_STATEMENT")
        node.add_child(self.eat("IF"))
        node.add_child(self.eat("LPAREN"))
        node.add_child(self.parse_condition())
        node.add_child(self.eat("RPAREN"))
        node.add_child(self.parse_block())
        node.add_child(self.parse_else_part())
        return node

    def parse_else_part(self):
        # <else_part> ::= ELSE <block> | ε
        node = CSTNode("ELSE_PART")
        if self.peek() == "ELSE":
            node.add_child(self.eat("ELSE"))
            node.add_child(self.parse_block())
        # If no ELSE, we return the empty node (Epsilon)
        return node

    def parse_while(self):
        # <while_statement> ::= WHILE LPAREN <condition> RPAREN <block>
        node = CSTNode("WHILE_STATEMENT")
        node.add_child(self.eat("WHILE"))
        node.add_child(self.eat("LPAREN"))
        node.add_child(self.parse_condition())
        node.add_child(self.eat("RPAREN"))
        node.add_child(self.parse_block())
        return node

    def parse_action(self):
        # <action_statement> ::= MOVE SEMICOLON | TURN_LEFT SEMICOLON ...
        node = CSTNode("ACTION")
        if self.peek() in ["MOVE", "TURN_LEFT", "TURN_RIGHT", "CLEAN", "SENSE"]:
            node.add_child(self.eat(self.peek()))
            node.add_child(self.eat("SEMICOLON"))
        else:
            raise SyntaxError("Expected Action Statement")
        return node

    # ==================================================================
    #                        CONDITIONS
    # ==================================================================

    def parse_condition(self):
        # <condition> ::= <expression> <condition_tail>
        node = CSTNode("CONDITION")
        node.add_child(self.parse_expression())
        node.add_child(self.parse_condition_tail())
        return node

    def parse_condition_tail(self):
        # <condition_tail> ::= <relational_op> <expression> | ε
        node = CSTNode("CONDITION_TAIL")
        if self.peek() in ["EQ", "NEQ", "LT", "LE", "GT", "GE"]:
            node.add_child(self.parse_relational_op())
            node.add_child(self.parse_expression())
        return node

    def parse_relational_op(self):
        node = CSTNode("REL_OP")
        node.add_child(self.eat(self.peek()))
        return node

    # ==================================================================
    #                        EXPRESSIONS
    # ==================================================================

    def parse_expression(self):
        # <expression> ::= <term> <expression_tail>
        node = CSTNode("EXPRESSION")
        node.add_child(self.parse_term())
        node.add_child(self.parse_expression_tail())
        return node

    def parse_expression_tail(self):
        # <expression_tail> ::= <additive_op> <term> <expression_tail> | ε
        node = CSTNode("EXPRESSION_TAIL")
        if self.peek() in ["PLUS", "MINUS", "OR"]:
            node.add_child(self.parse_additive_op())
            node.add_child(self.parse_term())
            node.add_child(self.parse_expression_tail()) # Recursive
        return node

    def parse_term(self):
        # <term> ::= <factor> <term_tail>
        node = CSTNode("TERM")
        node.add_child(self.parse_factor())
        node.add_child(self.parse_term_tail())
        return node

    def parse_term_tail(self):
        # <term_tail> ::= <multiplicative_op> <factor> <term_tail> | ε
        node = CSTNode("TERM_TAIL")
        if self.peek() in ["MUL", "DIV", "AND"]:
            node.add_child(self.parse_multiplicative_op())
            node.add_child(self.parse_factor())
            node.add_child(self.parse_term_tail()) # Recursive
        return node

    def parse_factor(self):
        # <factor> ::= ID | <literal> | LPAREN <expression> RPAREN | SENSE | NOT <factor>
        node = CSTNode("FACTOR")
        token_type = self.peek()
        
        if token_type == "ID":
            node.add_child(self.eat("ID"))
        elif token_type in ["INT_LITERAL", "BOOL_LITERAL", "DIRECTION_LITERAL", "STRING_LITERAL"]:
            node.add_child(self.parse_literal())
        elif token_type == "LPAREN":
            node.add_child(self.eat("LPAREN"))
            node.add_child(self.parse_expression())
            node.add_child(self.eat("RPAREN"))
        elif token_type == "SENSE":
            node.add_child(self.eat("SENSE"))
        elif token_type == "NOT":
            node.add_child(self.eat("NOT"))
            node.add_child(self.parse_factor()) # Recursive call
        # -------------------------------
        else:
            raise SyntaxError(f"Unexpected token in factor: {token_type}")
        return node

    def parse_literal(self):
        node = CSTNode("LITERAL")
        # Just consume whichever literal type matches
        node.add_child(self.eat(self.peek()))
        return node

    def parse_additive_op(self):
        node = CSTNode("ADD_OP")
        node.add_child(self.eat(self.peek()))
        return node

    def parse_multiplicative_op(self):
        node = CSTNode("MUL_OP")
        node.add_child(self.eat(self.peek()))
        return node

# ==================================================================
#                        MAIN EXECUTION
# ==================================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        # Print to stderr so it doesn't break pipes
        print("Usage: python parser.py <filename>", file=sys.stderr)
    else:
        try:
            # 1. Read File
            filename = sys.argv[1]
            with open(filename, "r") as f:
                code = f.read()
            
            # 2. Get Token Stream (Using your Lexer from Part 1)
            tokens = get_token_stream(code)
            
            # 3. Initialize and Run Parser
            parser = Parser(tokens)
            cst_root = parser.parse_program()
            
            # 4. Output Result as JSON to STDOUT (This is what the pipe catches)
            print(json.dumps(cst_root.to_dict(), indent=4))
            
            # Save to a separate file (Backup)
            # We remove the print statement here to keep stdout clean
            output_filename = filename.replace(".clean", "_cst.json")
            with open(output_filename, "w") as f:
                json.dump(cst_root.to_dict(), f, indent=4)

        except Exception as e:
            # Print errors to stderr so they don't corrupt the JSON file
            print(f"\n[Parser Error] {e}", file=sys.stderr)
            sys.exit(1) # Return error code
