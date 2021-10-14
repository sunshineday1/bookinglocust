import json
import os
from typing import List
from urllib.parse import urlparse

import click
import yaml


def form_to_json(form: list) -> dict:
    d = {x["name"]: x["value"] for x in form}
    return d


todo_remove_by_headers = [
    "Content-Length",
]


def filter_headers(headers: dict) -> dict:
    for k in todo_remove_by_headers:
        headers.pop(k, "")

    return headers


class Session:
    stage = 0
    strict = True

    def __init__(self, request, response):
        self.request = self.make_request(request)
        self.response = self.make_response(response)
        Session.stage += 1
        self.id = Session.stage

    def make_request(self, request):
        _request = {
            "method": request["method"],
            "url": request["url"],
            "headers": filter_headers(form_to_json(request["headers"])),
        }

        body_type = request.get("postData", {}).get("mimeType")
        if body_type:
            if "application/x-www-form-urlencoded" in body_type:
                _request["data"] = form_to_json(request["postData"]["params"])
            elif "application/json" in body_type:
                _request["json"] = json.loads(request["postData"]["text"])

        # for k in [_k for _k, _v in _request.items() if _v == {}]:
        #     _request.pop(k)
        return _request

    def make_response(self, response):
        _response = {
            "status_code": response["status"],
        }
        if "application/json" in response["content"]["mimeType"]:
            try:
                _response["json"] = json.loads(response["content"].get("text"))
            except:
                pass

        if self.strict is False:
            _response["strict"]: False

        return _response

    def __repr__(self):
        return f"< Session \n Request :{self.request} \n Response:{self.response} \n >"

    @staticmethod
    def from_file(path, host):
        with open(path, encoding="utf-8") as f:
            content = f.read()
        return Session.from_json(content, host)

    @staticmethod
    def from_json(content: str, host) -> list:
        host_by_headers = {"name": "Host", "value": host}
        entries = json.loads(content)["log"]["entries"]
        session_list = [
            Session(entrie["request"], entrie["response"])
            for entrie in entries
            if not host or host_by_headers in entrie["request"]["headers"]
        ]

        return session_list

    def dump_to_str(self, test_name: str) -> str:
        url = urlparse(self.request["url"])
        name = (
            f"{self.request['method']}_{url.path}_Return_{self.response['status_code']}"
        )

        name = name.replace("https://", "").replace("http://", "").replace("/", "#")

        d = {
            "test_name": f"test_case_{self.id} {test_name}",
            "stages": [
                {"name": name, "request": self.request, "response": self.response}
            ],
        }
        return yaml.dump(
            d, allow_unicode=True, explicit_start=True, default_flow_style=False
        )


def dump_to_file(sessions: List[Session], dir_path="./", single_file=False):
    output_count = 0
    content_list = [s.dump_to_str("generate by har2tavern") for s in sessions]
    if single_file is True:
        file_path = os.path.join(dir_path, "test_api_all.tavern1.yaml")
        content = "\n".join(content_list)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Output file: {file_path}")
        output_count = 1

    else:
        for output_count, content in enumerate(content_list, start=1):
            file_path = os.path.join(dir_path, f"test_api_{output_count}.tavern.yaml")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Output file: {file_path}")

    print(f"Successfully generated {output_count} files ")


@click.command(help="根据har文件，生成yaml格式的Restfuil API 自动化测试用例")
@click.argument("harfile", type=click.File(encoding="utf-8-sig"))
@click.option("-H", "--host", default=None, type=str, help="只为指定的host生成用例")
@click.option("-S", "--single-file", default=False, type=bool, help="将用例合并到单个文件")
def main(harfile, host=None, single_file=False):
    sessions: List[Session] = Session.from_json(harfile.read(), host)

    dump_to_file(sessions, single_file=single_file)


@click.command(help="根据har文件，生成requests代码")
@click.argument("harfile", type=click.File(encoding="utf-8-sig"))
@click.option("-H", "--host", default=None, type=str, help="根据Host筛选请求")
def har2requests(
    harfile, host=None,
):
    sessions: List[Session] = Session.from_json(harfile.read(), host)

    request_code = """import requests

s = requests.Session()

"""

    for i, session in enumerate(sessions):
        request_code += f"resp_{i} = s.request(**{session.request}) \n"

    print(request_code)


@click.command(help="根据har文件，生成loucst代码")
@click.argument("harfile", type=click.File(encoding="utf-8-sig"))
@click.option("-H", "--host", default=None, type=str, help="根据Host筛选请求")
def har2locust(
    harfile, host=None,
):
    sessions: List[Session] = Session.from_json(harfile.read(), host)

    request_code = """from locust import HttpUser, task, between


class QuickstartUser(HttpUser):
    wait_time = between(1, 2)  # 用户在执行每个task之后等待1-2秒
    token = ""

    #  被task装饰的方法，就是每个用户要执行的操作。操作之间没有依赖、顺序等关系
"""

    for i, session in enumerate(sessions):
        request_code += f"""
    @task
    def task_{i}(self):
        resp = self.client.request(**{session.request})
"""
    print(request_code)


if __name__ == "__main__":
    main()
