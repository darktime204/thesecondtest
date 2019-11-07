import json
import re
from django import http
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from apps.areas.models import Address
from apps.users.models import User
from utils.response_code import RETCODE
from utils.secret import SecretOauth


# 11. 修改密码
class ChangePwdView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        user = request.user

        # 1.接收参数
        old_pwd = request.POST.get('old_pwd')
        new_pwd = request.POST.get('new_pwd')
        new_cpwd = request.POST.get('new_cpwd')

        # 2.校验 密码是否正确
        if not user.check_password(old_pwd):
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})

        # 3. 改密码 set_password()
        user.set_password(new_pwd)
        user.save()

        # 4. 清空登录状态, 登录页---清除cookie
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')

        return response

# 10.新增地址
class AddressCreateView(LoginRequiredMixin, View):
    def post(self, request):

        # 判断收货地址 大于 20 个 不在增加
        # 用户的地址(没有逻辑删除的) .count > 20
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        count = request.user.addresses.filter(is_deleted=False).count()

        if count > 20:
            return http.JsonResponse({'errmsg': "地址最多20个!"})

        # - 1.接收参数 json  json.loads(request.body.decode())['']
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # - 2.校验 判空 判正则
        # - 3. 数据库存储 Address.objects.create()
        address = Address.objects.create(
            user=request.user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        # 判断用户 是否有 默认收货地址
        if not request.user.default_address:
            request.user.default_address = address
            request.user.save()

        # - 4. 构建前端需要的 字典{}
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


# 9. 收货地址
class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        # 1.查 当前用户的  未删除 地址
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        # 2. 装换前端 数据格式 [{}]
        addresss_list = []
        for address in addresses:
            addresss_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })

        context = {
            'default_address_id': request.user.default_address_id,
            'addresses': addresss_list,
        }
        # render--jinja渲染-->js--vue渲染
        return render(request, 'user_center_site.html', context)


# 8.激活邮箱
class VerifyEmailView(View):
    def get(self, request):
        # 1.接收token
        token = request.GET.get('token')

        # 2.解密
        token_dict = SecretOauth().loads(token)

        # 3. 取数据库对比
        try:
            user = User.objects.get(id=token_dict['user_id'], email=token_dict['email'])
        except Exception as e:
            return http.HttpResponseForbidden('token 无效的')

        # 4. 改email_active
        user.email_active = True
        user.save()

        # 5.重定向到 用户中心
        return redirect(reverse('users:info'))


# 7. 新增邮箱
class EmailView(LoginRequiredMixin, View):
    def put(self, request):
        # 1.接收参数
        email = json.loads(request.body.decode()).get('email')

        # 2.正则校验

        # 3.修改 User.objects.filter().update(email=email)
        # request.user
        request.user.email = email
        request.user.save()

        # 发邮件的功能
        # 生成 激活链接
        from apps.users.utils import generate_verify_email_url
        verify_url = generate_verify_email_url(request.user)

        from celery_tasks.email.tasks import send_verify_email
        send_verify_email.delay(email, verify_url)

        # 4.返回响应对象
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


# 6.用户中心显示
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        #  render  前后不分离  -  jinja2模板
        #  JsonResponse 分录---- vue模板

        #  render 前后不分离  -  jinja2模板-----vue渲染
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        return render(request, 'user_center_info.html', context)


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
