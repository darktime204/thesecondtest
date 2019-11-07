from django.conf import settings
from django.core.mail import send_mail

from celery_tasks.main import app

# name 代表任务的名称
# bind 绑定是任务对象 True
# retry_backoff：异常自动重试的时间间隔 第n次(retry_backoff×2^(n-1))s
from meiduo_mall.settings.dev import logger


@app.task(bind=True, name="send_email", retry_backoff=10)
def send_verify_email(self, email, verify_url):
    # 发件人邮箱
    # 收件人邮箱
    # 内容
    # 标题

    try:
        send_mail(
            subject='美多商城激活',
            message='',
            from_email=settings.EMAIL_FROM,
            recipient_list=[email],
            html_message='<p>尊敬的用户您好！</p>' \
                         '<p>感谢您使用美多商城。</p>' \
                         '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                         '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
        )

        print('发邮件--=------')
    except Exception as e:
        logger.error(e)
        raise self.retry(exc=e, max_retries=3)
