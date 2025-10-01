from app import app, db, UserModel
from models import UserSwipe
from flask_login import current_user

@app.route('/debug-users')
def debug_users():
    with app.app_context():
        # Получаем текущего пользователя (в тестовом режиме будет использоваться первый)
        # Для отладки получим всех пользователей
        all_users = UserModel.query.all()
        result = f"Total users in system: {len(all_users)}\n"
        result += "User list:\n"
        
        for user in all_users:
            result += f"  ID: {user.id}, Username: {user.username}, Blocked: {user.is_blocked}\n"
        
        # Проверим для конкретного пользователя (например, первого), сколько он отсвайпал
        if all_users:
            test_user = all_users[0]  # Используем первого пользователя для теста
            swipes_by_user = UserSwipe.query.filter_by(swiper_id=test_user.id).count()
            swipes_on_user = UserSwipe.query.filter_by(swipee_id=test_user.id).count()
            
            result += f"\nDebug info for user {test_user.username} (ID: {test_user.id}):\n"
            result += f"  Swipes made by user: {swipes_by_user}\n"
            result += f"  Swipes received by user: {swipes_on_user}\n"
            
            # Покажем, кого конкретно отсвайпал этот пользователь
            swiped_users = UserSwipe.query.filter_by(swiper_id=test_user.id).all()
            result += f"  Users swiped by this user: {[sw.swipee_id for sw in swiped_users]}\n"
        
        return "<pre>" + result + "</pre>"

if __name__ == '__main__':
    app.run(debug=True)