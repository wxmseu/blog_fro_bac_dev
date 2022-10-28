from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
import json
from .models import UserProfile
from utils.encrypt import md5
from utils.login_dec import login_check
from utils.sms import send_msm
from django.utils.decorators import method_decorator
import random
from django.core.cache import cache
from .tasks import send_msm_c

# Create your views here.
def test_cors(request):
    res = {'code': 200, 'msg': 'hello'}
    return JsonResponse(res)


# 短信接收视图
def sms_view(request):
    json_obj = json.loads(request.body)
    phone = json_obj['phone']
    # 判断手机号是否已注册，（手机号是否符合格式要求）
    # user = UserProfile.objects.filter(phone=phone).exists()
    # if user:
    #     return JsonResponse({'code': 202, 'error': '该手机号已注册'})
    # 生成随机字符串
    ran_num = random.randint(1000, 10000)
    # 发送验证码
    # 判断缓存中是否存在该号码，如果有未过期的key则提示稍后再发送
    code=cache.get(f'sms_{phone}')
    if code:
        return JsonResponse({'code': 202, 'error': '请两分钟后重试'})
    # res = send_msm(phone, ran_num)
    # celery版发送短信
    send_msm_c.delay(phone,ran_num)
    # res = json.loads(res)
    # print(type(res['statusCode']))
    # 根据res.statusCode判断异常情况
    # if res['statusCode'] != '000000':
    #     return JsonResponse({'code': 201, 'error': '发送失败，稍后重试'})
    # 存储随机字符串django_redis
    cache_key = f'sms_{phone}'
    cache.set(cache_key, ran_num, 120)
    return JsonResponse({'code': 200})


# 用来接收用户头像请求
@login_check
def users_views(request, username):
    if request.method != 'POST':
        result = {'code': 10103, 'error': 'Please use POST'}
        return JsonResponse(result)
    # 从装饰器中获取到用户对象
    user = request.my_user
    # try:
    #     user = UserProfile.objects.get(username=username)
    # except Exception as e:
    #     result = {'code': 10104, 'error': 'The username is error'}
    #     return JsonResponse(result)

    avatar = request.FILES['avatar']
    user.avatar = avatar
    user.save()
    return JsonResponse({'code': 200})


# #CBV
# 更灵活[可继承]
# 对未定义的http method请求 直接返回405响应
class UserViews(View):
    def get(self, request, username=None):
        if username:
            # api/v1/users/jdq
            try:
                user = UserProfile.objects.get(username=username)
            except Exception as e:
                result = {'code': 10102, 'error': 'The username is wrong'}
                return JsonResponse(result)
            # avatar 为对象需要对其str 转换成字符串
            result = {'code': 200, 'username': username,
                      'data': {'info': user.info, 'sign': user.sign, 'nickname': user.nickname,
                               'avatar': str(user.avatar)}}
            return JsonResponse(result)

        else:
            # /v1/users
            pass

        return JsonResponse({'code': 200, 'msg': 'test'})

    def post(self, request):
        json_str = request.body
        json_obj = json.loads(json_str)
        username = json_obj['username']
        email = json_obj['email']
        password_1 = json_obj['password_1']
        password_2 = json_obj['password_2']
        phone = json_obj['phone']
        sms_num = json_obj['sms_num']

        # 参数基本检查
        if password_1 != password_2:
            result = {'code': 10100, 'error': 'The password is not same~'}
            return JsonResponse(result)
        # 比对验证码是否正确，注意类型
        old_code = cache.get(f'sms_{phone}')
        if not old_code:
            result = {'code': 10110, 'error': '验证码已经过期，请重新获取'}
            return JsonResponse(result)
        if old_code != int(sms_num):
            result = {'code': 10111, 'error': '验证码错误，请重新获取'}
            return JsonResponse(result)
        # 检查用户名是否可用
        old_users = UserProfile.objects.filter(username=username)
        if old_users:
            result = {'code': 10101, 'error': 'The username is already existed'}
            return JsonResponse(result)
        UserProfile.objects.create(username=username, nickname=username, password=md5(password_1), email=email,
                                   phone=phone)
        result = {'code': 200, 'username': username, 'data': {}}
        return JsonResponse(result)

    @method_decorator(login_check)
    def put(self, request, username=None):
        # 更新用户数据[昵称，个人签名，个人描述]
        # 从装饰器中获取到用户对象
        user = request.my_user
        # try:
        #     user = UserProfile.objects.get(username=username)
        # except Exception as e:
        #     result = {'code': 10105, 'error': 'The username is error'}
        #     return JsonResponse(result)
        json_obj = json.loads(request.body)
        user.sign = json_obj['sign']
        user.info = json_obj['info']
        user.nickname = json_obj['nickname']
        user.save()
        return JsonResponse({'code': 200})
