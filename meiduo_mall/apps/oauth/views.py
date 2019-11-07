from django import http
from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from QQLoginTool.QQtool import OAuthQQ
from apps.oauth.models import OAuthQQUser
from apps.users.models import User
from utils.secret import SecretOauth

# 判断是否 绑定  opendi
def is_bind_openid(openid, request):
    # 1.绑定过----首页
    try:
        qq_user = OAuthQQUser.objects.get(openid=openid)

    except OAuthQQUser.DoesNotExist:

        # 给前端的 重要数据 加密 或者 混淆
        openid = SecretOauth().dumps({'openid': openid})

        # 2.没有绑定----绑定页面跳转
        return render(request, 'oauth_callback.html', {'openid': openid})
    else:
        # 绑定过-->--首页
        user = qq_user.user
        # 1.保持登录状态
        login(request, user)

        response = redirect(reverse('contents:index'))
        # 2. 设置cookie
        response.set_cookie('username', user.username, max_age=14 * 24 * 3600)

        # 3. 首页
        return response


class QQAuthCallBackView(View):
    # 1. code--token--openid--是否绑定
    def get(self, request):
        # /oauth_callback?code=027C81EA07E1F11115DEA7DFFFA64747&state=None
        # 1.解析code
        code = request.GET.get('code')

        if not code:
            return http.HttpResponseForbidden('无效的code!')

        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=None
        )
        # 1. code --- token
        token = oauth.get_access_token(code)

        # 2. token---openid
        openid = oauth.get_open_id(token)

        # 判断是否绑定openid
        response = is_bind_openid(openid, request)

        return response

    # 2. 提交绑定的数据 ---保存
    def post(self, request):

        # 1.接收解析参数
        mobile = request.POST.get('mobile')
        pwd = request.POST.get('password')
        sms_code = request.POST.get('sms_code')


        # 2. 校验---判断空, 正则---短信验证码
        openid = request.POST.get('openid')
        loads_openid_dict = SecretOauth().loads(openid)
        openid = loads_openid_dict.get('openid')
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': "openid是无效的!"})

        # 3.判断用户是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 5.不存在---创建新用户
            user = User.objects.create_user(username=mobile,mobile=mobile,password=pwd)
        else:
            # 4.存在---校验密码
            if not user.check_password(pwd):
                return render(request, 'oauth_callback.html', {'account_errmsg': "用户名或密码错误!"})


        # 6. 绑定 openid
        try:
            qq_user = OAuthQQUser.objects.create(user=user,openid=openid)
        except Exception as e:
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': "qq绑定失败!"})


        # 7. 保持登录状态---设置cookie首页用户名----首页
        # 1.保持登录状态
        login(request, user)

        response = redirect(reverse('contents:index'))
        # 2. 设置cookie
        response.set_cookie('username', user.username, max_age=14 * 24 * 3600)

        # 3. 首页
        return response


class QQAuthURLView(View):
    # 1. 返回qq登录地址
    def get(self, request):
        # 1.实例化对象--- 美多---认证---QQ
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=None
        )

        # 2.获取qq登录地址
        qq_login_url = oauth.get_qq_url()

        return http.JsonResponse({'code': 0, 'errmsg': "获取qq登录地址", "login_url": qq_login_url})
