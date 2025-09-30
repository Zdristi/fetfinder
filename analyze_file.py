import re

# Читаем файл
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем блок Extended Profile
pattern = r'(<!-- Extended Profile Fields -->\s*<div style=\\\\"[^>]*>.*?<!-- Additional Photos Section -->)'
match = re.search(pattern, content, re.DOTALL)

if match:
    print("Найден блок Extended Profile:")
    print(match.group(0)[:300] + "...")  # Показываем начало блока
else:
    print("Блок Extended Profile не найден")

# Выводим начало блока Extended Profile
extended_profile_start = content.find('<!-- Extended Profile Fields -->')
if extended_profile_start != -1:
    print(f"\nБлок начинается с позиции {extended_profile_start}")
    print("Контекст:")
    print(repr(content[extended_profile_start:extended_profile_start+150]))