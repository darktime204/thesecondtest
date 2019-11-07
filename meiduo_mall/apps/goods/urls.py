from django.conf.urls import url

from . import views

urlpatterns = [

    # 1.列表页
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view(), name='list'),
    # 2.热销商品 hot/(?P<category_id>\d+)/
    url(r'^hot/(?P<category_id>\d+)/$', views.HotView.as_view()),

]
