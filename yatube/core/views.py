from django.shortcuts import render


def page_not_found(request, exception):
    """Отображение страницы ошибки 404."""
    template = 'core/404.html'
    context = {
        'path': request.path,
    }

    return render(request, template, context, status=404)


def csrf_failure(request, reason=''):
    """Отображение страницы ошибки 403csrf."""
    template = 'core/403csrf.html'

    return render(request, template)


def permission_denied(request, exception):
    """Отображение страницы ошибки 403."""
    return render(request, 'core/403.html', status=403)


def server_error(request):
    """Отображение страницы ошибки 500."""
    return render(request, 'core/500.html', status=500)
