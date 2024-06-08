from django.http import HttpResponse
from django.shortcuts import redirect

def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home_page')
        return view_func(request, *args, **kwargs)
    return wrapper_func

def allowed_users(allowed_users=[]):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            groups = request.user.groups.values_list('name', flat=True)
            if any(group in allowed_users for group in groups):
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse('You are not authenticated to view this page')
        return wrapper
    return decorator