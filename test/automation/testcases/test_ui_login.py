# -*- coding: utf-8 -*-
"""
登录页 UI 自动化测试用例（Playwright）

场景：输入账号 -> 输入密码 -> 点击登录 -> 断言跳转成功

说明：
    - 保持原 test/automation/ui_test_login.py 的 Playwright 写法，仅做 pytest 化 + Allure 注解；
    - 页面定位依据（frontend/src/views/Login.vue）：
        用户名输入框  <input type="text"  placeholder="请输入用户名">
        密码输入框    <input type="password" placeholder="••••••••">
        登录按钮      button.submit-btn
        跳转规则      redirectByRole()：TENANT -> /tenant/apartments
        登录后写入 localStorage：token / role 等

依赖：
    - pip install playwright pytest-playwright（见 requirements.txt）
    - playwright install chromium
    - 前端服务需已启动（Vite，参见 README）
    - 若未安装 playwright，本模块会在收集阶段被自动跳过（详见文件末尾 importorskip）
"""

import os
from pathlib import Path

import allure
import pytest

# 若未安装 playwright，则跳过整个模块，避免阻塞纯接口用例的收集与执行
playwright_installed = pytest.importorskip("playwright", reason="未安装 playwright，跳过 UI 用例")

from playwright.sync_api import expect, sync_playwright  # noqa: E402

# 前端基础地址取自 conftest 环境变量（默认 http://localhost:5173）
from conftest import PASSWORD, UI_BASE_URL, USERNAME  # noqa: E402

# 登录成功后的期望路由：由角色决定，tenant 对应 /tenant/apartments
EXPECT_REDIRECT = "/tenant/apartments"

# 截图输出目录：test/evidence（相对本文件向上两级）
EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "evidence"


@allure.feature("UI 登录流程")
class TestUILogin:
    """登录页 UI 自动化测试类。"""

    @allure.title("UI登录：正确账号密码登录成功并跳转")
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_login_success(self, browser, ui_base_url):
        """验证输入正确账号密码点击登录后成功跳转至租户主页。"""
        page = browser.new_page()
        try:
            # 步骤一：打开登录页
            with allure.step("打开登录页面"):
                page.goto(ui_base_url + "/login")
                expect(page).to_have_title("公寓租赁管理系统")  # 若标题不确定可注释该断言

            # 步骤二：输入账号密码并点击登录
            with allure.step("输入账号、密码并点击登录"):
                page.locator('input[placeholder="请输入用户名"]').fill(USERNAME)
                page.locator('input[placeholder="••••••••"]').fill(PASSWORD)
                page.locator("button.submit-btn", has_text="登录").click()

            # 步骤三：断言跳转成功
            with allure.step("断言跳转至租户主页"):
                page.wait_for_url("**" + EXPECT_REDIRECT, timeout=10000)
                assert EXPECT_REDIRECT in page.url, f"登录后未跳转到 {EXPECT_REDIRECT}，当前：{page.url}"

            # 步骤四：断言登录态写入 localStorage
            with allure.step("断言 localStorage 已写入登录态"):
                token = page.evaluate("localStorage.getItem('token')")
                role = page.evaluate("localStorage.getItem('role')")
                assert token, "localStorage 中未写入 token"
                assert role == "TENANT", f"localStorage role 异常：{role}"

            # 步骤五：截图留存证据
            with allure.step("登录成功截图"):
                # 保存到 test/evidence 并附加到 Allure 报告
                EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
                shot_path = str(EVIDENCE_DIR / "ui_login_success.png")
                page.screenshot(path=shot_path)
                allure.attach.file(
                    shot_path,
                    name="登录成功截图",
                    attachment_type=allure.attachment_type.PNG,
                )
        finally:
            page.close()

    @allure.title("UI登录：错误密码展示错误提示且不跳转")
    @pytest.mark.ui
    @pytest.mark.regression
    def test_login_wrong_password(self, browser, ui_base_url):
        """验证错误密码登录时页面展示错误提示且不跳转。"""
        page = browser.new_page()
        try:
            # 步骤一：打开登录页并录入错误密码
            with allure.step("打开登录页并输入错误密码"):
                page.goto(ui_base_url + "/login")
                page.locator('input[placeholder="请输入用户名"]').fill(USERNAME)
                page.locator('input[placeholder="••••••••"]').fill("wrong-password")
                page.locator("button.submit-btn", has_text="登录").click()

            # 步骤二：断言错误提示可见
            with allure.step("断言页面展示错误提示"):
                # 错误时前端 handleLogin 的 catch 分支写入 errorMsg 并渲染到 .error-message
                error = page.locator(".error-message")
                expect(error).to_be_visible(timeout=5000)
                assert "用户名或密码错误" in error.inner_text()

            # 步骤三：断言仍停留在登录页
            with allure.step("断言未发生跳转"):
                assert EXPECT_REDIRECT not in page.url
        finally:
            page.close()


@pytest.fixture(scope="module")
def browser():
    """module 级 fixture：启动一个 Playwright 浏览器实例，供本模块全部 UI 用例复用。"""
    with sync_playwright() as p:
        # headless=False 便于可视化观察；CI 环境可改为 True
        b = p.chromium.launch(headless=os.getenv("HEADLESS", "false").lower() == "true")
        yield b
        b.close()