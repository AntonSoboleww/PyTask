import ast

def check_code(user_code, allowed_libraries=None, disabled_functions=None):
    if allowed_libraries is None:
        allowed_libraries = []
    if disabled_functions is None:
        allowed_libraries = []

    tree = ast.parse(user_code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            for name in node.names:
                if name.name not in allowed_libraries:
                    raise ValueError(f"Импорт библиотеки {name.name} запрещен")    
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
                if function_name in disabled_functions:
                    raise ValueError(f"Вызов функции {function_name} запрещен")

# Функция-фильтр zip для использования в шаблоне
def zip_lists(list1, list2):
    return zip(list1, list2)