# -*- coding: utf-8 -*-
"""
登录页 UI 自动化测试用例（Playwright + Page Object 模式）

场景：输入账号 -> 输入密码 -> 点击登录 -> 断言跳转成功

改造说明：
    - 元素定位与操作已下沉到 pages/login_page.py（LoginPage），用例中不再出现裸选择器；
    - 页面由 conftest 的 ui_page fixture 提供（用例级隔离 + trace 录制）；
    - 用例失败时由 conftest 的 pytest_runtest_makereport 钩子自动截图到 screenshots/、
      并保存 trace 到 traces/。

依赖：
    - pip install playwright pytest-playwright（见 requirements.txt）
    - playwright install chromium
    - 前端服务需已启动（Vite，默认 http://localhost:5173）
"""

from pathlib import Path

import allure
import pytest

from conftest import PASSWORD, USERNAME
from pages.login_page import LoginPage

# 截图输出目录：test/evidence（相对本文件向上两级）
EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "evidence"


@allure.feature("UI 登录流程")
@allure.story("登录页冒烟")
class TestUILogin:
    """登录页 UI 自动化测试类（基于 LoginPage 页面对象）。"""

    @allure.title("UI登录：正确账号密码登录成功并跳转")
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_login_success(self, ui_page, ui_base_url):
        """验证输入正确账号密码点击登录后成功跳转至租户主页。"""
        # 实例化登录页对象（所有定位与操作由其封装）
        login_page = LoginPage(ui_page)

        # 步骤一：打开登录页
        with allure.step("打开登录页面"):
            login_page.open(ui_base_url)
            # 断言页面标题，确认前端已正常渲染
            assert login_page.get_title() == LoginPage.PAGE_TITLE, (
                f"页面标题异常，实际：{login_page.get_title()}"
            )

        # 步骤二：输入账号密码并点击登录
        with allure.step("输入账号、密码并点击登录"):
            login_page.login(USERNAME, PASSWORD)

        # 步骤三：断言跳转成功
        with allure.step("断言跳转至租户主页"):
            login_page.wait_redirect("TENANT")
            current_url = login_page.get_current_url()
            assert LoginPage.ROLE_REDIRECT["TENANT"] in current_url, (
                f"登录后未跳转到 {LoginPage.ROLE_REDIRECT['TENANT']}，当前：{current_url}"
            )

        # 步骤四：断言登录态写入 localStorage
        with allure.step("断言 localStorage 已写入登录态"):
            token = login_page.get_local_storage("token")
            role = login_page.get_local_storage("role")
            assert token, "localStorage 中未写入 token"
            assert role == "TENANT", f"localStorage role 异常：{role}"

        # 步骤五：截图留存证据并附加到 Allure 报告
        with allure.step("登录成功截图"):
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            shot_path = str(EVIDENCE_DIR / "ui_login_success.png")
            login_page.screenshot(shot_path)
            allure.attach.file(
                shot_path,
                name="登录成功截图",
                attachment_type=allure.attachment_type.PNG,
            )

    @allure.title("UI登录：错误密码展示错误提示且不跳转")
    @pytest.mark.ui
    @pytest.mark.regression
    def test_login_wrong_password(self, ui_page, ui_base_url):
        """验证错误密码登录时页面展示错误提示且不跳转。"""
        login_page = LoginPage(ui_page)

        # 步骤一：打开登录页并录入错误密码
        with allure.step("打开登录页并输入错误密码"):
            login_page.open(ui_base_url)
            login_page.login(USERNAME, "wrong-password")

        # 步骤二：断言错误提示可见
        with allure.step("断言页面展示错误提示"):
            # 错误时前端 handleLogin 的 catch 分支写入 errorMsg 并渲染到 .error-message
            assert login_page.is_error_visible(timeout=5000), "错误提示元素未出现"
            error_text = login_page.get_error_message()
            assert "用户名或密码错误" in error_text, f"错误提示文案异常，实际：{error_text}"

        # 步骤三：断言仍停留在登录页
        with allure.step("断言未发生跳转"):
            assert LoginPage.ROLE_REDIRECT["TENANT"] not in login_page.get_current_url()