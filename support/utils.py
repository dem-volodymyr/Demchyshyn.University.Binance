import difflib
import openai
import requests
from .models import FAQ, Comment, User
from django.conf import settings

# Константи для Gemini API
API_URL = getattr(settings, 'OPEN_API')
headers = {
    "Content-Type": "application/json"
}
context = (
    "Xchange — це сучасна криптобіржа, яка дозволяє швидко, зручно та безпечно торгувати різними криптовалютами. "
    "Основні модулі та функції біржі Xchange:\n"
    "- Торгівля криптовалютами: підтримка багатьох валют, швидкі та безпечні операції, інноваційні торгові інструменти.\n"
    "- Гаманець: зберігання, поповнення, виведення криптовалют, перегляд балансу, історія транзакцій.\n"
    "- Ордера: створення, перегляд, управління ордерами на купівлю/продаж.\n"
    "- Реєстрація та профіль: реєстрація, вхід, редагування профілю, двофакторна аутентифікація.\n"
    "- Реферальна система: запрошення друзів, отримання бонусів.\n"
    "- Підтримка: система тікетів, FAQ, AI-помічник, email-підтримка.\n"
    "- Аналітика та трекінг: перегляд ринкових даних, аналітика, графіки.\n"
    "- Безпека: двофакторна аутентифікація, email-підтвердження, захист акаунта.\n"
    "- Локалізація: підтримка різних мов (основна — українська/англійська).\n\n"
    "Платформа підтримує великий вибір цифрових активів, надає інноваційні торгові інструменти, а також зручний гаманець для зберігання, поповнення та виведення криптовалюти. "
    "Користувачі можуть створювати ордери на купівлю та продаж, переглядати історію транзакцій, користуватися реферальною програмою, а також отримувати аналітику та ринкові дані. "
    "Для безпеки доступна двофакторна аутентифікація, email-підтвердження та сучасні засоби захисту акаунта. "
    "Платформа підходить як для новачків, так і для досвідчених трейдерів. "
    "Підтримка користувачів здійснюється через систему тікетів, FAQ, AI-помічника та email. "
    "Відповідай коротко, простою і дружньою мовою, без зайвих формальностей, не повторюй питання користувача, не використовуй розмітку Markdown (##, **, *, тощо), не додавай заголовків і не підписуйся як команда підтримки. "
    "Якщо користувач просто дякує або пише щось на кшталт «дякую», «ок», «все зрозуміло», відповідай коротко: «Будь ласка!» або «Раді допомогти!» і не давай інструкцій чи пояснень. "
    "Якщо питання стосується функцій біржі, давай чітку, покрокову відповідь, але не більше 3-5 речень. "
    "Якщо не знаєш точної відповіді — порадь звернутися до служби підтримки Xchange.\n\n"
)

def generate_ai_response(ticket, comment=None):
    # Only respond to open tickets
    if ticket.status != 'open':
        return

    ai_user = get_or_create_ai_user()

    # Визначаємо текст для аналізу (FAQ/AI): коментар або description тікету
    text_for_faq = comment.text if comment else ticket.description

    # First check FAQs
    faq_match = find_similar_faq(text_for_faq)
    if faq_match:
        Comment.objects.create(
            ticket=ticket,
            user=ai_user,
            text=f"🔍 I found a related FAQ:\n\n{faq_match.question}\n{faq_match.answer}",
            is_ai=True
        )
        return
    try:
        prompt_text = context + f"Ticket Title: {ticket.title}\n\nDescription: {text_for_faq}"
        print(prompt_text)
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt_text
                        }
                    ]
                }
            ]
        }
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            resp_json = response.json()
            try:
                text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                text = f"Не вдалося витягти текст відповіді."
        else:
            text = f"Помилка {response.status_code}: {response.text}"
        Comment.objects.create(
            ticket=ticket,
            user=ai_user,
            text=text,
            is_ai=True
        )
    except Exception as e:
        # Fallback if AI fails
        Comment.objects.create(
            ticket=ticket,
            user=ai_user,
            text=f"⚠️ Наш AI наразі недоступний. Людський агент відповість незабаром. ({e})",
            is_ai=True
        )


def get_or_create_ai_user():
    ai_user, created = User.objects.get_or_create(
        username='AI_Helper',
        defaults={
            'email': 'ai@example.com',
            'password': 'unusablepassword'
        }
    )
    if created:
        ai_user.set_unusable_password()
        ai_user.save()
    return ai_user


def find_similar_faq(text):
    faqs = FAQ.objects.all()
    best_match = None
    best_ratio = 0
    for faq in faqs:
        ratio = difflib.SequenceMatcher(None, text.lower(), faq.question.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = faq
    return best_match if best_ratio > 0.6 else None
