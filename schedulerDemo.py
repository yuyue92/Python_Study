from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging
import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def my_job():
    """要执行的定时任务"""
    print(f"任务执行时间: {datetime.datetime.now()}")
    # 这里写你的业务逻辑
    # outlook邮件处理等...

def job_listener(event):
    """任务执行监听器"""
    if event.exception:
        logger.error(f"任务执行失败: {event.job_id}, 错误: {event.exception}")
    else:
        logger.info(f"任务执行成功: {event.job_id}")

# 创建调度器
scheduler = BlockingScheduler()

# 添加任务
scheduler.add_job(
    my_job,
    'interval',  # 间隔执行
    minutes=30,  # 每30分钟执行一次
    id='email_processing_job',
    replace_existing=True
)

# 添加监听器
scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

try:
    logger.info("定时任务调度器启动...")
    scheduler.start()
except KeyboardInterrupt:
    logger.info("收到中断信号，停止调度器...")
except Exception as e:
    logger.error(f"调度器运行错误: {e}")
