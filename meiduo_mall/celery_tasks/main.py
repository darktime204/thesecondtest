# 1. 导包
from celery import Celery

# 2. 导入 项目 环境
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

# 3. 实例
app = Celery('celer_tasks')

# 4. 加载消息队列的配置
app.config_from_object('celery_tasks.config')

# 5. 自动查找 任务
app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])
