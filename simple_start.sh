#!/bin/bash
cd /home/site/wwwroot
echo "=== 启动应用 ==="
python3 -m pip install --user -r requirements.txt
exec gunicorn --bind 0.0.0.0:8000 --workers 2 lesson_13_fixed:app