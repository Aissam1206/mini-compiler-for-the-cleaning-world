# Semantic analysis: declaration + resolution + type checking
from symbols import Scope

class SemanticError(Exception):
    def __init__(self, code, msg, pos=None):
        self.code = code
        self.msg = msg
        self.pos = pos

def analyze(ast):
    errors = []
    global_scope = Scope(None, 0)

    # ================= DECLARATION PASS =================
    # We only scan the top-level body because our language 
    # enforces that ALL variables are global (at the top).
    for stmt in ast.get("body", []):
        t = stmt.get("type")
        if t in ("ConstDecl", "VarDecl"):
            name = stmt["id"]["name"]
            var_type = stmt.get("varType", "unknown") # Get the type extracted by converter
            
            try:
                # Determine category (const vs var)
                category = "const" if t == "ConstDecl" else "var"
                
                #Pass 'category' AND 'var_type' to the symbol table
                global_scope.declare(name, category, var_type, stmt)
            except KeyError as e:
                errors.append({"code": "E_DUP_DECL", "msg": str(e)})

    # ================= RESOLUTION PASS =================
    
    def check_statements(statements, scope):
        """Recursive function to check statements inside blocks"""
        for stmt in statements:
            t = stmt.get("type")
            
            if t == "Assign":
                target = stmt.get("target")
                if target and target.get("type") == "Identifier":
                    # Check if variable exists
                    sym = scope.resolve(target.get("name"))
                    if not sym:
                        errors.append({"code": "E_UNDEFINED", "msg": f"Undefined variable: {target.get('name')}"})
                    
                    # Check 'sym.category' for constant reassignment
                    elif sym.category == "const": 
                         errors.append({"code": "E_CONST_ASSIGN", "msg": f"Cannot reassign constant: {target.get('name')}"})
                
                resolve_expr(stmt.get("value"), scope)
            
            elif t == "ActionStmt":
                # Actions in our language don't have args, but good to keep structure
                pass 
            
            elif t == "IfStmt":
                resolve_expr(stmt.get("test"), scope)
                # Recurse into the 'consequent' block
                check_statements(stmt.get("consequent", []), scope)
                
                #Recurse into the 'alternate' (else) block
                if stmt.get("alternate"):
                    check_statements(stmt.get("alternate", []), scope)
            
            elif t == "WhileStmt":
                resolve_expr(stmt.get("test"), scope)
                #Recurse into the 'body' block
                check_statements(stmt.get("body", []), scope)

    def resolve_expr(expr, scope):
        if expr is None: return
        
        if expr.get("type") == "Identifier":
            name = expr.get("name")
            if not scope.resolve(name):
                errors.append({"code": "E_UNDEFINED", "msg": f"Undefined identifier: {name}"})
        
        elif expr.get("type") == "BinaryExpr":
            resolve_expr(expr.get("left"), scope)
            resolve_expr(expr.get("right"), scope)

    # Start checking from the main body
    check_statements(ast.get("body", []), global_scope)

    return errors
