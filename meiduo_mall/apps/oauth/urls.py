from django.conf.urls import url

from . import views

urlpatterns = [

    # 1.获取 qq网址
    url(r'^qq/login/$', views.QQAuthURLView.as_view()),

    # 2.回调网址 oauth_callback
    url(r'^oauth_callback/$', views.QQAuthCallBackView.as_view()),

]
