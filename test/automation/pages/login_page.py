# -*- coding: utf-8 -*-
"""
登录页 Page Object 模块。

元素定位依据（frontend/src/views/Login.vue 真实代码）：
    用户名输入框  <input type="text"     placeholder="请输入用户名">
    密码输入框    <input type="password" placeholder="••••••••">
    登录按钮      <button type="submit" class="submit-btn">登录</button>
    错误提示      <div class="error-message">{{ errorMsg }}</div>
跳转规则（Login.vue → redirectByRole）：
    ADMIN    -> /admin/dashboard
    LANDLORD -> /landlord/apartments
    TENANT   -> /tenant/apartments
登录成功后写入 localStorage：token / username / realName / role / userId
"""

from pages.base_page import BasePage


class LoginPage(BasePage):
    """登录页对象：封装登录页元素定位与登录操作。"""

    # ---------- 元素定位器（与 Login.vue 中的 placeholder / class 保持一致） ----------
    USERNAME_INPUT = 'input[placeholder="请输入用户名"]'
    PASSWORD_INPUT = 'input[placeholder="••••••••"]'
    SUBMIT_BUTTON = "button.submit-btn"
    ERROR_MESSAGE = ".error-message"

    # ---------- 页面信息 ----------
    LOGIN_PATH = "/login"                          # 登录页路由
    PAGE_TITLE = "公寓租赁管理系统"                 # 页面标题（用于加载断言）

    # 角色 -> 登录后跳转路由映射（对应 Login.vue 的 redirectByRole）
    ROLE_REDIRECT = {
        "ADMIN": "/admin/dashboard",
        "LANDLORD": "/landlord/apartments",
        "TENANT": "/tenant/apartments",
    }

    def open(self, base_url: str):
        """
        打开登录页。

        参数:
            base_url: 前端基础地址（如 http://localhost:5173）
        返回:
            无
        异常:
            playwright.sync_api.Error：页面加载失败
        """
        # 拼接登录路由并访问
        self.goto(base_url + self.LOGIN_PATH)

    def input_username(self, username: str):
        """
        在用户名输入框填写用户名。

        参数:
            username: 用户名
        返回:
            无
        异常:
            playwright.sync_api.Error：输入框不可用
        """
        self.fill(self.USERNAME_INPUT, username)

    def input_password(self, password: str):
        """
        在密码输入框填写密码。

        参数:
            password: 密码
        返回:
            无
        异常:
            playwright.sync_api.Error：输入框不可用
        """
        self.fill(self.PASSWORD_INPUT, password)

    def click_login(self):
        """
        点击登录按钮。

        参数:
            无
        返回:
            无
        异常:
            playwright.sync_api.Error：按钮不可点击
        """
        self.click(self.SUBMIT_BUTTON)

    def login(self, username: str, password: str):
        """
        完整登录动作：填用户名 -> 填密码 -> 点登录。

        参数:
            username: 用户名
            password: 密码
        返回:
            无
        异常:
            playwright.sync_api.Error：任一环节元素不可用
        """
        # 依次执行三步操作，供用例一行调用
        self.input_username(username)
        self.input_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        """
        获取页面错误提示文本。

        参数:
            无
        返回:
            str：错误提示内容（如“用户名或密码错误”）
        异常:
            playwright.sync_api.Error：错误提示元素不存在
        """
        return self.get_text(self.ERROR_MESSAGE)

    def is_error_visible(self, timeout: int = 5000) -> bool:
        """
        判断错误提示是否可见。

        参数:
            timeout: 等待超时毫秒数
        返回:
            bool：可见返回 True，否则 False
        异常:
            无
        """
        return self.is_visible(self.ERROR_MESSAGE, timeout=timeout)

    def wait_redirect(self, role: str = "TENANT", timeout: int = 10000):
        """
        等待登录成功后的角色主页跳转。

        参数:
            role: 角色（ADMIN / LANDLORD / TENANT），默认 TENANT
            timeout: 超时毫秒数，默认 10000
        返回:
            无
        异常:
            KeyError：传入未知角色
            playwright.sync_api.TimeoutError：超时未跳转
        """
        # 从角色映射表取目标路由，未知角色直接抛 KeyError（不臆造路由）
        target = self.ROLE_REDIRECT[role]
        self.wait_for_url("**" + target, timeout=timeout)