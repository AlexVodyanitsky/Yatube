from django.shortcuts import render


def page_not_found(request, exception):
    """Return 404 page"""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, reason=''):
    """Return 403 page"""
    return render(request, 'core/403csrf.html')

def internal_server_error(request):
    """Return 500 page"""
    return render(request, 'core/500.html')