from datetime import datetime


def year(request):
    """Возращает текущий год."""
    return {
        'year': datetime.now().year,
    }
