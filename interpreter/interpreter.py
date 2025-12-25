"""
AST Interpreter for the CleanWorld Language
============================================
This interpreter executes programs directly from the Abstract Syntax Tree (AST).
It simulates a grid world with an agent that can move, turn, clean, and sense dirt.

"""

import sys
import json
from typing import Dict, Any, List, Optional, Tuple


# ============================================================================
#                          RUNTIME ENVIRONMENT
# ============================================================================

class Environment:
    """
    Runtime environment that stores variable values.
    """
    def __init__(self, parent: Optional['Environment'] = None):
        self.vars: Dict[str, Any] = {}
        self.parent = parent
    
    def define(self, name: str, value: Any):
        """Define a new variable in this scope."""
        self.vars[name] = value
    
    def get(self, name: str) -> Any:
        """Get variable value, checking parent scopes if needed."""
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable: {name}")
    
    def set(self, name: str, value: Any):
        """Set variable value in the scope where it was defined."""
        if name in self.vars:
            self.vars[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise RuntimeError(f"Undefined variable: {name}")


# ============================================================================
#                          GRID WORLD SIMULATION
# ============================================================================

class GridWorld:
    """
    Simulates a 2D grid world with an agent that can move and clean dirt.
    """
    DIRECTIONS = ['north', 'east', 'south', 'west']  # Clockwise order
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.agent_x = 0
        self.agent_y = 0
        self.agent_direction = 'north'  # north, south, east, west
        self.dirt: set = set()  # Set of (x, y) coordinates with dirt
        
        # Initialize with some dirt for testing
        self.dirt.add((2, 2))
        self.dirt.add((3, 1))
        self.dirt.add((1, 3))
    
    def move(self):
        
        new_x, new_y = self.agent_x, self.agent_y
        
        if self.agent_direction == 'north':
            new_y -= 1
        elif self.agent_direction == 'south':
            new_y += 1
        elif self.agent_direction == 'east':
            new_x += 1
        elif self.agent_direction == 'west':
            new_x -= 1
        
        # Check bounds
        if 0 <= new_x < self.width and 0 <= new_y < self.height:
            self.agent_x, self.agent_y = new_x, new_y
        else:
            raise RuntimeError(f"Cannot move: agent would move off grid at ({new_x}, {new_y})")
    
    def turn_left(self):
        """Turn agent 90 degrees counter-clockwise."""
        idx = self.DIRECTIONS.index(self.agent_direction)
        self.agent_direction = self.DIRECTIONS[(idx - 1) % 4]
    
    def turn_right(self):
        """Turn agent 90 degrees clockwise."""
        idx = self.DIRECTIONS.index(self.agent_direction)
        self.agent_direction = self.DIRECTIONS[(idx + 1) % 4]
    
    def clean(self):
        """Clean dirt at current position."""
        pos = (self.agent_x, self.agent_y)
        if pos in self.dirt:
            self.dirt.remove(pos)
    
    def sense(self) -> bool:
        """Return True if there is dirt at current position."""
        return (self.agent_x, self.agent_y) in self.dirt
    
    def display(self):
        """Print the current state of the grid."""
        print("\n" + "=" * (self.width * 4 + 1))
        for y in range(self.height):
            row = "|"
            for x in range(self.width):
                if (x, y) == (self.agent_x, self.agent_y):
                    # Show agent with direction
                    if self.agent_direction == 'north':
                        row += " ^ |"
                    elif self.agent_direction == 'south':
                        row += " v |"
                    elif self.agent_direction == 'east':
                        row += " > |"
                    elif self.agent_direction == 'west':
                        row += " < |"
                elif (x, y) in self.dirt:
                    row += " * |"  # * represents dirt
                else:
                    row += "   |"
            print(row)
            print("-" * (self.width * 4 + 1))
        print(f"Agent: ({self.agent_x}, {self.agent_y}) facing {self.agent_direction}")
        print(f"Dirt remaining: {len(self.dirt)} cells")
        print("=" * (self.width * 4 + 1) + "\n")


# ============================================================================
#                          AST INTERPRETER
# ============================================================================

class Interpreter:
    """
    Executes a CleanWorld program from its AST representation.
    """
    def __init__(self, ast: Dict[str, Any], verbose: bool = False):
        self.ast = ast
        self.env = Environment()
        self.grid: Optional[GridWorld] = None
        self.verbose = verbose
        self.const_vars: set = set()  # Track const variables
    
    def run(self):
        """Main entry point to execute the program."""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"  EXECUTING PROGRAM: {self.ast.get('name', 'Unknown')}")
            print(f"{'='*60}\n")
        
        # Execute all statements in the program body
        for stmt in self.ast.get('body', []):
            self.execute_stmt(stmt)
        
        # Display final grid state
        if self.grid:
            print("\n[FINAL GRID STATE]")
            self.grid.display()
        
        if self.verbose:
            print(f"\n{'='*60}")
            print("  PROGRAM EXECUTION COMPLETED")
            print(f"{'='*60}\n")
    
    # ========================================================================
    #                      STATEMENT EXECUTION
    # ========================================================================
    
    def execute_stmt(self, stmt: Dict[str, Any]):
        """Execute a single statement."""
        stmt_type = stmt.get('type')
        
        if stmt_type == 'VarDecl':
            self.execute_var_decl(stmt)
        elif stmt_type == 'ConstDecl':
            self.execute_const_decl(stmt)
        elif stmt_type == 'Assign':
            self.execute_assign(stmt)
        elif stmt_type == 'IfStmt':
            self.execute_if(stmt)
        elif stmt_type == 'WhileStmt':
            self.execute_while(stmt)
        elif stmt_type == 'ActionStmt':
            self.execute_action(stmt)
        else:
            raise RuntimeError(f"Unknown statement type: {stmt_type}")
    
    def execute_var_decl(self, stmt: Dict[str, Any]):
        """Execute variable declaration: var x : int = 5;"""
        name = stmt['id']['name']
        var_type = stmt.get('varType', 'unknown')
        init_value = stmt.get('init')
        
        if init_value:
            value = self.evaluate_expr(init_value)
        else:
            # Default values based on type
            if var_type == 'int':
                value = 0
            elif var_type == 'bool':
                value = False
            elif var_type == 'direction':
                value = 'north'
            else:
                value = None
        
        self.env.define(name, value)
        
        if self.verbose:
            print(f"[VAR] {name} : {var_type} = {value}")
    
    def execute_const_decl(self, stmt: Dict[str, Any]):
        """Execute constant declaration: const x : int = 5;"""
        name = stmt['id']['name']
        var_type = stmt.get('varType', 'unknown')
        value = self.evaluate_expr(stmt['value'])
        
        self.env.define(name, value)
        self.const_vars.add(name)  # Mark as constant
        
        if self.verbose:
            print(f"[CONST] {name} : {var_type} = {value}")
    
    def execute_assign(self, stmt: Dict[str, Any]):
        """Execute assignment: x = 10;"""
        name = stmt['target']['name']
        
        # Check if trying to assign to a constant
        if name in self.const_vars:
            raise RuntimeError(f"Cannot assign to constant: {name}")
        
        value = self.evaluate_expr(stmt['value'])
        self.env.set(name, value)
        
        if self.verbose:
            print(f"[ASSIGN] {name} = {value}")
    
    def execute_if(self, stmt: Dict[str, Any]):
        """Execute if statement: if (condition) { ... } else { ... }"""
        condition = self.evaluate_expr(stmt['test'])
        
        if self.verbose:
            print(f"[IF] condition = {condition}")
        
        if condition:
            for s in stmt.get('consequent', []):
                self.execute_stmt(s)
        elif stmt.get('alternate'):
            if self.verbose:
                print(f"[ELSE]")
            for s in stmt['alternate']:
                self.execute_stmt(s)
    
    def execute_while(self, stmt: Dict[str, Any]):
        """Execute while loop: while (condition) { ... }"""
        iteration = 0
        max_iterations = 10000  # Safety limit
        
        while self.evaluate_expr(stmt['test']):
            iteration += 1
            if iteration > max_iterations:
                raise RuntimeError("Infinite loop detected (exceeded 10000 iterations)")
            
            if self.verbose:
                print(f"[WHILE] iteration {iteration}")
            
            for s in stmt.get('body', []):
                self.execute_stmt(s)
    
    def execute_action(self, stmt: Dict[str, Any]):
        """Execute built-in action: move, clean, turnLeft, etc."""
        action = stmt['action']
        
        # Initialize grid if this is the first action and grid exists
        if not self.grid:
            raise RuntimeError("Grid not initialized. Missing grid() declaration?")
        
        if self.verbose:
            print(f"[ACTION] {action}")
        
        if action == 'move':
            self.grid.move()
        elif action == 'turnLeft':
            self.grid.turn_left()
        elif action == 'turnRight':
            self.grid.turn_right()
        elif action == 'clean':
            self.grid.clean()
        elif action == 'sense':
            # sense is typically used in expressions, not as a statement
            # But we'll support it
            result = self.grid.sense()
            if self.verbose:
                print(f"  -> sense() = {result}")
        else:
            raise RuntimeError(f"Unknown action: {action}")
    
    # ========================================================================
    #                      EXPRESSION EVALUATION
    # ========================================================================
    
    def evaluate_expr(self, expr: Dict[str, Any]) -> Any:
        """Evaluate an expression and return its value."""
        if expr is None:
            return None
        
        expr_type = expr.get('type')
        
        if expr_type == 'Literal':
            return expr['value']
        
        elif expr_type == 'Identifier':
            name = expr['name']
            
            # Special built-in identifiers
            if name == 'sense':
                if self.grid:
                    return self.grid.sense()
                else:
                    raise RuntimeError("Cannot call sense: grid not initialized")
            elif name == 'dirt':
                raise RuntimeError("'dirt' is not a valid identifier")
            
            # Regular variable
            return self.env.get(name)
        
        elif expr_type == 'BinaryExpr':
            return self.evaluate_binary_expr(expr)
        
        else:
            raise RuntimeError(f"Unknown expression type: {expr_type}")
    
    def evaluate_binary_expr(self, expr: Dict[str, Any]) -> Any:
        """Evaluate binary expressions (arithmetic, logical, relational)."""
        operator = expr['operator']
        
        # Handle unary NOT
        if operator == 'not':
            right = self.evaluate_expr(expr['left'])
            return not right
        
        left = self.evaluate_expr(expr['left'])
        right = self.evaluate_expr(expr['right'])
        
        # Arithmetic operators
        if operator == '+':
            return left + right
        elif operator == '-':
            return left - right
        elif operator == '*':
            return left * right
        elif operator == '/':
            if right == 0:
                raise RuntimeError("Division by zero")
            return left // right  # Integer division
        
        # Relational operators
        elif operator == '==':
            return left == right
        elif operator == '!=':
            return left != right
        elif operator == '<':
            return left < right
        elif operator == '<=':
            return left <= right
        elif operator == '>':
            return left > right
        elif operator == '>=':
            return left >= right
        
        # Logical operators
        elif operator == 'and':
            return left and right
        elif operator == 'or':
            return left or right
        
        else:
            raise RuntimeError(f"Unknown operator: {operator}")


