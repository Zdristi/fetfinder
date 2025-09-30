# Скрипт для точной замены с учетом реального содержимого файла
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Проверим, как в файле представлены кавычки в действительности
extended_start = content.find('<!-- Extended Profile Fields -->')
if extended_start != -1:
    # Найдем следующий div после комментария
    div_start = content.find('<div', extended_start)
    if div_start != -1:
        # Найдем полный div до первого закрывающего </div>
        open_divs = 0
        pos = div_start
        
        while pos < len(content):
            open_tag = content.find('<div', pos)
            close_tag = content.find('</div>', pos)
            
            if open_tag != -1 and (open_tag < close_tag or close_tag == -1):
                open_divs += 1
                pos = open_tag + 4
            elif close_tag != -1 and (close_tag < open_tag or open_tag == -1):
                open_divs -= 1
                if open_divs == 0:
                    # Это закрывающий div для нашего блока
                    full_block_end = close_tag + 6
                    break
                pos = close_tag + 6
            else:
                break
        
        if 'full_block_end' in locals():
            old_block = content[div_start:full_block_end]
            print(f"Найден старый блок длиной {len(old_block)} символов")
            print(f"Начало старого блока: {repr(old_block[:100])}")
            
            # Найдем конец блока Extended Profile до закрывающего div
            h3_start = content.find('<h3', div_start)
            if h3_start != -1 and h3_start < full_block_end:
                inner_content_start = content.find('>', h3_start) + 1
                inner_content_end = full_block_end - 6  # Без последнего </div>
                
                inner_content = content[inner_content_start:inner_content_end]
                
                # Создаем новый блок
                new_block = f'''<div class="extended-profile-section">
            <h3 class="section-title-text">
                <i class="fas fa-user-circle"></i> {{ get_text('extended_profile') or 'Extended Profile' }}
            </h3>
            
            <div class="profile-fields-grid">
{inner_content.strip()}
            </div>
        </div>'''
                
                print(f"Новый блок: {repr(new_block[:100])}")
                
                # Выполняем замену
                new_content = content[:div_start] + new_block + content[full_block_end:]
                
                # Сохраняем изменения
                with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\templates\\edit_profile.html', 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("Замена выполнена успешно!")
            else:
                print("Не найден тег h3 внутри блока")
        else:
            print("Не найден конец блока")
    else:
        print("Не найден div после комментария")
else:
    print("Не найден комментарий Extended Profile Fields")