# !/user/bin/env python3
# -*- coding: UTF-8 -*-
# @Author : 梵音
# @Time : 2020/11/20 16:24
# @File : locustfile.py

from locust import HttpUser, between, task
from locust.clients import ResponseContextManager
import logging


class AwesomeUser(HttpUser):

    # wait_time = between(1, 2)
    # _count = 0
    #
    # _id = 0  # 给每个user一个独一无二的id
    # index_page_count = 0
    # load_page_count = 0
    # load_sub_page_count = 0

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.__class__._count += 1
    #     self._id = self.__class__._count

    @task()
    def index_page(self):
        # logging.info(f'userid = {self._id} start')
        resp = self.client.request(
            catch_response=True,
            **{"method": "GET",
               "url": "https://leyoutest.fangte.com/project/api/Test/Test",
               "headers": {"debug": "true"},
               # "params": {"parkId": 31}
            }
        )
        with resp as r:
            r: ResponseContextManager
            item_name = []
            try:
                data = r.json()['data']['data']
                if len(data) >= 1:
                    for i in range(len(data)):
                        item_name.append(data[i]['projectName'])
                    # print(item_name)
                    if '秦陵历险-循环无等候未开始' in item_name:
                        r._report_success()
                        # print('pass')
                    else:
                        r._report_failure(f"失败 :{r}")
                        print('fail')
                else:
                    r._report_failure(f"失败 :{r}")
                    print(r.json(encoding="utf-8")['data'])
            except Exception:
                r._report_failure(f"失败 :{r}")
                print(r.json(encoding="utf-8")['data'])
