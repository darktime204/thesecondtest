from django.conf.urls import url

from . import views

urlpatterns = [

    # 1.首页面 显示
    url(r'^areas/$', views.AreasView.as_view()),
]
