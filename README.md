# 🚀 自动化亚马逊选品分析系统 (优化版)

一个基于 Python Flask 开发的 Web 应用，用于自动化分析亚马逊产品数据，通过评分算法筛选高潜力商品，帮助决策。

## ✨ 核心功能
- **CSV数据导入**：支持上传包含价格、销量的CSV文件，自动清洗数据（如处理`$3.99`格式）。
- **智能评分算法**：综合ROI、月销量、竞争程度、评价等因素计算产品潜力分。
- **可视化仪表板**：展示核心数据统计、品类分布与利润分析图表。
- **自动化报告**：支持定时生成分析报告，并可模拟邮件发送。
- **用户系统**：完整的用户注册、登录及数据隔离管理。

## 🖥️ 在线演示
- **应用地址**：[https://myselect-app-new-c6dhbngjddhheugw.eastasia-01.azurewebsites.net](https://myselect-app-new-c6dhbngjddhheugw.eastasia-01.azurewebsites.net)
- **测试账号**: `demo` / `demo123`

## 🔧 本地安装与运行
1.  **克隆项目**
    ```bash
    git clone https://github.com/silinli007/my_azure_app.git
    cd my_azure_app
    ```
2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```
3.  **运行应用**
    ```bash
    python lesson_13_fixed.py
    ```
4.  **访问应用**：打开浏览器，访问 `http://127.0.0.1:5010`

## ☁️ 部署到 Azure
1.  在 Azure 门户创建 **App Service**（推荐 B1 基本层）。
2.  开启 **“始终在线 (Always On)”** 功能。
3.  通过部署中心连接你的 GitHub 仓库，或使用 Git 直接推送部署。

## 📁 项目结构

my_azure_app/
├── lesson_13_fixed.py # 主应用文件
├── requirements.txt # Python 依赖清单
├── templates_automation_optimized/ # 网页模板
├── instance/ # 本地数据库目录 (生产环境请忽略)
└── README.md # 本文档

## 🧠 技术栈
- **后端**：Python, Flask, SQLAlchemy, Pandas
- **前端**：HTML, CSS, JavaScript, Jinja2
- **数据库**：SQLite (开发) / 可连接 Azure Database (生产)
- **部署**：Azure App Service
- **版本控制**：Git & GitHub

## 📄 许可证
本项目采用 MIT 许可证。