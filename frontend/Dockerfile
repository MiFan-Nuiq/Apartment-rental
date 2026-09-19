# ============================================================================
# frontend/Dockerfile —— 公寓租赁管理系统前端（Vue3 + Vite）镜像
#
# 用途：
#   为 **本地测试环境** 提供前端服务，运行的是 Vite dev server（开发服务器），
#   端口 5173，与本地直接执行 npm run dev 的效果一致。
#   选用 dev server 而不是生产构建的原因：
#     test/automation/ 下的 UI 用例（Playwright）访问的是 http://localhost:5173，
#     且 dev server 支持 /api 反向代理，能直接把接口请求转发给后端容器，
#     与本地开发时的前端行为完全一致，测试结果才具备可比性。
#
# 构建方式（由 docker-compose.yml 自动调用；也可单独构建）：
#   docker build -t apartment-frontend ./frontend
#
# 运行方式：
#   docker run -d --name apartment-frontend -p 5173:5173 \
#     -e VITE_API_TARGET=http://backend:8080 apartment-frontend
#   （正常使用 docker compose up -d 即可，无需手动执行上面的命令）
#
# 多阶段构建说明：
#   阶段一 deps：用 Node 镜像安装依赖（含 devDependencies，vite 在其中）；
#   阶段二 runtime：只携带依赖与源码运行 dev server，不把 npm 缓存带进最终镜像。
#
# 若将来需要「生产环境」镜像（Nginx 暴露 80 端口），替换思路：
#   阶段一改为 `npm run build` 产出 dist/，阶段二用 `nginx:alpine`，
#   把 dist/ 拷到 /usr/share/nginx/html，并在 nginx.conf 中配置 /api 反向代理到后端。
#   本项目测试场景不需要，故默认采用开发环境方案。
# ============================================================================

# ---------------------------------------------------------------------------
# 阶段一：依赖安装阶段 —— 安装 node_modules
# ---------------------------------------------------------------------------
FROM node:20-alpine AS deps

WORKDIR /app

# npm 源（registry）：
#   默认使用国内镜像 registry.npmmirror.com —— 与开发机 `npm config get registry` 的配置一致。
#   原因：在容器内直接访问官方源 registry.npmjs.org 时，npm 并发下载依赖容易出现
#   ECONNRESET（网络重置）导致构建失败；国内镜像更稳定、速度也更快。
#   如需切回官方源，构建时覆盖该参数即可：
#     docker compose build --build-arg NPM_REGISTRY=https://registry.npmjs.org frontend
ARG NPM_REGISTRY=https://registry.npmmirror.com

# 先只拷贝依赖清单：
# 只要依赖没变，后续修改源代码时可直接复用这一层缓存，免去重复安装
COPY package.json package-lock.json ./

# 安装全部依赖（含 devDependencies），与 CI 的安装方式保持一致：
#   --registry      ：使用上面的 npm 源
#   --include=dev   ：显式包含 devDependencies，确保 vite / @vitejs/plugin-vue 一定被装上
#   --fetch-retries ：网络抖动时多重试几次，避免偶发 ECONNRESET 直接让构建失败
#   --no-audit --no-fund：关闭安全审计与资助提示，加快安装、保持日志干净
# 说明：这里刻意不用 npm ci，而是沿用 CI 已验证可用的 npm install，
#       避免 Windows 上生成的 package-lock.json 在 Linux 下解析出平台差异问题。
RUN npm install --registry=${NPM_REGISTRY} --include=dev --fetch-retries=5 --no-audit --no-fund

# ---------------------------------------------------------------------------
# 阶段二：运行阶段 —— 运行 Vite dev server，暴露 5173
# ---------------------------------------------------------------------------
FROM node:20-alpine

WORKDIR /app

# 复用阶段一装好的依赖，避免在运行镜像里再装一次
COPY --from=deps /app/node_modules ./node_modules

# 拷贝前端源码与配置（node_modules 已在 .dockerignore 中排除，不会被覆盖）
COPY . .

# 对外暴露前端端口（与 vite.config.js 的 server.port 一致）
EXPOSE 5173

# API 代理目标（在 vite.config.js 中读取）：
#   - 本地开发：默认 http://localhost:8080
#   - Docker：由 docker-compose 覆盖为 http://backend:8080
#     （容器内的 localhost 指向容器自身，必须用 compose 的服务名 backend 才能连到后端容器）
ENV VITE_API_TARGET=http://localhost:8080

# 启动 Vite dev server。
# 直接调用 node 执行 vite 入口文件，而不是 npm run dev / npx：
#   npm run dev 走 node_modules/.bin/vite 的 shim，遇到权限位问题会报
#   "sh: 1: vite: Permission denied"（CI 曾出现过该故障），直接跑 js 入口最稳。
#   --host 0.0.0.0   允许容器外访问
#   --port 5173      固定端口，与端口映射、UI 用例地址保持一致
#   --strictPort     端口被占用时直接失败，避免 Vite 自动换端口后 UI 用例连不上
CMD ["node", "node_modules/vite/bin/vite.js", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]