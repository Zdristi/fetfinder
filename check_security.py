import os
import re

def check_xss_vulnerabilities():
    """Проверить HTML шаблоны на потенциальные XSS уязвимости"""
    xss_issues = []
    
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Проверить на потенциальные XSS уязвимости
                    # Примеры: использование {{ variable }} без экранирования в опасных контекстах
                    dangerous_patterns = [
                        r'{{\s*(\w+)\s*}}\s*[\r\n\s]*<[sS][cC][rR][iI][pP][tT]',  # переменная перед скриптом
                        r'value\s*=\s*["\']?\s*{{\s*(\w+)\s*}}',  # переменная в значении атрибута
                        r'href\s*=\s*["\']?\s*{{\s*(\w+)\s*}}',  # переменная в href
                        r'javascript:\s*{{\s*(\w+)\s*}}',  # javascript в переменной
                    ]
                    
                    for i, line_num in enumerate(content.splitlines(), 1):
                        for pattern in dangerous_patterns:
                            matches = re.finditer(pattern, line_num, re.IGNORECASE)
                            for match in matches:
                                xss_issues.append((file_path, i, line_num.strip(), f"Potential XSS: {match.group(0)}"))
    
    return xss_issues

def check_sql_injection():
    """Проверить на потенциальные SQL-инъекции"""
    sql_issues = []
    
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            # Проверить на неэкранированные строки в SQL запросах
                            if 'execute(' in line and ('+' in line or 'f"' in line or '.format' in line):
                                if 'text(' not in line:  # если не используется безопасный text()
                                    sql_issues.append((file_path, i, line.strip(), "Potential SQL injection"))
                except:
                    continue  # пропустить файлы с проблемами кодировки
    
    return sql_issues

def main():
    print("=== Проверка XSS уязвимостей в HTML шаблонах ===")
    xss_issues = check_xss_vulnerabilities()
    if xss_issues:
        for file_path, line_num, code, issue in xss_issues:
            print(f"XSS уязвимость в {file_path}:{line_num}: {issue}")
            print(f"  Код: {code}")
    else:
        print("XSS уязвимостей не найдено")
    
    print("\n=== Проверка SQL-инъекций в Python файлах ===")
    sql_issues = check_sql_injection()
    if sql_issues:
        for file_path, line_num, code, issue in sql_issues:
            print(f"SQL-инъекция в {file_path}:{line_num}: {issue}")
            print(f"  Код: {code}")
    else:
        print("SQL-инъекций не найдено")
    
    print("\n=== Проверка безопасности завершена ===")

if __name__ == '__main__':
    main()