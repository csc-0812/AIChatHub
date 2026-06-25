#!/bin/bash
# ============================================
# AIChatHub 镜像构建 & 容器备份脚本 (Linux/Mac/WSL)
# 用法: bash scripts/build-image.sh
# 输出: build/planaskdemo-backup-YYYYMMDD-HHmmss.tar.gz
# ============================================
set -e

PROJECT_NAME="planaskdemo"
COMPOSE_FILE="docker/docker-compose.yml"
OUTDIR="${OUTDIR:-build}"
TAG_SUFFIX="${1:-}"

if [ -n "$TAG_SUFFIX" ]; then
    ARCHIVE_NAME="${PROJECT_NAME}-backup-${TAG_SUFFIX}.tar.gz"
else
    TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
    ARCHIVE_NAME="${PROJECT_NAME}-backup-${TIMESTAMP}.tar.gz"
fi

echo "============================================"
echo "  AIChatHub 镜像构建 & 容器备份脚本"
echo "============================================"
echo ""
echo "  项目名称: $PROJECT_NAME"
echo "  输出目录: $OUTDIR"
echo "  备份文件: $ARCHIVE_NAME"
echo ""

# ---------- 1. 环境检查 ----------
echo "[1/5] 检查 Docker 环境..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   下载地址: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null 2>&1; then
    echo "❌ Docker Compose 不可用"
    exit 1
fi

echo "  ✓ Docker $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
echo "  ✓ Docker Compose $(docker compose version --short)"
echo ""

# ---------- 2. 准备输出目录 ----------
echo "[2/5] 准备输出目录..."
mkdir -p "$OUTDIR"
echo "  ✓ 输出目录: $OUTDIR"
echo ""

# ---------- 3. 构建镜像 ----------
echo "[3/5] 构建 Docker 镜像..."
docker compose -f "$COMPOSE_FILE" build --parallel backend frontend
echo "  ✓ 镜像构建完成"
echo ""

# ---------- 4. 导出镜像 ----------
echo "[4/5] 导出镜像为 tar.gz..."

BACKEND_IMAGE="${PROJECT_NAME}-backend"
FRONTEND_IMAGE="${PROJECT_NAME}-frontend"
TEMP_DIR="${OUTDIR}/temp_${TIMESTAMP:-$(date +"%Y%m%d-%H%M%S")}"

# 验证镜像是否存在
if ! docker image inspect "$BACKEND_IMAGE" &> /dev/null; then
    echo "❌ 未找到后端镜像: $BACKEND_IMAGE"
    echo "   请先执行 docker compose -f $COMPOSE_FILE build"
    exit 1
fi
if ! docker image inspect "$FRONTEND_IMAGE" &> /dev/null; then
    echo "❌ 未找到前端镜像: $FRONTEND_IMAGE"
    echo "   请先执行 docker compose -f $COMPOSE_FILE build"
    exit 1
fi

echo "  → 后端镜像: $BACKEND_IMAGE"
echo "  → 前端镜像: $FRONTEND_IMAGE"

# 创建临时目录
mkdir -p "$TEMP_DIR"

# 分别导出镜像
echo "  → 导出后端镜像..."
docker save "$BACKEND_IMAGE" -o "$TEMP_DIR/backend.tar"

echo "  → 导出前端镜像..."
docker save "$FRONTEND_IMAGE" -o "$TEMP_DIR/frontend.tar"

# 复制部署所需文件
echo "  → 复制部署配置文件..."
cp "config/config.yaml" "$TEMP_DIR/config.yaml"

# 生成部署用 docker-compose.yml（将 build: 替换为 image:，避免重新构建）
echo "  → 生成部署 compose 文件（去除 build 指令）..."
awk '
/^    build:$/                   { in_build=1; next }
in_build && /^(      context|      dockerfile):/ { next }
                                 { in_build=0 }
/^    container_name: planaskdemo-backend$/  { print "    image: planaskdemo-backend" }
/^    container_name: planaskdemo-frontend$/ { print "    image: planaskdemo-frontend" }
                                 { print }
' "$COMPOSE_FILE" > "$TEMP_DIR/docker-compose.yml"

# 创建恢复说明
cat > "$TEMP_DIR/README.txt" << 'EOF'
# AIChatHub 容器备份恢复说明
#
# 恢复步骤:
# 1. 解压备份:
#    tar -xzf <备份文件>.tar.gz
#
# 2. 导入镜像:
#    docker load -i backend.tar
#    docker load -i frontend.tar
#
# 3. 启动服务（在解压目录下）:
#    docker compose -f docker-compose.yml up -d
#
# 或者一步恢复:
#    tar -xzf <备份文件>.tar.gz && cd temp_* && \
#    docker load -i backend.tar && docker load -i frontend.tar && \
#    docker compose -f docker-compose.yml up -d
EOF

# 添加到 tar.gz
echo "  → 打包为 tar.gz..."
cd "$OUTDIR"
tar -czf "$ARCHIVE_NAME" "$(basename "$TEMP_DIR")"
cd - > /dev/null

# 清理临时目录
rm -rf "$TEMP_DIR"

echo "  ✓ 镜像导出完成"
echo ""

# ---------- 5. 输出结果 ----------
FILE_SIZE=$(du -h "$OUTDIR/$ARCHIVE_NAME" | cut -f1)

echo "============================================"
echo "  ✅ 镜像备份完成!"
echo "============================================"
echo ""
echo "  备份文件: $OUTDIR/$ARCHIVE_NAME"
echo "  文件大小: $FILE_SIZE"
echo ""
echo "  恢复命令:"
echo "    tar -xzf $OUTDIR/$ARCHIVE_NAME -C <目标目录>"
echo "    docker load -i <目标目录>/backend.tar"
echo "    docker load -i <目标目录>/frontend.tar"
echo "    docker compose -f <目标目录>/docker-compose.yml up -d"
echo ""
