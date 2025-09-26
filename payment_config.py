import hashlib
import hmac
import requests
from flask import request, url_for, current_app
from urllib.parse import urlencode

class InterKassaConfig:
    def __init__(self):
        # Настройки InterKassa - получите их из вашей панели управления InterKassa
        self.ik_shop_id = current_app.config.get('INTERKASSA_SHOP_ID', 'your_shop_id_here')
        self.ik_secret_key = current_app.config.get('INTERKASSA_SECRET_KEY', 'your_secret_key_here')
        self.ik_test_key = current_app.config.get('INTERKASSA_TEST_KEY', 'your_test_key_here')
        self.is_test_mode = current_app.config.get('INTERKASSA_TEST_MODE', True)
        self.gateway_url = 'https://pay.interkassa.com/'
        
    def create_payment_form(self, order_id, amount, description, user_email=None, user_id=None):
        """Создать форму для оплаты через InterKassa"""
        
        # Подготавливаем данные для формы
        form_data = {
            'ik_shop_id': self.ik_shop_id,
            'ik_payment_amount': f'{amount:.2f}',
            'ik_payment_currency': 'USD',  # или 'EUR', 'UAH' и т.д.
            'ik_payment_desc': description,
            'ik_paysys': '',
            'ik_baggage_fields': '',
            'ik_success_url': url_for('premium_success', _external=True),
            'ik_success_method': 'POST',
            'ik_fail_url': url_for('premium', _external=True),
            'ik_fail_method': 'POST',
            'ik_status_url': url_for('interkassa_webhook', _external=True),
            'ik_status_method': 'POST',
            'ik_pm_no': '',
            'ik_co_id': '',
            'ik_inv_id': order_id  # Идентификатор заказа
        }
        
        # Добавляем пользовательские поля при необходимости
        if user_id:
            form_data['user_id'] = user_id
        if user_email:
            form_data['user_email'] = user_email
            
        # Создаем подпись (ик-сиг)
        signature_data = [
            self.ik_shop_id,
            order_id,
            f'{amount:.2f}',
            self.ik_secret_key  # Ключ для подписи
        ]
        
        # Создаем подпись из данных
        sign_string = ':'.join(str(val) for val in signature_data)
        sign_hmac = hmac.new(
            self.ik_secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        form_data['ik_sign'] = sign_hmac
        
        return form_data
    
    def verify_payment(self, form_data):
        """Проверить подлинность платежа от InterKassa"""
        received_sign = form_data.get('ik_sign')
        if not received_sign:
            return False
            
        # Удаляем подпись из данных для проверки
        form_data_copy = dict(form_data)
        form_data_copy.pop('ik_sign', None)
        
        # Создаем строку подписи
        sorted_keys = sorted(form_data_copy.keys())
        sign_string_parts = [form_data_copy[key] for key in sorted_keys if form_data_copy[key]]
        sign_string_parts.append(self.ik_secret_key)
        sign_string = ':'.join(sign_string_parts)
        
        # Вычисляем контрольную подпись
        calculated_sign = hmac.new(
            self.ik_secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем подписи
        return hmac.compare_digest(calculated_sign, received_sign)