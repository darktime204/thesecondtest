from django.conf.urls import url

from . import views

urlpatterns = [

    # 1.首页面 显示
    url(r'^qq/login/$', views.QQAuthURLView.as_view()),
]
