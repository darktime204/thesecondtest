from django.conf.urls import url

from . import views

urlpatterns = [

    # 1.首页面 显示
    url(r'^$', views.IndexView.as_view(), name='index'),
]
