from django.utils import translation

def language_processor(request):
    lang = request.session.get('site_lang') or request.session.get('django_language') or translation.get_language() or 'fr'
    is_en = (lang == 'en')
    return {
        'site_lang': lang,
        'is_en': is_en,
    }
