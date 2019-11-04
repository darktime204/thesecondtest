from django import http
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection


class SmsCodeView(View):
    def get(self, request, mobile):
        # - 1.接收参数 解析参数
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # - 2.校验图形验证码 redis
        # img_client = get_redis_connection('verify_image_code')
        # redis_img_code = img_client.get('img_%s' % uuid)
        #
        # if image_code.lower() != redis_img_code.decode().lower():
        #     return http.HttpResponseForbidden('验证码输入有误!')

        # - 3.生成随机6位码
        import random
        sms_code = random.randint(100000, 999999)

        #  4.使用 容联云 发送短信
        sms_client = get_redis_connection('sms_code')

        # 获取redis里面的标识
        send_sms_flag = sms_client.get('send_flag%s' % mobile)

        # 如果 倒计时的标识 在
        if send_sms_flag:
            return http.HttpResponseForbidden('短信发送太频繁,请稍后!')

        # 如果 倒计时的标识 不在

        # 使用异步任务 celery工具 发短信
        from celery_tasks.sms.tasks import ccp_send_sms_code
        ccp_send_sms_code.delay(mobile, sms_code)
        print('项目里面的短信:', sms_code)

        # 5.存储短信
        pipeline = sms_client.pipeline()
        pipeline.setex("sms_%s" % mobile, 300, sms_code)
        pipeline.setex('send_flag%s' % mobile, 60, 1)
        pipeline.execute()

        # - 6.返回响应对象a
        return http.JsonResponse({'code': '0', 'errmsg': '发送短信成功'})


class ImageCodeView(View):
    def get(self, request, uuid):
        # 1. 前端发请求-->key---UUID  唯一码
        # 2. 接收请求 UUID 参数, 正则校验

        # 3. 生成图片验证码( 随机产生的 )
        from libs.captcha.captcha import captcha
        image_code, image = captcha.generate_captcha()

        # 4. 使用django-redis存储 随机码(UUID:code)
        from django_redis import get_redis_connection
        client = get_redis_connection('verify_image_code')
        # client.setex('img_%s' % uuid, 300, image_code)

        # constants.IMAGE_CODE_REDIS_EXPIRES 代码易扩展
        from apps.verifications import constants
        client.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, image_code)

        # 5. 返回前端 图片验证码--二进制流
        return http.HttpResponse(image, content_type='image/jpg')
