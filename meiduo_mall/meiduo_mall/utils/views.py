from django.http import JsonResponse


def my_decorator(func)

    def wrapper(request,*args,**kwargs):

        if request.user.is_authenticated:
            return func(request,*args,**kwargs)
        else:
            return JsonResponse({"code":400,"errmsg":"请登录后重试"})
    return wrapper


class LoginRequiredMixin(object):
