import json

class CSTNode:
    def __init__(self, node_type, value=None):
        """
        node_type: String (e.g., "PROGRAM", "VAR_DECL", "IF")
        value: String or None (e.g., "dirtCount", "5", or None for internal nodes)
        """
        self.node_type = node_type
        self.value = value
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def to_dict(self):
        """
        Recursive function to convert tree to dictionary for JSON export.
        """
        node_dict = {"type": self.node_type}
        if self.value is not None:
            node_dict["value"] = self.value
        
        # Only add children key if there are children to keep output clean
        if self.children:
            node_dict["children"] = [child.to_dict() for child in self.children]
            
        return node_dict

    def __repr__(self):
        # Helper for printing nodes during debugging
        if self.value:
            return f"<{self.node_type}: {self.value}>"
        return f"<{self.node_type}>"
