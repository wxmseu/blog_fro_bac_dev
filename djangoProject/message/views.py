import json
from topic.models import Topic
from utils.login_dec import login_check
from django.http import JsonResponse
from .models import Message

# Create your views here.
''' 异常码 14000-14300'''


@login_check
def message_view(request, topic_id):
    user = request.my_user
    json_obj = json.loads(request.body)
    content = json_obj['content']
    parent_message = json_obj.get('parent_id',0)
    try:
        topic = Topic.objects.get(id=int(topic_id))
    except Exception as e:
        return JsonResponse({'code': 14000, 'error': 'The topic is not existed'})
    Message.objects.create(content=content, parent_message=parent_message, publisher=user, topic=topic)
    return JsonResponse({'code': 200})
