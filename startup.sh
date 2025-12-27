#!/bin/bash
cd /home/site/wwwroot

# 1. 动态寻找Python（最可靠的方式）
PYTHON_CMD=""
for cmd in python3 python3.9 python3.10; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$(command -v $cmd)
        echo "[INFO] 动态找到Python: $PYTHON_CMD"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] 未找到Python，退出。"
    exit 1
fi

# 2. 使用之前验证绝对可用的Gunicorn绝对路径
GUNICORN_CMD="/home/.local/bin/gunicorn"

echo "=== 最终启动配置 ==="
echo "Python: $PYTHON_CMD"
echo "Gunicorn: $GUNICORN_CMD"
echo "端口: 8000 (已固定)"
echo "==================="

# 3. 安装依赖（使用找到的Python）
$PYTHON_CMD -m pip install --user -r requirements.txt 2>&1 | tail -5

# 4. 【关键】直接绑定到8000端口，无视$PORT变量，彻底避免冲突
exec $GUNICORN_CMD --bind=0.0.0.0:8000 \
    --workers=2 \
    --timeout=120 \
    --access-logfile - \
    --error-logfile - \
    lesson_13_fixed:app