# Простой скрипт для замены HTML разметки в файле
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Сохраним оригинальные позиции для отладки
extended_start_pos = content.find('<!-- Extended Profile Fields -->')
div_start_pos = content.find('<div style=\\\\\\"margin: 30px 0; padding: 20px; border: 2px solid var(--accent); border-radius: 15px; background: var(--card-bg);\\\\">', extended_start_pos)
h3_start_pos = content.find('<h3 style=\\\\\\"color: var(--accent); margin-top: 0;\\\\">', div_start_pos)

print(f'Extended profile start: {extended_start_pos}')
print(f'Div start: {div_start_pos}')
print(f'H3 start: {h3_start_pos}')

if div_start_pos != -1:
    # Найдем конец блока Extended Profile (перед началом Additional Photos Section)
    additional_photos_pos = content.find('<!-- Additional Photos Section -->', div_start_pos)
    
    if additional_photos_pos != -1:
        # Найдем позицию закрывающего div
        # Считаем количество открывающих и закрывающих тегов div
        content_to_search = content[div_start_pos:additional_photos_pos]
        
        open_divs = 0
        pos = 0
        closing_div_pos = -1
        
        while pos < len(content_to_search):
            open_pos = content_to_search.find('<div', pos)
            close_pos = content_to_search.find('</div>', pos)
            
            if open_pos != -1 and (open_pos < close_pos or close_pos == -1):
                open_divs += 1
                pos = open_pos + 4
            elif close_pos != -1 and (close_pos < open_pos or open_pos == -1):
                open_divs -= 1
                if open_divs == 0:
                    closing_div_pos = close_pos
                    break
                pos = close_pos + 6
            else:
                break
        
        if closing_div_pos != -1:
            # Рассчитываем абсолютную позицию закрывающего тега
            absolute_closing_pos = div_start_pos + closing_div_pos
            
            # Выделяем блок для замены
            old_block = content[div_start_pos:absolute_closing_pos+6]  # +6 для </div>
            
            print(f'Длина старого блока: {len(old_block)}')
            print(f'Старый блок: {repr(old_block[:200])}...')
            
            # Создаем новый блок с классами
            new_block = '''<div class="extended-profile-section">
            <h3 class="section-title-text">
                <i class="fas fa-user-circle"></i> {{ get_text('extended_profile') or 'Extended Profile' }}
            </h3>
            
            <div class="profile-fields-grid">
'''
            # Добавим содержимое между старыми тегами div
            inner_content_start = content_to_search.find('>', content_to_search.find('<h3'))
            inner_content_end = closing_div_pos - 7  # Отнимаем 7 для "</div>"
            
            inner_content = content_to_search[inner_content_start+1:inner_content_end-6].strip()  # Убираем лишние отступы
            
            # Заменяем только стиль у внутреннего div
            import re
            inner_content = re.sub(r'<div style=\\\\\\"display: grid; grid-template-columns: repeat\(auto-fit, minmax\(300px, 1fr\)\); gap: 20px;\\\\\\"', '<div class="profile-fields-grid"', inner_content)
            
            new_block += inner_content + '            </div>\n        </div>'
            
            print(f'Новый блок: {repr(new_block[:200])}...')
            
            # Выполняем замену
            new_content = content[:div_start_pos] + new_block + content[absolute_closing_pos+6:]
            
            # Сохраняем изменения
            with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print('Замена выполнена успешно!')
        else:
            print('Не найден закрывающий тег div')
    else:
        print('Не найден раздел Additional Photos Section')
else:
    print('Не найден div элемент Extended Profile')