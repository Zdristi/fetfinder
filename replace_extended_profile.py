import re

# Читаем файл
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("До замены:")
print("Пример строки с Extended Profile:")
extended_profile_match = re.search(r'(<div style=\\\\\"margin: 30px 0; padding: 20px; border: 2px solid var\(--accent\)[^>]*>.*?</div>)', content, re.DOTALL)
if extended_profile_match:
    print(extended_profile_match.group(0)[:100] + "...")

# Определяем начало и конец блока Extended Profile
start_pattern = r'<!-- Extended Profile Fields -->\s*<div style=\\\\\"margin: 30px 0; padding: 20px; border: 2px solid var\(--accent\); border-radius: 15px; background: var\(--card-bg\);\\\"[^>]*>'
end_pattern = r'</div>\s*\n*\s*<!-- Additional Photos Section -->'

# Находим полный блок
full_pattern = r'(<!-- Extended Profile Fields -->\s*)(<div style=\\\\\"[^>]*>.*?</div>)(\s*\n*\s*)(<!-- Additional Photos Section -->)'
match = re.search(full_pattern, content, re.DOTALL)

if match:
    full_match = match.group(0)
    print(f"\nПолный блок найден: {len(full_match)} символов")
    
    # Заменяем только начальную часть до закрывающего тега div
    # Находим первый закрывающий div после начала блока
    start_pos = match.start(2)  # Начало второго захваченного блока (div с инлайновыми стилями)
    div_content = match.group(2)
    
    # Находим парные теги div
    content_to_modify = content
    extended_start = content.find('<!-- Extended Profile Fields -->')
    extended_end = content.find('<!-- Additional Photos Section -->', extended_start)
    
    if extended_start != -1 and extended_end != -1:
        main_block = content[extended_start:extended_end]
        
        # Заменяем только начальный div с инлайновыми стилями и закрывающий div
        old_block = content[extended_start:extended_end]
        
        # Ищем полный div контейнер
        container_pattern = r'(<div style=\\\\\"margin: 30px 0; padding: 20px; border: 2px solid var\(--accent\); border-radius: 15px; background: var\(--card-bg\);\\\"[^>]*>.*?</div>)'
        
        # Нужно более точно определить границы
        div_start = content.find('<div style=\\\\\"margin: 30px 0; padding: 20px;', extended_start)
        if div_start != -1:
            # Найдем соответствующий закрывающий тег div
            open_divs = 0
            pos = div_start
            while pos < extended_end:
                open_tag = content.find('<div', pos)
                close_tag = content.find('</div>', pos)
                
                if open_tag != -1 and (open_tag < close_tag or close_tag == -1):
                    open_divs += 1
                    pos = open_tag + 4
                elif close_tag != -1 and (close_tag < open_tag or open_tag == -1):
                    open_divs -= 1
                    if open_divs == 0:
                        full_div_end = close_tag + 6
                        break
                    pos = close_tag + 5
                else:
                    break
            
            if 'full_div_end' in locals():
                old_div_block = content[div_start:full_div_end]
                
                # Заменяем на новый блок с классами
                new_div_block = '<div class="extended-profile-section">\n            <h3 class="section-title-text">\n                <i class="fas fa-user-circle"></i> {{ get_text(\'extended_profile\') or \'Extended Profile\' }}\n            </h3>\n            \n            <div class="profile-fields-grid">\n                <!-- Поле начинаются здесь -->\n' + content[content.find('                <div class=', div_start):content.find('            </div>', div_start)] + '\n            </div>'
                
                # Добавим правильный закрывающий тег
                new_div_block = new_div_block + '\n        </div>'
                
                print("Старый блок:")
                print(repr(old_div_block[:200]))
                print("Новый блок:")
                print(repr(new_div_block[:200]))
                
                # Выполним замену
                updated_content = content[:div_start] + new_div_block + content[full_div_end:]
                
                # Сохраняем изменения
                with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print("Замена выполнена успешно!")