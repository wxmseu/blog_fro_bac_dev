from django.http import JsonResponse
from django.conf import settings
import jwt
from blog.models import UserProfile


def login_check(func):
    def wrap(request, *args, **kwargs):
        # 获取token
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            result = {'code': 403, 'error': 'please login'}
            return JsonResponse(result)
        # 校验token
        try:
            res = jwt.decode(token, settings.JWT_TOKEN_KEY, algorithms='HS256')
        except Exception as e:
            print(f'jwt decode error is {e}')
            # 失败 code 403 error 请登录
            result = {'code': 403, 'error': 'please login'}
            return JsonResponse(result)
        # 获取用户
        # 获取token中payload部分username
        username = res['username']
        user = UserProfile.objects.get(username=username)
        request.my_user = user
        return func(request, *args, **kwargs)

    return wrap


def get_user_by_request(request):
    # 尝试性获取登录用户
    # return UserProfile obj or None
    token = request.META.get('HTTP_AUTHORIZATION')
    if not token:
        return None
    try:
        res = jwt.decode(token, settings.JWT_TOKEN_KEY,algorithms='HS256')
    except Exception as e:
        return None
    # 根据业务需要返回user对象或者username
    username = res['username']
    # user = UserProfile.objects.get(username=username)
    return username
