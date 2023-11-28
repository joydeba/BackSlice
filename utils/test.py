import ast

# def find_source_code_entity(source_code_toTest, test_case_line):

#     parsed_source_code_tree = ast.parse(source_code_toTest)

#     class EntityVisitor(ast.NodeVisitor):
#         def __init__(self, test_case_line):
#             self.test_case_line = test_case_line
#             self.found_entity = None

#         def visit_FunctionDef(self, node):
#             if self._matches_test_case(node.name):
#                 self.found_entity = node.name

#         def visit_ClassDef(self, node):
#             if self._matches_test_case(node.name):
#                 self.found_entity = node.name

#         def _matches_test_case(self, entity_name):
#             if entity_name:
#                 if entity_name in self.test_case_line:
#                     return True
#                 else:
#                     return False
#             else:
#                 return False    

#     visitor = EntityVisitor(test_case_line)
#     visitor.visit(parsed_source_code_tree)

#     return visitor.found_entity

# source_code = 'from ansible.utils.unsafe_proxy import AnsibleUnsafeText, AnsibleUnsafeBytes\n'
# target_line = 'from ansible.module_utils.six import PY2'
# result = find_source_code_entity(source_code, target_line)
# print(result)

