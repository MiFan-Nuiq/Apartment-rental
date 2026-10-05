# -*- coding: utf-8 -*-
"""
接口基类模块：抽取各 API 模块中重复的请求逻辑（拼 URL、带 token、超时、日志）。

职责（子类只需写业务接口方法，不再重复这些细节）：
    - 路径拼接：把 base_path（如 "/api/contracts"）与子路径拼成完整接口路径；
    - 自动鉴权：token 非空时自动附加 Authorization: Bearer <token> 请求头；
    - 统一请求：所有请求都走 utils/request_util.RequestUtil
      （base_url 拼接、超时 timeout、请求/响应日志均由它统一处理，此处不重复实现）；
    - 统一返回：直接返回 requests.Response 响应对象
      （含 status_code / json() / text / headers，与重构前的返回值完全一致）。

设计说明：
    - 子类在构造函数里传入 base_path 与可选 token；
    - token 传 None 时**不会**带 Authorization 头，
      用于"未登录访问受保护接口应被拦截"这类用例（如 get_apartments_without_token）；
    - 为兼容既有用例，各 API 模块在类之外**仍保留同名的模块级函数**，
      签名与返回值保持不变，内部仅转调对应的方法，
      因此 testcases 与 conftest 无需做任何修改。
"""


class BaseApi:
    """接口封装基类：负责路径拼接、鉴权头注入与统一请求发。"""

    def __init__(self, api_client, base_path: str, token: str = None):
        """
        初始化接口基类。

        参数:
            api_client: 请求工具实例（utils/request_util.RequestUtil，内部复用 requests.Session）
            base_path: 接口基础路径，如 "/api/contracts"（末尾斜杠会被自动去掉）
            token: 登录获取的 token；传 None 表示该接口不需要鉴权头
        返回:
            无
        异常:
            无（仅保存配置，不发请求）
        """
        self.api_client = api_client
        # 去掉末尾斜杠，避免拼接出双斜杠（如 /api/contracts//1）
        self.base_path = (base_path or "").rstrip("/")
        self.token = token

    def build_path(self, path=None) -> str:
        """
        拼接完整接口路径。

        参数:
            path: 子路径或路径片段（如 1、"contract/5"）；为空时返回 base_path 本身
        返回:
            str：完整接口路径，如 "/api/contracts/1"
        异常:
            无
        """
        if path is None or path == "":
            # 空路径直接返回基础路径（如 GET /api/contracts）
            return self.base_path
        return f"{self.base_path}/{str(path).lstrip('/')}"

    def build_headers(self, extra_headers: dict = None, json_content_type: bool = False) -> dict:
        """
        构造请求头：自动带上鉴权头，并按需补充 JSON 的 Content-Type。

        参数:
            extra_headers: 调用方额外传入的请求头（优先级最高，可覆盖默认值）
            json_content_type: 是否补充 "Content-Type: application/json"（POST/PUT 时为 True）
        返回:
            dict：可直接传给 requests 的请求头字典
        异常:
            无
        """
        headers = {}
        # token 为空时不带 Authorization 头（用于"未登录"场景）
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if json_content_type:
            headers.setdefault("Content-Type", "application/json")
        # 调用方显式传入的请求头优先级最高，放在最后更新
        headers.update(extra_headers or {})
        return headers

    def _request(self, method: str, path=None, json_content_type: bool = False, **kwargs):
        """
        统一的请求发送逻辑（get/post/put/delete 均经由此方法）。

        参数:
            method: HTTP 方法名（小写：get/post/put/delete）
            path: 子路径或路径片段
            json_content_type: 是否补充 JSON 的 Content-Type
            kwargs: 透传 requests 参数（json/params/timeout 等）；
                    其中 headers 会与鉴权头合并，调用方传入的同名头优先
        返回:
            requests.Response 响应对象
        异常:
            requests 相关异常（网络/超时）
        """
        # 合并鉴权头与调用方自定义头；调用方传入优先
        extra_headers = kwargs.pop("headers", None)
        kwargs["headers"] = self.build_headers(extra_headers, json_content_type=json_content_type)
        # 转发到 RequestUtil 对应方法：base_url、超时、日志都在那里统一处理
        return getattr(self.api_client, method)(self.build_path(path), **kwargs)

    def get(self, path=None, **kwargs):
        """
        发送 GET 请求。

        参数:
            path: 子路径或路径片段（为空表示访问 base_path 本身）
            kwargs: 透传 requests 参数（params/timeout 等）
        返回:
            requests.Response 响应对象
        异常:
            requests 相关异常（网络/超时）
        """
        return self._request("get", path, **kwargs)

    def post(self, path=None, **kwargs):
        """
        发送 POST 请求（自动补充 JSON 的 Content-Type）。

        参数:
            path: 子路径或路径片段
            kwargs: 透传 requests 参数（json/params/timeout 等）
        返回:
            requests.Response 响应对象
        异常:
            requests 相关异常（网络/超时）
        """
        return self._request("post", path, json_content_type=True, **kwargs)

    def put(self, path=None, **kwargs):
        """
        发送 PUT 请求（自动补充 JSON 的 Content-Type）。

        参数:
            path: 子路径或路径片段
            kwargs: 透传 requests 参数（json/params/timeout 等）
        返回:
            requests.Response 响应对象
        异常:
            requests 相关异常（网络/超时）
        """
        return self._request("put", path, json_content_type=True, **kwargs)

    def delete(self, path=None, **kwargs):
        """
        发送 DELETE 请求。

        参数:
            path: 子路径或路径片段
            kwargs: 透传 requests 参数（params/timeout 等）
        返回:
            requests.Response 响应对象
        异常:
            requests 相关异常（网络/超时）
        """
        return self._request("delete", path, **kwargs)