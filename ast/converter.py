import json
import sys

def convert_cst_to_ast(cst_node):
    """
    Traverses the CST and returns a simplified AST .
    """
    node_type = cst_node.get("type")
    
    # 1. Program Conversion
    if node_type == "PROGRAM":
        # CST: PROGRAM -> program ID { world declarations statements }
        # Children indices: 0:program, 1:ID, 2:{, 3:WORLD, 4:DECLS, 5:STMTS, 6:}
        
        # Safety check: ensure children exist
        if "children" not in cst_node:
            return None

        program_name = cst_node["children"][1]["value"]
        
        body = []
        
        # Extract Declarations (Index 4)
        if len(cst_node["children"]) > 4:
            decl_node = cst_node["children"][4]
            for child in decl_node.get("children", []):
                body.append(convert_declaration(child))
            
        # Extract Statements (Index 5)
        if len(cst_node["children"]) > 5:
            stmts_node = cst_node["children"][5]
            for child in stmts_node.get("children", []):
                body.append(convert_statement(child))
            
        return {
            "type": "Program",
            "name": program_name,
            "body": body
        }

    return None

def convert_declaration(decl_cst):
    # CST: CONST/VAR ID : TYPE ...
    first_token = decl_cst["children"][0]["value"] # 'const' or 'var'
    id_value = decl_cst["children"][1]["value"]
    
    # Extract the type (e.g., "int", "bool")
    type_node = decl_cst["children"][3] 
    var_type = type_node["children"][0]["value"]

    if first_token == "const":
        # CONST ID : TYPE = EXPR ;
        expr_node = decl_cst["children"][5]
        return {
            "type": "ConstDecl",
            "id": {"type": "Identifier", "name": id_value},
            "varType": var_type,
            "value": convert_expression(expr_node)
        }
    else:
        # VAR ID : TYPE <var_tail>
        var_tail = decl_cst["children"][4]
        init_value = None
        # Check var_tail children safely
        if var_tail.get("children") and len(var_tail["children"]) > 1:
            init_value = convert_expression(var_tail["children"][1])
            
        return {
            "type": "VarDecl",
            "id": {"type": "Identifier", "name": id_value},
            "varType": var_type,
            "init": init_value
        }

def convert_statement(stmt_cst):
    type_map = {
        "ASSIGNMENT": convert_assignment,
        "IF_STATEMENT": convert_if,
        "WHILE_STATEMENT": convert_while,
        "ACTION": convert_action,
        "BLOCK": convert_block
    }
    
    t = stmt_cst.get("type")
    if t in type_map:
        return type_map[t](stmt_cst)
        
    return None

def convert_assignment(node):
    target_name = node["children"][0]["value"]
    expr_node = node["children"][2]
    return {
        "type": "Assign",
        "target": {"type": "Identifier", "name": target_name},
        "value": convert_expression(expr_node)
    }

def convert_if(node):
    # IF ( COND ) BLOCK <else_part>
    cond_node = node["children"][2]
    block_node = node["children"][4]
    else_part = node["children"][5]
    
    alternate = None
    if else_part.get("children"): # Check if ELSE part exists
        alternate = convert_block(else_part["children"][1])
        
    return {
        "type": "IfStmt",
        "test": convert_condition(cond_node),
        "consequent": convert_block(block_node),
        "alternate": alternate
    }

def convert_while(node):
    cond_node = node["children"][2]
    block_node = node["children"][4]
    return {
        "type": "WhileStmt",
        "test": convert_condition(cond_node),
        "body": convert_block(block_node)
    }

def convert_action(node):
    action_name = node["children"][0]["value"] 
    return {
        "type": "ActionStmt",
        "action": action_name,
        "args": [] 
    }

def convert_block(node):
    # { STATEMENTS }
    if len(node.get("children", [])) > 1:
        stmts_node = node["children"][1]
        stmt_list = []
        for child in stmts_node.get("children", []):
            stmt_list.append(convert_statement(child))
        return stmt_list
    return []

def convert_expression(node):
    return flatten_expression(node)

def flatten_expression(node):
    # Base case: FACTOR
    if node["type"] == "FACTOR":
        child = node["children"][0]
        if child["type"] == "LITERAL":
            val = child["children"][0]["value"]
            if val.isdigit(): return {"type": "Literal", "value": int(val)}
            if val in ["true", "false"]: return {"type": "Literal", "value": val == "true"}
            return {"type": "Literal", "value": val} 
        elif child["type"] == "TERMINAL":
            # Check if it's a special terminal like "sense" or "not"
            if child["value"] in ["sense", "dirt"]:
                return {"type": "Identifier", "name": child["value"]}
            elif child["value"] == "not":
                # NOT operator
                return {
                    "type": "BinaryExpr",
                    "operator": "not",
                    "left": flatten_expression(node["children"][1]),
                    "right": None
                }
            else:
                # Regular identifier (ID)
                return {"type": "Identifier", "name": child["value"]}

    # Recursive Step: Parse Left side
    if "children" in node and len(node["children"]) > 0:
        left = flatten_expression(node["children"][0])
        
        # Check for Tail (Right side)
        if len(node["children"]) > 1:
            tail = node["children"][1]
            
            
            # We must use .get("children") because empty tails don't have the key
            if tail.get("children"): 
                op_node = tail["children"][0] # MUL_OP or ADD_OP
                op = op_node["children"][0]["value"]
                right = flatten_expression(tail["children"][1]) 
                return {
                    "type": "BinaryExpr",
                    "operator": op,
                    "left": left,
                    "right": right
                }
        return left
    return None

def convert_condition(node):
    left = flatten_expression(node["children"][0])
    tail = node["children"][1]
    
    # Check tail safely
    if tail.get("children"):
        op = tail["children"][0]["children"][0]["value"]
        right = flatten_expression(tail["children"][1])
        return {
            "type": "BinaryExpr",
            "operator": op,
            "left": left,
            "right": right
        }
    return left

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python converter.py <input_cst> <output_ast>")
        sys.exit(1)
        
    cst_file = sys.argv[1]
    ast_file = sys.argv[2]
    
    with open(cst_file, 'r') as f:
        cst = json.load(f)
        
    ast = convert_cst_to_ast(cst)
    
    with open(ast_file, 'w') as f:
        json.dump(ast, f, indent=2)
