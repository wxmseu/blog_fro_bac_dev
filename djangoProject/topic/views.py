from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from utils.login_dec import login_check, get_user_by_request
import json
from .models import Topic
from blog.models import UserProfile
from utils.cache_dec import cache_set
from django.core.cache import cache
from message.models import Message

# Create your views here.
"""异常码 10300-10399"""


class TopicView(View):
    def clear_topics_cache(self, request):
        # 不带参数的路由 path_info()

        path = request.path_info
        cache_key_p = ['topic_cache_self_', 'topic_cache_']
        cache_key_h = ['', '?category=tec', '?category=no-tec']
        all_keys = []
        for key_p in cache_key_p:
            for key_h in cache_key_h:
                all_keys.append(key_p + path + key_h)
        cache.delete_many(all_keys)

    def make_topics_res(self, author, topics):
        topic = []
        for top in topics:
            d = {
                'id': top.id,
                'title': top.title,
                'category': top.category,
                'created_time': top.created_time.strftime("%Y-%m-%d %H:%M:%S"),
                'introduce': top.introduce,
                'author': top.author.username

            }
            topic.append(d)
        result = {
            'code': '200',
            'data': {
                'nickname': author.nickname,
                'topics': topic
            }
        }
        return result

    def make_topic_detail_res(self, author, topic, is_self):
        if is_self:
            # 博主访问自己博客
            next_topic = Topic.objects.filter(id__gt=topic.id, author=author).first()
            last_topic = Topic.objects.filter(id__lt=topic.id, author=author).last()
        else:
            next_topic = Topic.objects.filter(id__gt=topic.id, author=author, limit='public').first()
            last_topic = Topic.objects.filter(id__lt=topic.id, author=author, limit='public').last()
        next_id = next_topic.id if next_topic else None
        next_title = next_topic.title if next_topic else ''
        last_id = last_topic.id if last_topic else None
        last_title = last_topic.title if last_topic else ''
        # 关联留言和回复
        all_messages = Message.objects.filter(topic=topic).order_by('-created_time')
        msg_list = []
        rep_dic = {}
        m_count = 0
        for msg in all_messages:
            if msg.parent_message:
                # 回复
                rep_dic.setdefault(msg.parent_message, [])
                rep_dic[msg.parent_message].append({'msg_id': msg.id, 'publisher': msg.publisher.nickname,
                                                    'publisher_avatr': str(msg.publisher.avatar),
                                                    'content': msg.content,
                                                    'created_time': msg.created_time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                # 留言
                m_count += 1
                msg_list.append({'id': msg.id, 'content': msg.content, 'publisher': msg.publisher.nickname,
                                 'publisher_avatar': str(msg.publisher.avatar),
                                 'created_time': msg.created_time.strftime('%Y-%m-%d %H:%M:%S'), 'reply': []})

        for m in msg_list:
            if m['id'] in rep_dic:
                m['reply'] = rep_dic[m['id']]

        result = {'code': 200, 'data': {}}
        data = {}
        data['nickname'] = author.nickname
        data['title'] = topic.title
        data['category'] = topic.category
        data['created_time'] = topic.created_time.strftime("%Y-%m-%d %H:%M:%S")
        data['content'] = '<p>' + topic.content + '<p>'
        data['introduce'] = topic.introduce
        data['author'] = author.username
        data['next_id'] = next_id
        data['next_title'] = next_title
        data['last_id'] = last_id
        data['last_title'] = last_title
        data['messages'] = msg_list
        data['messages_count'] = m_count
        result['data'] = data
        return result

    @method_decorator(login_check)
    def post(self, request, *args, **kwargs):
        # {
        #     "content": "<p>88</p>",
        #     "content_text": "88",
        #     "limit": "private",
        #     "title": "8",
        #     "category": "no-tec"
        # }
        author = request.my_user
        # 从前端获取数据
        json_obj = json.loads(request.body)
        title = json_obj['title']
        category = json_obj['category']
        limit = json_obj['limit']
        introduce = json_obj['content_text'][:30]
        content = json_obj['content']
        # 对传入的数据进行校验
        if limit not in ['private', 'public']:
            return JsonResponse({'code': 10300, 'error': 'limit error'})
        # 创建topic数据
        Topic.objects.create(title=title, category=category, limit=limit, introduce=introduce, content=content,
                             author=author)
        # 删除缓存
        self.clear_topics_cache(request)
        return JsonResponse({'code': 200})

    @method_decorator(cache_set(3600 * 24))
    def get(self, request, author_id):
        # 访问者visitor
        # 当前被访问博客的博主 author
        try:
            author = UserProfile.objects.get(username=author_id)
        except Exception as e:
            result = {'code': 10302, 'error': '博主不存在'}
            return JsonResponse(result)
        user_login = get_user_by_request(request)
        t_id = request.GET.get('t_id')
        if t_id:
            t_id = int(t_id)
            is_self = False
            if user_login == author_id:
                # 博主访问自己博客
                is_self = True
                try:
                    topic = Topic.objects.filter(id=t_id, author=author_id).first()
                except Exception as e:
                    return JsonResponse({'code': 10303, 'error': 'no topic'})
            else:
                # 其他人访问博主博客
                try:
                    topic = Topic.objects.filter(id=t_id, author=author_id, limit='public').first()
                except Exception as e:
                    return JsonResponse({'code': 10303, 'error': 'no topic'})
            result = self.make_topic_detail_res(author, topic, is_self)
            return JsonResponse(result)



        else:
            category = request.GET.get('category', None)
            if category in ['tec', 'no-tec']:
                if user_login == author_id:
                    # 博主在访问自己的博客列表
                    topics = Topic.objects.filter(author=author_id, category=category)
                else:
                    # 访客或者其他博主，只显示公开的文章
                    topics = Topic.objects.filter(author=author_id, limit='public', category=category)
            else:
                if user_login == author_id:
                    # 博主在访问自己的博客列表
                    topics = Topic.objects.filter(author=author_id)
                else:
                    # 访客或者其他博主，只显示公开的文章
                    topics = Topic.objects.filter(author=author_id, limit='public')
            result = self.make_topics_res(author, topics)
            return JsonResponse(result)

    @method_decorator(login_check)
    def delete(self, request, author_id, *args, **kwargs):
        t_id = request.GET.get('t_id')
        if request.my_user.username != author_id:
            return JsonResponse({'code': 404, 'error': '用户不一致'})
        Topic.objects.filter(id=int(t_id)).delete()
        self.clear_topics_cache(request)
        return JsonResponse({'code': 200})
