from django.shortcuts import render
from django.views import View

# 1.首页 广告页
class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')
