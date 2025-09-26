import stripe
from flask import current_app

# Настройки Stripe
class StripeConfig:
    def __init__(self):
        # Получите эти ключи из вашей панели управления Stripe
        self.secret_key = current_app.config.get('STRIPE_SECRET_KEY', 'sk_test_...')
        self.publishable_key = current_app.config.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')
        self.premium_price_id = current_app.config.get('STRIPE_PREMIUM_PRICE_ID', 'price_...')
        
        stripe.api_key = self.secret_key

    def create_checkout_session(self, user_email, success_url, cancel_url):
        """Создать сессию оплаты через Stripe"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': self.premium_price_id,  # ID вашего ценника для премиума
                    'quantity': 1,
                }],
                mode='subscription',  # Используем подписку
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                metadata={
                    'user_id': current_app.current_user.id if hasattr(current_app, 'current_user') else None
                }
            )
            return session
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None

    def verify_webhook(self, payload, sig_header, endpoint_secret):
        """Проверить webhook от Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            return event
        except Exception as e:
            print(f"Error verifying webhook: {e}")
            return None