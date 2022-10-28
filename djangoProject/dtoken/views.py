from django.shortcuts import render
import json
from django.http import JsonResponse
from blog.models import UserProfile
from utils.encrypt import md5
from utils.token import make_token

# Create your views here.


#异常码 10200-10299
# Create your views here.
def tokens(request):
    if request.method != 'POST':
        result = {'code':10200, 'error':'Please use POST!'}
        return JsonResponse(result)
    json_str = request.body
    json_obj = json.loads(json_str)
    username = json_obj['username']
    password = json_obj['password']
    #校验用户名和密码
    try:
        user = UserProfile.objects.get(username=username)
    except Exception as e:
        result = {'code':10201, 'error':'The username or password is wrong'}
        return JsonResponse(result)

    if md5(password)!= user.password:
        result = {'code':10202, 'error':'The username or password is wrong'}
        return JsonResponse(result)

    #记录会话状态
    token = make_token(username)
    result = {'code':200, 'username':username,'data':{'token':token}}
    return JsonResponse(result)



