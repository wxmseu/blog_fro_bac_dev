from django.urls import path
from . import views


urlpatterns = [
    path('<str:topic_id>', views.message_view),
]
