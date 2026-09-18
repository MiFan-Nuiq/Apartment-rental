# -*- coding: utf-8 -*-
"""
基础页面对象模块：封装 Playwright 的常用页面操作。

设计说明：
    - 所有具体页面对象（如 LoginPage）继承 BasePage，复用通用操作；
    - 页面对象只负责“定位与操作”，断言放在测试用例中，保持职责清晰。
"""

from playwright.sync_api import Page


class BasePage:
    """页面基类：封装 goto / fill / click / wait_for_url / get_text / screenshot 等常用操作。"""

    def __init__(self, page: Page):
        """
        初始化页面对象。

        参数:
            page: Playwright 的 Page 对象（由 ui_page fixture 提供）
        返回:
            无
        异常:
            无
        """
        self.page = page  # 持有页面句柄，后续所有定位与操作都基于它

    def goto(self, url: str):
        """
        打开指定 URL。

        参数:
            url: 完整访问地址
        返回:
            无
        异常:
            playwright.sync_api.Error：页面加载失败（如服务未启动）
        """
        self.page.goto(url)

    def fill(self, selector: str, value: str):
        """
        在输入框中填写内容。

        参数:
            selector: 元素选择器
            value: 待填写的内容
        返回:
            无
        异常:
            playwright.sync_api.Error：元素不可见或不可编辑
        """
        self.page.locator(selector).fill(value)

    def click(self, selector: str):
        """
        点击元素。

        参数:
            selector: 元素选择器
        返回:
            无
        异常:
            playwright.sync_api.Error：元素不存在或多匹配（strict 模式）
        """
        # 使用 .first 规避同名元素多处渲染导致的 strict 模式报错
        self.page.locator(selector).first.click()

    def wait_for_url(self, url_pattern: str, timeout: int = 10000):
        """
        等待页面跳转到目标 URL。

        参数:
            url_pattern: URL 匹配模式（支持 ** 通配）
            timeout: 超时毫秒数，默认 10000
        返回:
            无
        异常:
            playwright.sync_api.TimeoutError：超时仍未跳转
        """
        self.page.wait_for_url(url_pattern, timeout=timeout)

    def get_text(self, selector: str) -> str:
        """
        获取元素文本内容。

        参数:
            selector: 元素选择器
        返回:
            str：元素文本
        异常:
            playwright.sync_api.Error：元素不存在
        """
        return self.page.locator(selector).first.inner_text()

    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """
        判断元素是否可见（等待至超时）。

        参数:
            selector: 元素选择器
            timeout: 等待超时毫秒数，默认 5000
        返回:
            bool：可见返回 True，超时未出现返回 False
        异常:
            无（内部捕获超时异常）
        """
        try:
            # 等待元素可见，成功即返回 True
            self.page.locator(selector).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False  # 超时视为不可见，不向上抛异常

    def screenshot(self, path: str):
        """
        页面截图。

        参数:
            path: 截图保存路径
        返回:
            无
        异常:
            playwright.sync_api.Error：截图失败
        """
        self.page.screenshot(path=path)

    def get_local_storage(self, key: str):
        """
        读取浏览器 localStorage 中指定 key 的值。

        参数:
            key: localStorage 键名（如 token / role / userId）
        返回:
            str | None：对应值，不存在时返回 None
        异常:
            playwright.sync_api.Error：脚本执行失败
        """
        return self.page.evaluate(f"localStorage.getItem('{key}')")

    def get_current_url(self) -> str:
        """
        获取当前页面 URL。

        参数:
            无
        返回:
            str：当前页面地址
        异常:
            无
        """
        return self.page.url

    def get_title(self) -> str:
        """
        获取页面标题。

        参数:
            无
        返回:
            str：页面 title
        异常:
            playwright.sync_api.Error：页面未就绪
        """
        return self.page.title()