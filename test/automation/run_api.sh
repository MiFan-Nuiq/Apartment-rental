#!/usr/bin/env bash
# ============================================================================
# run_api.sh —— 一键清理并执行全部接口测试，成功后生成 Allure 报告
#
# 用途：
#   只跑接口层用例（apis/ + testcases 中带 api marker 的用例），
#   用于在不启动前端的情况下快速验证后端接口是否正常。
#
# 用法：
#   ./run_api.sh                # 在脚本所在目录执行（需先 chmod +x run_api.sh）
#   bash run_api.sh             # 不想加可执行权限时的等价写法
#
# 前置条件：
#   1) 后端服务已启动：Spring Boot，端口 8080（唯一必需的服务）
#   2) MySQL 已启动（带 db marker 的用例需要直连数据库校验）
#      —— 本脚本不选 ui marker，因此**不需要启动前端 5173**，
#         这也是它比 run_smoke.sh 更快、更适合在后端改动后快速回归的原因
#   3) Allure CLI 已安装并在 PATH 中（仅"生成报告"这一步需要；未安装时脚本会提示并跳过）
#
# 执行流程：
#   ① 调用同目录的 clean.sh 清理旧产物
#   ② pytest -m api --alluredir=./allure-results
#   ③ 退出码为 0  -> 打印"接口测试通过"，并 allure generate 生成 HTML 报告
#      退出码非 0 -> 打印"接口测试失败，请查看日志"，保留 allure-results 便于排查
#
# 退出码：
#   直接透传 pytest 的退出码（0 表示全部通过），便于在 CI 中串联使用
# ============================================================================

# -u：未定义变量报错，防止变量名拼错
# -o pipefail：管道任一环节失败即失败
# 注意：刻意不使用 set -e —— 需要显式捕获 pytest 的非 0 退出码做分支判断，
#      开启后 pytest 一失败脚本就退出，失败处理逻辑将不会执行
set -uo pipefail

# 切换到脚本所在目录：保证 clean.sh、pytest.ini、allure-results 都定位到 test/automation
cd "$(dirname "$0")"

echo "=========================================="
echo "步骤 1/3：清理旧产物"
echo "=========================================="
# 调用同目录的 clean.sh；用 bash 显式执行，避免因缺少可执行权限而失败
bash ./clean.sh

echo ""
echo "=========================================="
echo "步骤 2/3：执行接口测试（pytest -m api）"
echo "提示：本脚本不需要前端 5173，只需后端 8080 已启动"
echo "=========================================="
# --alluredir 显式指定结果目录，与 pytest.ini 中的 addopts 保持一致（命令行参数优先）
pytest -m api --alluredir=./allure-results
# 立即保存退出码：任何后续命令都会覆盖 $?，必须先存到变量里
PYTEST_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ "$PYTEST_EXIT_CODE" -eq 0 ]; then
  # ---------- 成功分支 ----------
  echo "接口测试通过"
  echo "=========================================="

  # 生成 Allure 静态 HTML 报告；--clean 先清空输出目录，避免残留上一次的文件
  if command -v allure >/dev/null 2>&1; then
    echo "正在生成 Allure 报告..."
    allure generate ./allure-results -o ./allure-report --clean
    echo "Allure 报告已生成：./allure-report/index.html"
    echo "查看方式：allure open ./allure-report    或用 allure serve ./allure-results"
  else
    # 未安装 Allure CLI 不算测试失败，只提示如何补装
    echo "未检测到 allure 命令，跳过报告生成（测试结果本身已通过）"
    echo "安装后可执行：allure generate ./allure-results -o ./allure-report --clean"
  fi
else
  # ---------- 失败分支 ----------
  echo "接口测试失败，请查看日志"
  echo "pytest 退出码：${PYTEST_EXIT_CODE}"
  echo "=========================================="
  # 刻意不生成报告、也不清理 allure-results：保留原始结果便于排查
  echo "已保留 ./allure-results 原始结果，便于排查："
  echo "  1) allure serve ./allure-results          # 打开报告看失败详情"
  echo "  2) pytest -m api --lf                     # 只重跑上次失败的用例"
  echo "  3) 确认后端 8080 是否已启动：curl http://localhost:8080/api/apartments"
fi

# 透传 pytest 退出码：让调用方（人或 CI）能据此判断本次执行是否成功
exit "$PYTEST_EXIT_CODE"