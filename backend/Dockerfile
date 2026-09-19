# ============================================================================
# backend/Dockerfile —— 公寓租赁管理系统后端（Spring Boot）镜像
#
# 构建方式（在项目根目录执行，由 docker-compose.yml 自动调用；也可单独构建）：
#   docker build -t apartment-backend ./backend
#
# 运行方式：
#   docker run -d --name apartment-backend -p 8080:8080 \
#     -e SPRING_DATASOURCE_URL="jdbc:mysql://<数据库主机>:3306/apartment_rental_db?useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&characterEncoding=utf8" \
#     -e SPRING_DATASOURCE_USERNAME=apartment \
#     -e SPRING_DATASOURCE_PASSWORD=123456 \
#     apartment-backend
#   （正常使用 docker compose up -d 即可，无需手动执行上面的命令）
#
# 多阶段构建说明：
#   阶段一 builder：用 Maven 镜像编译打包，产出可执行 jar（构建工具不进最终镜像）；
#   阶段二 runtime：只拷贝 jar 到轻量 JRE 镜像运行，镜像更小、攻击面更少。
#
# 关于 JDK 版本（重要，与后端 pom.xml 的差异记录）：
#   backend/pom.xml 中 <java.version>1.8</java.version>（源码级别为 Java 8），
#   但 .github/workflows/auto-test.yml 的 CI 使用的是 Java 17，且 CI 全绿。
#   为与 CI 环境保持一致（本地 Docker 复现 CI 才有意义），这里同样选用 JDK 17：
#   JDK 17 编译 source/target=1.8 是合规的，Spring Boot 2.7.18 也支持在 Java 17 上运行。
# ============================================================================

# ---------------------------------------------------------------------------
# 阶段一：构建阶段 —— 编译源码并打包成可执行 jar
# ---------------------------------------------------------------------------
FROM maven:3.9-eclipse-temurin-17 AS builder

# 构建目录
WORKDIR /build

# 先只拷贝 pom.xml 并预下载依赖：
# 这样只要 pom.xml 没变，后续修改 Java 源码时可以直接复用这一层缓存，避免重复下载依赖。
# 末尾的 || true 说明：这一步只是「预热依赖缓存」，即使个别插件没被 go-offline 覆盖到也不影响结果，
# 缺失的部分会在下面的 mvn package 中自动补齐；真正的构建失败仍会在 package 阶段明确报错。
COPY pom.xml .
RUN mvn -B -DskipTests dependency:go-offline || true

# 再拷贝源码进行编译打包
# -DskipTests：后端单元测试由 CI 的 pytest 流程负责，镜像构建阶段无需重复执行
COPY src ./src
RUN mvn -B -DskipTests package

# ---------------------------------------------------------------------------
# 阶段二：运行阶段 —— 仅携带 JRE 与 jar，体积更小
# ---------------------------------------------------------------------------
FROM eclipse-temurin:17-jre-alpine

# curl 仅用于 docker-compose 中的容器健康检查（探测 /api/auth/login）
# alpine 基础镜像默认不带 curl，这里显式安装
RUN apk add --no-cache curl

# 运行目录：jar 与上传目录（upload.path: uploads）都以此为基准
WORKDIR /app

# 从构建阶段拷贝可执行 jar（spring-boot-maven-plugin 打包出的主 jar）
# 注意：target 下还有 xxx.jar.original，它不以 .jar 结尾，不会被该通配符匹配
COPY --from=builder /build/target/*.jar app.jar

# 对外暴露后端端口（与 application.yml 的 server.port 一致）
EXPOSE 8080

# 数据库连接等敏感/易变配置不在镜像里写死，统一由 docker-compose 以环境变量注入：
#   SPRING_DATASOURCE_URL / SPRING_DATASOURCE_USERNAME / SPRING_DATASOURCE_PASSWORD
# Spring Boot 会自动把上述环境变量绑定到 spring.datasource.* 配置项上。
# 启动命令：java -jar
ENTRYPOINT ["java", "-jar", "app.jar"]