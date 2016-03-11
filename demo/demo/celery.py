# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery


# wechatpy依赖requests。这里提高requests日志输出的级别
logging.getLogger("requests").setLevel(logging.WARNING)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo.settings')

from django.conf import settings
app = Celery('demo')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
