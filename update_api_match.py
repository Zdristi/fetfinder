# Скрипт для обновления функции api_match в app.py
with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Найдем начало и конец функции api_match
start_marker = "@app.route('/api/match', methods=['POST'])\n@login_required\ndef api_match():"
end_marker = "    return jsonify(response)\n"

start_pos = content.find(start_marker)
if start_pos != -1:
    # Найдем конец функции - строку после return
    end_pos = content.find(end_marker, start_pos)
    if end_pos != -1:
        end_pos += len(end_marker)
        
        # Извлечем текущую функцию
        old_func = content[start_pos:end_pos]
        print(f"Найдена текущая функция длиной {len(old_func)} символов")
        
        # Новая функция
        new_func = """@app.route('/api/match', methods=['POST'])
@login_required
def api_match():
    from models import UserSwipe
    from datetime import datetime
    data = request.get_json()
    user2 = data.get('user2')
    action = data.get('action')  # 'like' or 'dislike'
    
    is_mutual_match = False
    
    # Record the swipe action (like or dislike)
    existing_swipe = UserSwipe.query.filter_by(
        swiper_id=int(current_user.id), 
        swipee_id=int(user2)
    ).first()
    
    if existing_swipe:
        # Update existing swipe if needed
        existing_swipe.action = action
        existing_swipe.timestamp = datetime.utcnow()
    else:
        # Create new swipe record
        swipe = UserSwipe(
            swiper_id=int(current_user.id),
            swipee_id=int(user2),
            action=action
        )
        db.session.add(swipe)
    
    if action == 'like':
        # Check if match already exists
        existing_match = Match.query.filter_by(
            user_id=int(current_user.id), 
            matched_user_id=int(user2)
        ).first()
        
        if not existing_match:
            match = Match(
                user_id=int(current_user.id),
                matched_user_id=int(user2)
            )
            db.session.add(match)
            
            # Check if this is a mutual match
            reverse_match = Match.query.filter_by(
                user_id=int(user2),
                matched_user_id=int(current_user.id)
            ).first()
            
            # Return True if it's a mutual match
            is_mutual_match = reverse_match is not None
    
    # Commit all changes
    db.session.commit()

    response = {'status': 'success'}
    
    # If it's a mutual match, add notification
    if is_mutual_match:
        response['mutual_match'] = True
        response['matched_user_id'] = user2
        # Get matched user info
        matched_user = UserModel.query.get(int(user2))
        if matched_user:
            response['matched_user_name'] = matched_user.username
            response['matched_user_photo'] = matched_user.photo
    
    return jsonify(response)"""
        
        # Заменим функцию
        new_content = content[:start_pos] + new_func + content[end_pos:]
        
        # Запишем обратно в файл
        with open('C:\\Users\\Andrey\\Desktop\\QwenSite\\app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("Функция api_match успешно обновлена!")
    else:
        print("Не найден конец функции")
else:
    print("Не найдено начало функции")