import ast

filename = 'addons-custom/ak_ai/services/openrouter_service.py'

with open(filename, 'r') as f:
    source = f.read()

tree = ast.parse(source)

class NameVisitor(ast.NodeVisitor):
    def visit_Name(self, node):
        if node.id == 'name' and isinstance(node.ctx, ast.Load):
            print(f"Found usage of 'name' at line {node.lineno}")
        self.generic_visit(node)

NameVisitor().visit(tree)
