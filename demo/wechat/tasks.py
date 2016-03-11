# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from celery.utils.log import get_task_logger
from demo import app
from wechat.models import Wechat
from wechat.utils import get_component


@app.task
def process_wechat_query_auth_code_test(FromUserName, query_auth_code):
    """
    处理发布前微信的自动化测试query_auth_code
    """
    logger = get_task_logger('process_wechat_query_auth_code_test')
    logger.info(FromUserName)
    logger.info(query_auth_code)
    component = get_component()
    client = component.get_client_by_authorization_code(query_auth_code)
    client.message.send_text(FromUserName, query_auth_code+'_from_api')


@app.task(bind=True)
def refresh_all_wechat_token(self):
    """
    定时1小时，刷新所有已授权公众号
    """
    logger = get_task_logger('refresh_all_wechat_token')
    for wechat in Wechat.objects.exclude(appid=settings.TEST_APPID).all():
        if not wechat.authorized:
            logger.error('公众号{0}失去授权'.format(wechat.appid))
            continue
        refresh_wechat_token.delay(wechat.appid)


@app.task(bind=True)
def refresh_wechat_token(self, appid):
    """
    刷新已授权公众号
    """
    logger = get_task_logger('refresh_wechat_token')
    wechat = Wechat.objects.get(appid=appid)
    if not wechat.authorized:
        logger.error('公众号{0}失去授权'.format(wechat.appid))
        return None
    try:
        result = wechat.client.fetch_access_token()
        logger.info(result)
    except Exception as e:
        logger.error(u'刷新已授权公众号{0}失败:{1}'.format(appid, str(e)))
