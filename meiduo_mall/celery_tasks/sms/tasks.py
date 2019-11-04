
from celery_tasks.main import app

# 1.任务 发短信
@app.task
def ccp_send_sms_code(mobile, sms_code):
    from libs.yuntongxun.sms import CCP
    result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    print('当前的短信验证码:', sms_code)

    return result

# 2. 添加装饰器 app
