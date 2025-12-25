# Basic symbol table and scope handling

class Symbol:
    def __init__(self, name, category, var_type, node=None, pos=None, level=0):
        self.name = name
        self.category = category  # "const" or "var"
        self.type = var_type      # "int", "bool", "direction"
        self.node = node
        self.pos = pos
        self.level = level

class Scope:
    def __init__(self, parent=None, level=0):
        self.parent = parent
        self.level = level
        self.names = {}

    def declare(self, name, category, var_type, node=None, pos=None):
        if name in self.names:
            raise KeyError(f"Duplicate declaration: {name}")
        # Store both category (const/var) and type (int/bool)
        self.names[name] = Symbol(name, category, var_type, node, pos, self.level)

    def resolve(self, name):
        s = self
        while s is not None:
            if name in s.names:
                return s.names[name]
            s = s.parent
        return None
