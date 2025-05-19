import difflib
import openai
from .models import FAQ, Comment, User
from django.conf import settings


def generate_ai_response(ticket):
    # Only respond to open tickets
    if ticket.status != 'open':
        return

    ai_user = get_or_create_ai_user()

    # First check FAQs
    faq_match = find_similar_faq(ticket.description)
    if faq_match:
        Comment.objects.create(
            ticket=ticket,
            user=ai_user,
            text=f"🔍 I found a related FAQ:\n\n**{faq_match.question}**\n{faq_match.answer}",
            is_ai=True
        )
        return

    # Generate custom AI response
    try:
        client = openai.OpenAI(
            base_url=settings.LEPTON_BASE_URL,
            api_key=settings.LEPTON_API_KEY
        )

        response = client.chat.completions.create(
            model="openchat_3.5",
            messages=[{
                "role": "system",
                "content": "You're a helpful support assistant. Respond to this new ticket."
            }, {
                "role": "user",
                "content": f"Ticket Title: {ticket.title}\n\nDescription: {ticket.description}"
            }],
            max_tokens=500
        )

        Comment.objects.create(
            ticket=ticket,
            user=ai_user,
            text=response.choices[0].message.content,
            is_ai=True
        )

    except Exception:
        # Fallback if AI fails
        Comment.objects.create(
            ticket=ticket,
            user=ai_user,
            text="⚠️ Our AI is currently unavailable. A human agent will respond shortly.",
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
