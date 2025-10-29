import ast
import os
import sys

def check_syntax_errors():
    """Проверить синтаксические ошибки в Python файлах"""
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    
    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                ast.parse(content)
        except SyntaxError as e:
            syntax_errors.append((file_path, str(e)))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return syntax_errors

def check_common_issues():
    """Проверить код на распространенные проблемы"""
    issues = []
    
    # Проверить, используются ли потенциально небезопасные функции
    dangerous_patterns = [
        'eval(', 'exec(', 'os.system(', 'subprocess.call(', 'subprocess.run(',
        'open('  # potentially unsafe file operations
    ]
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                for pattern in dangerous_patterns:
                    if pattern in line and not line.strip().startswith('#'):
                        issues.append((file_path, i, line.strip(), f"Potentially unsafe pattern: {pattern}"))
    
    return issues

def main():
    print("=== Проверка синтаксических ошибок ===")
    syntax_errors = check_syntax_errors()
    if syntax_errors:
        for file_path, error in syntax_errors:
            print(f"Синтаксическая ошибка в {file_path}: {error}")
    else:
        print("Синтаксических ошибок не найдено")
    
    print("\n=== Проверка потенциально небезопасных паттернов ===")
    common_issues = check_common_issues()
    if common_issues:
        for file_path, line_num, code, issue in common_issues:
            print(f"Потенциальная проблема в {file_path}:{line_num}: {issue}")
            print(f"  Код: {code}")
    else:
        print("Потенциально небезопасных паттернов не найдено")
    
    print("\n=== Проверка завершена ===")

if __name__ == '__main__':
    main()