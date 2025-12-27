#!/bin/bash
cd /home/site/wwwroot
# 1. 强制安装依赖
python3 -m pip install --user --no-cache-dir --no-warn-script-location -r requirements.txt > /home/site/pip_install.log 2>&1
# 2. 以最简方式启动应用
exec python3 -m gunicorn --bind 0.0.0.0:8000 --workers 1 --timeout 300 --preload --access-logfile - --error-logfile - lesson_13_fixed:app