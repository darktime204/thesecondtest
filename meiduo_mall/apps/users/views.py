import re
from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from apps.users.models import User
from utils.response_code import RETCODE




# 6.用户中心显示
class UserInfoView(LoginRequiredMixin,View):
    def get(self, request):
        return render(request, 'user_center_info.html')

# 5.退出登录
class LogoutView(View):
    def get(self, request):
        from django.contrib.auth import logout
        # 清除session
        logout(request)

        # 一下代码可以不写--- 清除cookie--首页用户名不显示
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')

        return response


# 4.登录页
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # - 1.接收参数 : username password 记住登录
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # - 2.校验 判空 all() 判正则re

        # - 3. 判断用户名和密码  是否正确
        # orm --传统---User.objects.get(username=username,password=password)
        # django认证系统 authenticate(username=username,password=password)

        from django.contrib.auth import authenticate, login
        user = authenticate(username=username, password=password)

        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错了!'})

        # 4. 保持登录状态  login()
        login(request, user)

        if remembered == 'on':
            # 记住 None 默认 2 周
            request.session.set_expiry(None)
        else:
            # 不记住 -- 会话结束就失效
            request.session.set_expiry(0)

        # next 获取
        next = request.GET.get('next')

        if next:
            response = redirect(reverse('users:info'))
        else:
            response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=14 * 3600 * 24)

        #   5. 跳转到首页 redirect(reverse('contents:index'))
        return response


# 3.判断手机号 是否重复
class MobileCountView(View):
    def get(self, request, mobile):
        # 1.接收参数
        # 2.正则校验
        # 3. 去数据库查询 mobile 统计个数
        count = User.objects.filter(mobile=mobile).count()
        # 4.返回响应对象
        return http.JsonResponse({'code': 0, 'errmsg': "OK", 'count': count})


# 2.判断是否 重复  username
class UsernameCountView(View):
    def get(self, request, username):
        # 1. 接收参数
        # 2. 校验参数
        # 3.去数据库查询 用户 计算个数
        count = User.objects.filter(username=username).count()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


# 1.注册功能
class RegisterView(View):
    # 1.注册页面显示
    def get(self, request):
        return render(request, 'register.html')

    # 2.注册功能提交
    def post(self, request):
        # 请求方式POST
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        # 5.是否同意协议
        allow = request.POST.get('allow')

        # 判空all()
        if not all([username, password, password2, mobile]):
            return http.HttpResponseForbidden('参数不齐!')

        # 校验参数正则校验re.match
        # 1.用户名 正则
        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        # 2.密码正则
        if not re.match('^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20密码')

        # 4. 密码 是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次密码不一致!')

        # 3.手机号正则
        if not re.match('^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')

        # 5. 是否勾选同意
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选同意')

        # 短信验证码
        sms_code = request.POST.get('msg_code')

        # 1. 从redis里面取出 短信验证码
        sms_client = get_redis_connection('sms_code')
        redis_sms_code = sms_client.get("sms_%s" % mobile)

        # 判空 代表是 短信失效了 ;  删除短信验证码后台

        # 2. 和前端 短信验证码 对比
        if sms_code != redis_sms_code.decode():
            return http.HttpResponseForbidden('短信输入有误!')

        # 6. 注册用户- ORM 原生的写法-create()  save()
        #    django权限认证---create_user()
        from apps.users.models import User
        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 7. 保持登录状态:原生---cookie session ; request.session['username']=username
        #  django权限认证 ---login()
        from django.contrib.auth import login
        login(request, user)

        # 8. 跳转到 首页 redirect(reverse())
        # return redirect('/')
        return redirect(reverse('contents:index'))