# ============================================================================
#                          HELPER FUNCTIONS
# ============================================================================

def load_ast(filepath: str) -> Dict[str, Any]:
    """Load AST from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


# ============================================================================
#                          MAIN ENTRY POINT
# ============================================================================

def main():
    """Main function for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <ast_file.json> [--verbose]")
        print("   or: python interpreter.py <source_file.clean> [--verbose]")
        print("\nIf a .clean file is provided, the full pipeline will run automatically.")
        sys.exit(1)
    
    filepath = sys.argv[1]
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    ast = None
    cst = None
    
    # Check if input is .clean source file
    if filepath.endswith('.clean'):
        print(f"\n{'='*60}")
        print(f"  RUNNING FULL COMPILATION PIPELINE")
        print(f"{'='*60}\n")
        
        # Import required modules
        from lexer import get_token_stream
        from parser import Parser
        from converter import convert_cst_to_ast
        from semantic import analyze
        
        # Read source code
        with open(filepath, 'r') as f:
            source = f.read()
        
        print("[1/5] Lexical Analysis...")
        tokens = get_token_stream(source)
        print(f"      Found {len(tokens)} tokens")
        
        print("[2/5] Parsing...")
        parser = Parser(tokens)
        cst_root = parser.parse_program()
        cst = cst_root.to_dict()
        print(f"      CST created successfully")
        
        print("[3/5] AST Conversion...")
        ast = convert_cst_to_ast(cst)
        print(f"      AST created successfully")
        
        print("[4/5] Semantic Analysis...")
        errors = analyze(ast)
        if errors:
            print(f"      Found {len(errors)} semantic error(s):")
            for error in errors:
                print(f"        - {error['code']}: {error['msg']}")
            sys.exit(1)
        print(f"      No semantic errors found")
        
        print("[5/5] Interpretation & Execution...")
        
    elif filepath.endswith('.json'):
        # Load AST directly
        ast = load_ast(filepath)
    else:
        print("Error: File must be either .clean (source) or .json (AST)")
        sys.exit(1)
    
    # Create interpreter with default 5x5 grid
    interpreter = Interpreter(ast, verbose=verbose)
    interpreter.grid = GridWorld(5, 5)
    
    # Display initial grid
    if verbose:
        print("\n[INITIAL GRID STATE]")
        interpreter.grid.display()
    
    # Run the program
    try:
        interpreter.run()
        print("\n[SUCCESS] Program executed successfully!")
    except RuntimeError as e:
        print(f"\n[ERROR] Runtime Error: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"\n[ERROR] KeyError: {e}")
        print("This might indicate an issue with the AST structure.")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
