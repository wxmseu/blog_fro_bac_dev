from .login_dec import get_user_by_request
from django.core.cache import cache


def cache_set(expire):
    def _cache_set(func):
        def wrap(request, *args, **kwargs):
            # 区分场景，只做列表页
            if 't_id' in request.GET:
                # URL中有t_id说明是详情页
                return func(request, *args, **kwargs)
            # 生成正确的cache_key[访客访问，博主访问]

            # 获取用户登录信息
            username = get_user_by_request(request)
            # 获取用户查询的博主信息
            author = kwargs['author_id']
            # 带参数的路由request.get_full_path()
            full_path = request.get_full_path()
            if username == author:
                # 说明是博主
                cache_key = f'topic_cache_self_{full_path}'
            else:
                cache_key = f'topic_cache_{full_path}'
            # 判断是否有缓存，有缓存则直接返回
            res = cache.get(cache_key)
            if res:
                return res
            # 执行视图
            res = func(request, *args, **kwargs)
            # 存储缓存   cache对象/set/get
            cache.set(cache_key, res, expire)
            # 返回响应
            return res

        return wrap

    return _cache_set
