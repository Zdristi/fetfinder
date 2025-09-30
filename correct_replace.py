# Исправленный скрипт для точной замены
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Найдем начало блока Extended Profile
start_pos = content.find('<!-- Extended Profile Fields -->')
if start_pos != -1:
    # Найдем начало div после комментария
    div_start = content.find('<div', start_pos)
    if div_start != -1:
        # Подсчитаем количество открывающих и закрывающих тегов div
        open_divs = 0
        pos = div_start
        end_pos = -1
        
        while pos < len(content):
            open_tag = content.find('<div', pos)
            close_tag = content.find('</div>', pos)
            
            if open_tag != -1 and (open_tag < close_tag or close_tag == -1):
                open_divs += 1
                # Проверим, является ли это внутренним div с grid-ом
                grid_check = content[open_tag:open_tag+100]
                if 'grid-template-columns' in grid_check:
                    # Это внутренний div, запомним его конец, чтобы не включать в замену
                    pass
                pos = open_tag + 4
            elif close_tag != -1 and (close_tag < open_tag or open_tag == -1):
                open_divs -= 1
                if open_divs == 0:
                    end_pos = close_tag + 6
                    break
                pos = close_tag + 6
            else:
                break
        
        if end_pos != -1:
            original_block = content[div_start:end_pos]
            print("Оригинальный блок:")
            print(repr(original_block[:200]))
            
            # Теперь найдем правильное содержимое между внешним div и его закрывающим тегом
            # Пропустим начальные теги до внутреннего div с gridом
            h3_end = content.find('>', content.find('<h3', div_start)) + 1
            grid_div_start = content.find('<div', h3_end)
            
            # Пропустим grid div и найдем следующий контент
            grid_div_end = content.find('>', grid_div_start) + 1
            
            # Найдем закрывающий тег для grid div
            inner_open_divs = 0
            inner_pos = grid_div_start
            
            while inner_pos < end_pos:
                inner_open = content.find('<div', inner_pos)
                inner_close = content.find('</div>', inner_pos)
                
                if inner_open != -1 and inner_open < inner_close:
                    inner_open_divs += 1
                    inner_pos = inner_open + 4
                elif inner_close != -1:
                    inner_open_divs -= 1
                    if inner_open_divs == 0:
                        inner_content = content[grid_div_end:inner_close]  # Без закрывающего </div>
                        break
                    inner_pos = inner_close + 6
                else:
                    break
            
            if 'inner_content' in locals():
                # Создаем новую разметку
                new_block = f'''<div class="extended-profile-section">
            <h3 class="section-title-text">
                <i class="fas fa-user-circle"></i> {{ get_text('extended_profile') or 'Extended Profile' }}
            </h3>
            
            <div class="profile-fields-grid">
{inner_content}
            </div>
        </div>'''
                
                # Выполняем замену
                new_content = content[:div_start] + new_block + content[end_pos:]
                
                print("Новый блок:")
                print(repr(new_block[:200]))
                
                # Сохраняем изменения
                with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("Замена выполнена успешно!")
            else:
                print("Не удалось извлечь внутреннее содержимое")
        else:
            print("Не найден конец блока")
    else:
        print("Не найден div после комментария")
else:
    print("Не найден комментарий Extended Profile Fields")