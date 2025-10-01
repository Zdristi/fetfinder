# Скрипт для добавления недостающих переводов в русский словарь
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Найдем конец русского словаря (до закрывающей скобки)
ru_start = content.find("'ru': {")
if ru_start != -1:
    # Найдем позицию закрывающей скобки для русского словаря
    # Посчитаем скобки, чтобы точно определить границы
    pos = content.find("},", ru_start)
    
    # Найдем конец русского словаря более точно
    bracket_count = 1
    search_pos = content.find('{', ru_start) + 1
    
    while bracket_count > 0 and search_pos < len(content):
        open_bracket = content.find('{', search_pos)
        close_bracket = content.find('}', search_pos)
        
        if open_bracket != -1 and (open_bracket < close_bracket or close_bracket == -1):
            bracket_count += 1
            search_pos = open_bracket + 1
        elif close_bracket != -1:
            bracket_count -= 1
            if bracket_count == 0:
                ru_end = close_bracket
                break
            search_pos = close_bracket + 1
        else:
            break
    
    if 'ru_end' in locals():
        # Проверим, есть ли уже какие-то из ключей
        ru_dict_content = content[ru_start:ru_end]
        
        # Добавим недостающие ключи
        missing_translations = {
            'extended_profile': 'Расширенный профиль',
            'about_me_video': 'Видео о себе',
            'relationship_goals': 'Цели отношений',
            'long_term_relationship': 'Долгосрочные отношения',
            'short_term_fun': 'Краткосрочное веселье',
            'marriage': 'Брак',
            'friends': 'Дружба',
            'open_relationship': 'Открытые отношения',
            'lifestyle': 'Образ жизни',
            'active': 'Активный',
            'sedentary': 'Малоподвижный',
            'moderate': 'Умеренный',
            'very_active': 'Очень активный',
            'diet': 'Диета',
            'vegetarian': 'Вегетарианец',
            'vegan': 'Веган',
            'omnivore': 'Всеядный',
            'pescatarian': 'Пескатарианец',
            'keto': 'Кето-диета',
            'paleo': 'Палео-диета',
            'smoking': 'Курение',
            'never': 'Никогда',
            'occasionally': 'Иногда',
            'socially': 'Социально',
            'regularly': 'Регулярно',
            'drinking': 'Употребление алкоголя',
            'occupation': 'Род занятий',
            'education': 'Образование',
            'children': 'Дети',
            'none': 'Нет',
            'yes': 'Да',
            'want_someday': 'Хочу когда-нибудь',
            'dont_want': 'Не хочу',
            'pets': 'Домашние животные',
            'comma_separated': 'через запятую'
        }
        
        # Проверим, какие ключи уже существуют
        existing_keys = []
        for key in missing_translations.keys():
            if f"'{key}':" in ru_dict_content or f'"{key}":' in ru_dict_content:
                existing_keys.append(key)
        
        # Удалим существующие ключи из добавляемых
        for key in existing_keys:
            del missing_translations[key]
        
        if missing_translations:
            # Подготовим строки для добавления
            new_entries = []
            for key, value in missing_translations.items():
                new_entries.append(f"        '{key}': '{value}',")
            
            # Вставим новые переводы перед закрывающей скобкой
            # Найдем последнюю строку перед }
            insertion_point = content.rfind('\n', ru_start, ru_end)
            insertion_point = content.rfind('\n', ru_start, insertion_point)  # Предпоследняя строка
            
            # Добавим отступ для новых записей
            new_content = '\n' + ',\n'.join(new_entries)
            
            # Вставим новые переводы
            updated_content = content[:insertion_point] + new_content + content[insertion_point:]
            
            # Запишем обновленный файл
            with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\app.py', 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"Добавлено {len(new_entries)} новых переводов в русский словарь")
            print("Новые переводы:", list(missing_translations.items()))
        else:
            print("Все необходимые переводы уже существуют")
    else:
        print("Не удалось найти конец русского словаря")
else:
    print("Не найден русский словарь")