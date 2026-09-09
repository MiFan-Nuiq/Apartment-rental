# -*- coding: utf-8 -*-

"""

===== 运行记录 =====
最近一次执行时间：2026-09-10
执行结果：2 passed in 2.04s（全部通过）
===== 运行记录结束 =====

公寓租赁管理系统 —— 登录页 UI 自动化测试（Playwright）
场景：输入账号 -> 输入密码 -> 点击登录 -> 断言跳转成功

页面定位依据（对应前端源码 frontend/src/views/Login.vue）：
  - 用户名输入框  <input type="text"  placeholder="请输入用户名">
  - 密码输入框    <input type="password" placeholder="••••••••">
  - 登录按钮      button.submit-btn
  - 登录成功提示  ElMessage：文本"登录成功"
  - 跳转规则      redirectByRole()：
                    ADMIN   -> /admin/dashboard
                    LANDLORD-> /landlord/apartments
                    TENANT  -> /tenant/apartments
  - 登录后写入 localStorage：token / username / realName / role / userId

运行准备：
  pip install pytest-playwright
  playwright install chromium
运行方式：
  pytest ui_test_login.py -v
"""

import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5173"   # 前端 Vite 开发服务器地址
USERNAME = "tenant"
PASSWORD = "123456"
# 登录成功后的期望路由：由角色决定，tenant 对应 /tenant/apartments
EXPECT_REDIRECT = "/tenant/apartments"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)   # 需可视化观察时可设 headless=True
        yield b
        b.close()


def test_login_success(browser):
    page = browser.new_page()
    page.goto(BASE_URL + "/login")
    expect(page).to_have_title("公寓租赁管理系统")  # 若标题不确定可注释该断言

    # 1. 输入账号
    page.locator('input[placeholder="请输入用户名"]').fill(USERNAME)
    # 2. 输入密码
    page.locator('input[placeholder="••••••••"]').fill(PASSWORD)
    # 3. 点击登录
    page.locator("button.submit-btn", has_text="登录").click()

    # 4. 断言跳转成功：URL 进入角色对应主页
    page.wait_for_url("**" + EXPECT_REDIRECT, timeout=10000)
    assert EXPECT_REDIRECT in page.url, f"登录后未跳转到 {EXPECT_REDIRECT}，当前：{page.url}"

    # 5. 断言登录态已写入 localStorage
    token = page.evaluate("localStorage.getItem('token')")
    role = page.evaluate("localStorage.getItem('role')")
    assert token, "localStorage 中未写入 token"
    assert role == "TENANT", f"localStorage role 异常：{role}"

    page.close()


def test_login_wrong_password(browser):
    """错误密码登录应在页面展示错误提示，且不跳转。"""
    page = browser.new_page()
    page.goto(BASE_URL + "/login")

    page.locator('input[placeholder="请输入用户名"]').fill(USERNAME)
    page.locator('input[placeholder="••••••••"]').fill("wrong-password")
    page.locator("button.submit-btn", has_text="登录").click()

    # 错误时前端 handleLogin 的 catch 分支写入 errorMsg「用户名或密码错误」并渲染到 .error-message
    error = page.locator(".error-message")
    expect(error).to_be_visible(timeout=5000)
    assert "用户名或密码错误" in error.inner_text()

    # 仍停留在登录页，未发生跳转
    assert EXPECT_REDIRECT not in page.url
    page.close()