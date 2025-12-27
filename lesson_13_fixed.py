print("🚀 路径3 - 自动化系统开发（优化版）")

# ===== 缓存优化添加 =====
import functools
import time
import hashlib

class PerformanceCache:
    """性能缓存系统"""
    def __init__(self):
        self._cache = {}
    
    def get(self, key):
        if key in self._cache:
            data = self._cache[key]
            if time.time() < data['expires']:
                return data['value']
        return None
    
    def set(self, key, value, ttl=300):
        self._cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }

performance_cache = PerformanceCache()

def cached(ttl=300):
    """缓存装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [func.__module__, func.__name__]
            if args:
                start_index = 1 if args and hasattr(args[0], '__class__') else 0
                key_parts.extend(str(arg) for arg in args[start_index:start_index+2])
            cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            
            # 检查缓存
            cached_result = performance_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存
            result = func(*args, **kwargs)
            performance_cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
# ===== 缓存优化结束 =====

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import io
import base64
from datetime import datetime, timezone, timedelta
import json
from sqlalchemy import or_, text, func
import secrets
import time
from functools import lru_cache
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import threading
from concurrent.futures import ThreadPoolExecutor
import glob

# 尝试导入APScheduler，如果失败使用备用方案
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
    print("✅ APScheduler 可用")
except ImportError:
    APSCHEDULER_AVAILABLE = False
    print("⚠️  APScheduler 不可用，使用简单定时器")

# 尝试导入flask-mail，如果失败使用备用方案
try:
    from flask_mail import Mail, Message
    FLASK_MAIL_AVAILABLE = True
    print("✅ Flask-Mail 可用")
except ImportError:
    FLASK_MAIL_AVAILABLE = False
    print("⚠️  Flask-Mail 不可用，使用模拟邮件发送")

# 配置中文字体
try:
    font_path = 'C:/Windows/Fonts/msyh.ttc' if os.path.exists('C:/Windows/Fonts/msyh.ttc') else None
    if font_path:
        font_prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams['font.sans-serif'] = [font_prop.get_name(), 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        print("✅ 中文字体设置成功")
except Exception as e:
    print(f"⚠️  字体设置失败: {e}")

app = Flask(__name__, template_folder='templates_automation_optimized')

# 生产环境配置
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'automation-system-' + secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///products_automation_optimized.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 邮件配置（使用环境变量或默认值）
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'test@example.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'password'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@example.com'

app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

db = SQLAlchemy(app)

# 如果Flask-Mail可用则初始化
if FLASK_MAIL_AVAILABLE:
    mail = Mail(app)
else:
    mail = None

# 配置日志系统
def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler(
        'logs/automation_optimized.log', 
        maxBytes=10240, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

# 线程池执行器（用于后台任务）
executor = ThreadPoolExecutor(max_workers=4)

# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    receive_notifications = db.Column(db.Boolean, default=True)
    products = db.relationship('Product', backref='owner', lazy=True)
    reports = db.relationship('Report', backref='owner', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    estimated_cost = db.Column(db.Float, nullable=False)
    monthly_sales = db.Column(db.Integer, nullable=False)
    competition_level = db.Column(db.String(20), nullable=False)
    review_rating = db.Column(db.Float, default=4.0)
    product_url = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        estimated_profit = self.current_price - self.estimated_cost
        estimated_roi = (estimated_profit / self.estimated_cost) * 100 if self.estimated_cost > 0 else 0
        
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'current_price': self.current_price,
            'estimated_cost': self.estimated_cost,
            'monthly_sales': self.monthly_sales,
            'competition_level': self.competition_level,
            'review_rating': self.review_rating,
            'product_url': self.product_url,
            'estimated_profit': round(estimated_profit, 2),
            'estimated_roi': round(estimated_roi, 1),
            'revenue_potential': self.current_price * self.monthly_sales,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M')
        }

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly
    report_data = db.Column(db.Text)  # JSON数据
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sent_via_email = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)

# 登录装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '需要登录'}), 401 if request.is_json else redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 创建数据库表
with app.app_context():
    db.create_all()

# 简单的定时任务管理器（如果APScheduler不可用）
class SimpleScheduler:
    def __init__(self):
        self.tasks = []
        self.running = False
        self.thread = None
        self.task_history = []
    
    def add_job(self, func, trigger_type='interval', **kwargs):
        """添加定时任务"""
        task_id = f"task_{len(self.tasks) + 1}"
        task = {
            'id': task_id,
            'func': func,
            'trigger_type': trigger_type,
            'kwargs': kwargs,
            'last_run': None,
            'next_run': None,
            'enabled': True
        }
        self.tasks.append(task)
        self._calculate_next_run(task)
        return task_id
    
    def _calculate_next_run(self, task):
        """计算下次运行时间"""
        now = datetime.now(timezone.utc)
        if task['trigger_type'] == 'interval':
            interval = task['kwargs'].get('minutes', 5)
            if task['last_run']:
                task['next_run'] = task['last_run'] + timedelta(minutes=interval)
            else:
                task['next_run'] = now + timedelta(minutes=interval)
        elif task['trigger_type'] == 'cron':
            hour = task['kwargs'].get('hour', 9)
            minute = task['kwargs'].get('minute', 0)
            today = now.date()
            next_run = datetime(today.year, today.month, today.day, hour, minute, tzinfo=timezone.utc)
            if next_run <= now:
                next_run += timedelta(days=1)
            task['next_run'] = next_run
    
    def start(self):
        """启动定时任务"""
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        print("✅ 优化版定时器启动")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self.running:
            now = datetime.now(timezone.utc)
            
            for task in self.tasks:
                if not task['enabled']:
                    continue
                    
                if task['next_run'] and now >= task['next_run']:
                    try:
                        start_time = time.time()
                        task['func']()
                        execution_time = round(time.time() - start_time, 2)
                        
                        # 记录执行历史
                        self.task_history.append({
                            'task_id': task['id'],
                            'executed_at': now,
                            'execution_time': execution_time,
                            'status': 'success'
                        })
                        
                        task['last_run'] = now
                        self._calculate_next_run(task)
                        
                    except Exception as e:
                        app.logger.error(f"定时任务执行失败: {e}")
                        self.task_history.append({
                            'task_id': task['id'],
                            'executed_at': now,
                            'execution_time': 0,
                            'status': 'failed',
                            'error': str(e)
                        })
            
            # 保留最近100条执行记录
            if len(self.task_history) > 100:
                self.task_history = self.task_history[-100:]
                
            time.sleep(30)  # 每30秒检查一次
    
    def get_task_status(self):
        """获取任务状态"""
        status = []
        for task in self.tasks:
            status.append({
                'id': task['id'],
                'trigger_type': task['trigger_type'],
                'last_run': task['last_run'].strftime('%Y-%m-%d %H:%M:%S') if task['last_run'] else '从未运行',
                'next_run': task['next_run'].strftime('%Y-%m-%d %H:%M:%S') if task['next_run'] else '未知',
                'enabled': task['enabled']
            })
        return status
    
    def shutdown(self):
        """关闭调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

# 初始化任务调度器
if APSCHEDULER_AVAILABLE:
    scheduler = BackgroundScheduler()
    print("✅ 使用APScheduler")
else:
    scheduler = SimpleScheduler()
    print("✅ 使用优化版定时器")

class AutomationProductAnalyzer:
    def __init__(self, products):
        self.df = pd.DataFrame([p.to_dict() for p in products]) if products else pd.DataFrame()
        self.app_logger = app.logger
    
    @cached(ttl=600)  # 缓存10分钟
    def calculate_comprehensive_score(self, product_dict):
        """计算综合评分"""
        try:
            score = 0
            
            # ROI评分 (40%)
            roi = product_dict['estimated_roi']
            if roi > 70: score += 40
            elif roi > 50: score += 30
            elif roi > 30: score += 20
            else: score += 10
            
            # 销量评分 (30%)
            sales = product_dict['monthly_sales']
            if sales > 500: score += 30
            elif sales > 300: score += 22
            elif sales > 100: score += 15
            else: score += 8
            
            # 竞争评分 (20%)
            comp_mapping = {'低': 20, '中': 13, '高': 6}
            score += comp_mapping.get(product_dict['competition_level'], 10)
            
            # 评价评分 (10%)
            review_score = (product_dict['review_rating'] - 3) * 5
            score += max(0, min(10, review_score))
            
            return score
        except Exception as e:
            self.app_logger.error(f'计算综合评分失败: {e}')
            return 0
    
    def get_detailed_stats(self):
        """获取详细统计数据"""
        if self.df.empty:
            return {
                'total_products': 0,
                'avg_roi': 0,
                'avg_profit': 0,
                'total_revenue': 0,
                'high_value_count': 0,
                'top_product': '暂无数据',
                'category_breakdown': {},
                'roi_distribution': {},
                'trend_analysis': {},
                'profit_analysis': {},
                'sales_analysis': {}
            }
        
        total_products = len(self.df)
        avg_roi = float(self.df['estimated_roi'].mean())
        avg_profit = float(self.df['estimated_profit'].mean())
        total_revenue = float(self.df['revenue_potential'].sum())
        
        # 计算高价值产品数量
        high_value_count = 0
        for _, product in self.df.iterrows():
            score = self.calculate_comprehensive_score(product.to_dict())
            if score >= 70:
                high_value_count += 1
        
        # 找到最佳产品
        best_product_row = self.df.loc[self.df['estimated_roi'].idxmax()] if not self.df.empty else None
        best_product = best_product_row['name'] if best_product_row is not None else '暂无数据'
        
        # 类别分析
        category_breakdown = {}
        for category in self.df['category'].unique():
            category_data = self.df[self.df['category'] == category]
            category_breakdown[category] = {
                'count': len(category_data),
                'avg_roi': float(category_data['estimated_roi'].mean()),
                'avg_profit': float(category_data['estimated_profit'].mean()),
                'total_revenue': float(category_data['revenue_potential'].sum())
            }
        
        # ROI分布
        roi_ranges = ['0-50%', '50-100%', '100-150%', '150-200%', '200%+']
        roi_counts = [0, 0, 0, 0, 0]
        
        for roi in self.df['estimated_roi']:
            if roi <= 50:
                roi_counts[0] += 1
            elif roi <= 100:
                roi_counts[1] += 1
            elif roi <= 150:
                roi_counts[2] += 1
            elif roi <= 200:
                roi_counts[3] += 1
            else:
                roi_counts[4] += 1
        
        roi_distribution = dict(zip(roi_ranges, roi_counts))
        
        # 趋势分析
        trend_analysis = {
            'high_roi_products': len(self.df[self.df['estimated_roi'] > 100]),
            'high_sales_products': len(self.df[self.df['monthly_sales'] > 300]),
            'low_competition_products': len(self.df[self.df['competition_level'] == '低'])
        }
        
        # 利润分析
        profit_analysis = {
            'total_profit_potential': float((self.df['current_price'] - self.df['estimated_cost']).sum()),
            'avg_profit_margin': float(((self.df['current_price'] - self.df['estimated_cost']) / self.df['current_price'] * 100).mean()),
            'high_profit_products': len(self.df[self.df['estimated_profit'] > 20])
        }
        
        # 销售分析
        sales_analysis = {
            'total_monthly_sales': int(self.df['monthly_sales'].sum()),
            'avg_monthly_sales': float(self.df['monthly_sales'].mean()),
            'sales_velocity': '高' if self.df['monthly_sales'].mean() > 400 else '中' if self.df['monthly_sales'].mean() > 200 else '低'
        }
        
        return {
            'total_products': total_products,
            'avg_roi': round(avg_roi, 1),
            'avg_profit': round(avg_profit, 2),
            'total_revenue': round(total_revenue, 2),
            'high_value_count': high_value_count,
            'top_product': best_product,
            'category_breakdown': category_breakdown,
            'roi_distribution': roi_distribution,
            'trend_analysis': trend_analysis,
            'profit_analysis': profit_analysis,
            'sales_analysis': sales_analysis
        }

# 邮件服务类（优化版）
class EmailService:
    def __init__(self):
        self.app_logger = app.logger
    
    def send_report_email(self, user_email, username, report_data, report_chart):
        """发送报告邮件"""
        try:
            # 如果没有配置真实邮箱或Flask-Mail不可用，使用模拟发送
            if not FLASK_MAIL_AVAILABLE or not app.config['MAIL_USERNAME'] or app.config['MAIL_USERNAME'] == 'test@example.com':
                self.app_logger.info(f"模拟发送报告邮件给: {user_email}")
                print(f"📧 模拟发送邮件到: {user_email}")
                print(f"   主题: 选品分析报告 - {datetime.now(timezone.utc).strftime('%Y年%m月%d日')}")
                print(f"   内容: {report_data['total_products']}个产品, 平均ROI: {report_data['avg_roi']}%")
                print(f"   高价值产品: {report_data['high_value_count']}个, 总收益潜力: ${report_data['total_revenue']:.2f}")
                return True
            
            # 如果Flask-Mail可用且配置了真实邮箱，则实际发送
            if FLASK_MAIL_AVAILABLE:
                subject = f"📊 选品分析报告 - {datetime.now(timezone.utc).strftime('%Y年%m月%d日')}"
                
                html_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: linear-gradient(135deg, #3498db, #2c3e50); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                        .stat-card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .highlight {{ color: #e74c3c; font-weight: bold; }}
                        .footer {{ text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 0.9em; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚀 选品分析报告</h1>
                            <p>个性化数据分析 · 自动生成</p>
                        </div>
                        <div class="content">
                            <h2>亲爱的 {username}，</h2>
                            <p>这是您的选品分析系统自动生成的报告：</p>
                            
                            <div class="stat-card">
                                <h3>📈 核心数据统计</h3>
                                <p>总产品数量: <span class="highlight">{report_data['total_products']}</span></p>
                                <p>平均ROI率: <span class="highlight">{report_data['avg_roi']}%</span></p>
                                <p>平均单件利润: <span class="highlight">${report_data['avg_profit']}</span></p>
                                <p>高价值产品: <span class="highlight">{report_data['high_value_count']}</span> 个</p>
                            </div>
                            
                            <div class="stat-card">
                                <h3>🏆 最佳表现产品</h3>
                                <p>最佳ROI产品: <span class="highlight">{report_data['top_product']}</span></p>
                            </div>
                            
                            <p>登录系统查看更多详细分析：</p>
                            <p><a href="http://localhost:5009" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">查看完整报告</a></p>
                        </div>
                        <div class="footer">
                            <p>此邮件由选品分析系统自动发送，请勿回复。</p>
                            <p>发送时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                msg = Message(
                    subject=subject,
                    recipients=[user_email],
                    html=html_body
                )
                
                mail.send(msg)
                self.app_logger.info(f"报告邮件发送成功: {user_email}")
                return True
            
            return False
            
        except Exception as e:
            self.app_logger.error(f"发送邮件失败: {e}")
            print(f"❌ 邮件发送失败: {e}")
            return False

# 定时任务函数
def generate_daily_reports():
    """生成每日报告"""
    with app.app_context():
        try:
            app.logger.info("开始生成每日报告...")
            print("🔄 生成每日报告中...")
            
            users = User.query.filter_by(is_active=True, receive_notifications=True).all()
            email_service = EmailService()
            
            for user in users:
                user_products = Product.query.filter_by(user_id=user.id).all()
                
                if not user_products:
                    continue
                
                analyzer = AutomationProductAnalyzer(user_products)
                report_data = analyzer.get_detailed_stats()
                
                # 保存报告到数据库
                report = Report(
                    user_id=user.id,
                    report_type='daily',
                    report_data=json.dumps(report_data, ensure_ascii=False)
                )
                db.session.add(report)
                db.session.commit()
                
                # 发送邮件
                if email_service.send_report_email(user.email, user.username, report_data, ""):
                    report.sent_via_email = True
                    report.email_sent_at = datetime.now(timezone.utc)
                    db.session.commit()
                
                app.logger.info(f"用户 {user.username} 的每日报告生成完成")
                print(f"✅ {user.username} 的每日报告生成完成")
            
            app.logger.info("所有用户每日报告生成完成")
            print("✅ 所有用户每日报告生成完成")
            
        except Exception as e:
            app.logger.error(f"生成每日报告失败: {e}")
            print(f"❌ 生成每日报告失败: {e}")

def generate_weekly_summary():
    """生成每周总结"""
    with app.app_context():
        try:
            app.logger.info("开始生成每周总结...")
            print("🔄 生成每周总结中...")
            
            users = User.query.filter_by(is_active=True, receive_notifications=True).all()
            email_service = EmailService()
            
            for user in users:
                user_products = Product.query.filter_by(user_id=user.id).all()
                
                if not user_products:
                    continue
                
                analyzer = AutomationProductAnalyzer(user_products)
                report_data = analyzer.get_detailed_stats()
                
                # 添加周报特定分析
                report_data['weekly_insights'] = {
                    'trend_comparison': '本周表现稳定',
                    'recommendations': ['建议关注高ROI产品', '优化低销量产品策略']
                }
                
                # 保存报告到数据库
                report = Report(
                    user_id=user.id,
                    report_type='weekly',
                    report_data=json.dumps(report_data, ensure_ascii=False)
                )
                db.session.add(report)
                db.session.commit()
                
                # 发送邮件
                if email_service.send_report_email(user.email, user.username, report_data, ""):
                    report.sent_via_email = True
                    report.email_sent_at = datetime.now(timezone.utc)
                    db.session.commit()
                
                app.logger.info(f"用户 {user.username} 的周报生成完成")
                print(f"✅ {user.username} 的周报生成完成")
            
            app.logger.info("所有用户周报生成完成")
            print("✅ 所有用户周报生成完成")
            
        except Exception as e:
            app.logger.error(f"生成周报失败: {e}")
            print(f"❌ 生成周报失败: {e}")

def health_check_task():
    """健康检查任务"""
    app.logger.info("定时任务测试 - 系统运行正常")
    print("💓 系统健康检查 - 运行正常")

# 注册定时任务
def register_scheduled_tasks():
    """注册定时任务"""
    try:
        if APSCHEDULER_AVAILABLE:
            # 使用APScheduler
            scheduler.add_job(
                func=generate_daily_reports,
                trigger=CronTrigger(hour=9, minute=0),
                id='daily_reports',
                name='生成每日选品分析报告',
                replace_existing=True
            )
            
            scheduler.add_job(
                func=generate_weekly_summary,
                trigger=CronTrigger(day_of_week=0, hour=10, minute=0),
                id='weekly_summary',
                name='生成每周选品总结',
                replace_existing=True
            )
            
            scheduler.add_job(
                func=health_check_task,
                trigger='interval',
                minutes=5,
                id='health_check',
                name='系统健康检查'
            )
            
            scheduler.start()
        else:
            # 使用优化版定时器
            scheduler.add_job(
                func=generate_daily_reports,
                trigger_type='cron',
                hour=9,
                minute=0
            )
            
            scheduler.add_job(
                func=generate_weekly_summary,
                trigger_type='cron',
                hour=10,
                minute=0,
                day_of_week=0
            )
            
            scheduler.add_job(
                func=health_check_task,
                trigger_type='interval',
                minutes=5
            )
            
            scheduler.start()
        
        app.logger.info("定时任务注册完成")
        print("✅ 定时任务注册完成")
        
    except Exception as e:
        app.logger.error(f"注册定时任务失败: {e}")
        print(f"❌ 注册定时任务失败: {e}")

# 后台任务函数
def background_generate_report(user_id, report_type):
    """后台生成报告"""
    with app.app_context():
        try:
            # 修复：使用新的Session.get()方法替代旧的Query.get()
            user = db.session.get(User, user_id)
            if not user:
                return
            
            app.logger.info(f"后台生成 {report_type} 报告 for {user.username}")
            print(f"🔄 后台生成 {report_type} 报告 for {user.username}")
            
            user_products = Product.query.filter_by(user_id=user.id).all()
            if user_products:
                analyzer = AutomationProductAnalyzer(user_products)
                report_data = analyzer.get_detailed_stats()
                
                report = Report(
                    user_id=user.id,
                    report_type=report_type,
                    report_data=json.dumps(report_data, ensure_ascii=False)
                )
                db.session.add(report)
                db.session.commit()
                
                # 如果是手动生成的报告，也尝试发送邮件
                if report_type == 'manual':
                    email_service = EmailService()
                    if email_service.send_report_email(user.email, user.username, report_data, ""):
                        report.sent_via_email = True
                        report.email_sent_at = datetime.now(timezone.utc)
                        db.session.commit()
                
                app.logger.info(f"后台报告生成完成: {user.username}")
                print(f"✅ 后台报告生成完成: {user.username}")
            
        except Exception as e:
            app.logger.error(f"后台生成报告失败: {e}")
            print(f"❌ 后台生成报告失败: {e}")

# ========== 新增的CSV导入功能 ==========

@app.route('/api/import-csv', methods=['POST'])
@login_required
def api_import_csv():
    """导入CSV文件数据"""
    try:
        # 新增的清洗函数
        def clean_price(price_str):
            if isinstance(price_str, str):
                return price_str.replace('$', '').replace(',', '').strip()
            return price_str

        # 获取上传的文件
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': '请上传CSV文件'})
        
        # 读取CSV文件
        try:
            # 跳过前2行（文件头），从第3行开始读取数据
            df = pd.read_csv(file, skiprows=2, encoding='utf-8')
        except Exception as e:
            return jsonify({'success': False, 'message': f'读取CSV文件失败: {str(e)}'})
        
        # 检查必要的列是否存在
        required_columns = ['ASIN', 'Product Name', 'Price', 'Units Sold (Monthly)', 'Category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'success': False, 'message': f'CSV文件缺少必要的列: {missing_columns}'})
        
        # 导入产品数据
        imported_count = 0
        for index, row in df.iterrows():
            try:
                # 检查是否已存在相同名称的产品
                existing_product = Product.query.filter_by(
                    name=row['Product Name'], 
                    user_id=session['user_id']
                ).first()
                
                if existing_product:
                    continue  # 跳过已存在的产品
                
                # 创建新产品
                product = Product(
                    name=row['Product Name'],
                    category=row.get('Category', '未知类别'),
                    current_price=float(clean_price(row['Price'])),
                    estimated_cost=float(clean_price(row['Price'])) * 0.3,# 假设成本是价格的30%
                    monthly_sales=int(row['Units Sold (Monthly)']),
                    competition_level='中',  # 默认值
                    review_rating=4.0,  # 默认值
                    product_url=f"https://www.amazon.com/dp/{row['ASIN']}" if pd.notna(row['ASIN']) else '',
                    user_id=session['user_id']
                )
                
                db.session.add(product)
                imported_count += 1
                
            except Exception as e:
                app.logger.error(f"导入产品失败 (行 {index+3}): {e}")
                continue
        
        db.session.commit()
        
        app.logger.info(f"用户 {session['username']} 导入 {imported_count} 个产品")
        return jsonify({
            'success': True, 
            'message': f'成功导入 {imported_count} 个产品',
            'imported_count': imported_count
        })
        
    except Exception as e:
        app.logger.error(f"导入CSV失败: {e}")
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'})

@app.route('/api/clear-products', methods=['POST'])
@login_required
def api_clear_products():
    """清空当前用户的所有产品"""
    try:
        deleted_count = Product.query.filter_by(user_id=session['user_id']).delete()
        db.session.commit()
        
        app.logger.info(f"用户 {session['username']} 清空了 {deleted_count} 个产品")
        return jsonify({
            'success': True, 
            'message': f'已清空 {deleted_count} 个产品'
        })
        
    except Exception as e:
        app.logger.error(f"清空产品失败: {e}")
        return jsonify({'success': False, 'message': f'清空失败: {str(e)}'})

# ========== 路由定义 ==========

@app.route('/')
def index():
    app.logger.info('首页访问')
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            app.logger.info(f'用户登录成功: {username}')
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            app.logger.warning(f'登录失败: {username}')
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        app.logger.info(f'新用户注册: {username}')
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    product_count = Product.query.filter_by(user_id=session['user_id']).count()
    report_count = Report.query.filter_by(user_id=session['user_id']).count()
    
    # 获取产品统计数据
    user_products = Product.query.filter_by(user_id=session['user_id']).all()
    analyzer = AutomationProductAnalyzer(user_products)
    stats = analyzer.get_detailed_stats()
    
    app.logger.info(f'用户访问仪表板: {session["username"]}')
    return render_template('dashboard_automation_optimized.html', 
                         username=session.get('username'),
                         product_count=product_count,
                         report_count=report_count,
                         stats=stats)

@app.route('/api/stats')
@login_required
def api_stats():
    user_products = Product.query.filter_by(user_id=session['user_id']).all()
    analyzer = AutomationProductAnalyzer(user_products)
    stats = analyzer.get_detailed_stats()
    return jsonify(stats)

@app.route('/api/generate-report', methods=['POST'])
@login_required
def api_generate_report():
    """手动生成报告"""
    try:
        report_type = request.json.get('report_type', 'manual')
        
        # 在后台生成报告
        executor.submit(background_generate_report, session['user_id'], report_type)
        
        app.logger.info(f"用户 {session['username']} 请求生成 {report_type} 报告")
        return jsonify({'success': True, 'message': '报告生成任务已启动，请稍后查看'})
        
    except Exception as e:
        app.logger.error(f"生成报告失败: {e}")
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'})

@app.route('/api/reports')
@login_required
def api_reports():
    """获取用户报告列表"""
    try:
        reports = Report.query.filter_by(user_id=session['user_id']).order_by(Report.generated_at.desc()).limit(10).all()
        
        reports_data = []
        for report in reports:
            report_data = json.loads(report.report_data) if report.report_data else {}
            reports_data.append({
                'id': report.id,
                'report_type': report.report_type,
                'generated_at': report.generated_at.strftime('%Y-%m-%d %H:%M'),
                'sent_via_email': report.sent_via_email,
                'summary': f"{report_data.get('total_products', 0)}个产品, 平均ROI: {report_data.get('avg_roi', 0)}%"
            })
        
        return jsonify({'reports': reports_data})
        
    except Exception as e:
        app.logger.error(f"获取报告列表失败: {e}")
        return jsonify({'reports': []})

@app.route('/api/system/status')
@login_required
def api_system_status():
    """获取系统状态"""
    try:
        # 获取任务调度器状态
        if APSCHEDULER_AVAILABLE:
            scheduler_status = 'APScheduler'
            jobs = []
            for job in scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.strftime('%Y-%m-d %H:%M:%S') if job.next_run_time else '未知'
                })
        else:
            scheduler_status = 'SimpleScheduler'
            jobs = scheduler.get_task_status() if hasattr(scheduler, 'get_task_status') else []
        
        system_info = {
            'status': 'running',
            'scheduler_type': scheduler_status,
            'mail_service': 'Available' if FLASK_MAIL_AVAILABLE else 'Simulated',
            'background_workers': executor._max_workers,
            'server_time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'scheduled_jobs': jobs
        }
        
        return jsonify(system_info)
        
    except Exception as e:
        app.logger.error(f"获取系统状态失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/products/overview')
@login_required
def api_products_overview():
    """获取产品概览数据"""
    try:
        user_products = Product.query.filter_by(user_id=session['user_id']).all()
        analyzer = AutomationProductAnalyzer(user_products)
        stats = analyzer.get_detailed_stats()
        
        # 添加实时产品数据
        products_data = []
        for product in user_products[:5]:  # 只返回前5个产品
            product_dict = product.to_dict()
            product_dict['comprehensive_score'] = analyzer.calculate_comprehensive_score(product_dict)
            products_data.append(product_dict)
        
        overview = {
            'basic_stats': {
                'total_products': stats['total_products'],
                'avg_roi': stats['avg_roi'],
                'total_revenue': stats['total_revenue'],
                'high_value_count': stats['high_value_count']
            },
            'recent_products': products_data,
            'category_distribution': stats['category_breakdown'],
            'performance_metrics': {
                'profit_potential': stats['profit_analysis']['total_profit_potential'],
                'sales_velocity': stats['sales_analysis']['sales_velocity'],
                'top_product': stats['top_product']
            }
        }
        
        return jsonify(overview)
        
    except Exception as e:
        app.logger.error(f"获取产品概览失败: {e}")
        return jsonify({'error': str(e)})

# 其他产品管理路由
@app.route('/api/products')
@login_required
def api_products():
    user_products = Product.query.filter_by(user_id=session['user_id']).all()
    
    products_data = []
    analyzer = AutomationProductAnalyzer(user_products)
    
    for product in user_products:
        product_dict = product.to_dict()
        product_dict['comprehensive_score'] = analyzer.calculate_comprehensive_score(product_dict)
        products_data.append(product_dict)
    
    app.logger.info(f'产品数据查询: 用户={session["username"]}, 结果数={len(products_data)}')
    return jsonify({'products': products_data})

@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    try:
        name = request.form['name'].strip()
        category = request.form['category']
        current_price = float(request.form['current_price'])
        estimated_cost = float(request.form['estimated_cost'])
        monthly_sales = int(request.form['monthly_sales'])
        competition_level = request.form['competition_level']
        review_rating = float(request.form.get('review_rating', 4.0))
        product_url = request.form.get('product_url', '')
        
        product = Product(
            name=name,
            category=category,
            current_price=current_price,
            estimated_cost=estimated_cost,
            monthly_sales=monthly_sales,
            competition_level=competition_level,
            review_rating=review_rating,
            product_url=product_url,
            user_id=session['user_id']
        )
        
        db.session.add(product)
        db.session.commit()
        
        app.logger.info(f'产品添加成功: {name}, 用户: {session["username"]}')
        return jsonify({'success': True, 'message': '产品添加成功！'})
        
    except Exception as e:
        app.logger.error(f'添加产品失败: {e}')
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'})

@app.route('/logout')
def logout():
    username = session.get('username', '未知用户')
    session.clear()
    app.logger.info(f'用户退出登录: {username}')
    flash('已成功退出登录', 'success')
    return redirect(url_for('login'))

# 创建优化版模板
def create_optimized_templates():
    templates_dir = 'templates_automation_optimized'
    if not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)
    
    # 登录页面（保持不变）
    login_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - 自动化选品系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #34495e;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input:focus {
            outline: none;
            border-color: #3498db;
        }
        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .register-link {
            text-align: center;
            margin-top: 20px;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .alert {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .alert-success { background: #d4edda; color: #155724; }
        .alert-error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 用户登录</h1>
        
        <div class="flash-messages">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'error' }}">
                            {{ message }}
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        
        <form method="POST">
            <div class="form-group">
                <label>用户名:</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>密码:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">登录</button>
        </form>
        
        <div class="register-link">
            <p>还没有账号？ <a href="{{ url_for('register') }}">立即注册</a></p>
        </div>
        
        <div style="text-align: center; margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <p><strong>演示账号:</strong> demo / demo123</p>
        </div>
    </div>
</body>
</html>
'''
    
    # 注册页面（保持不变）
    register_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>注册 - 自动化选品系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .register-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #34495e;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input:focus {
            outline: none;
            border-color: #3498db;
        }
        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #27ae60, #229954);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .login-link {
            text-align: center;
            margin-top: 20px;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .alert {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .alert-success { background: #d4edda; color: #155724; }
        .alert-error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="register-container">
        <h1>📝 用户注册</h1>
        
        <div class="flash-messages">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'error' }}">
                            {{ message }}
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        
        <form method="POST">
            <div class="form-group">
                <label>用户名:</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>邮箱:</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>密码:</label>
                <input type="password" name="password" required>
            </div>
            <div class="form-group">
                <label>确认密码:</label>
                <input type="password" name="confirm_password" required>
            </div>
            <button type="submit" class="btn">注册</button>
        </form>
        
        <div class="login-link">
            <p>已有账号？ <a href="{{ url_for('login') }}">立即登录</a></p>
        </div>
    </div>
</body>
</html>
'''
    
    # 优化版仪表板页面 - 已添加CSV导入功能
    dashboard_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自动化选品分析系统 - 优化版</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: #f5f6fa;
            min-height: 100vh;
        }
        .container { 
            max-width: 1600px; 
            margin: 0 auto; 
        }
        .header { 
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 5px;
        }
        .header p {
            opacity: 0.9;
        }
        .user-info {
            text-align: right;
        }
        .user-info a {
            color: white;
            text-decoration: none;
            margin-left: 15px;
            background: rgba(255,255,255,0.2);
            padding: 8px 15px;
            border-radius: 5px;
        }
        .main-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin: 20px 40px;
        }
        .automation-panel {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        .stats-panel {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 15px;
        }
        .automation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .automation-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 12px;
            border-left: 6px solid #3498db;
            transition: all 0.3s ease;
        }
        .automation-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .card-icon {
            font-size: 2em;
            margin-right: 15px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card.warning {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }
        .stat-card.success {
            background: linear-gradient(135deg, #27ae60, #229954);
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .btn {
            padding: 12px 25px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 5px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        .btn-success {
            background: linear-gradient(135deg, #27ae60, #229954);
        }
        .btn-warning {
            background: linear-gradient(135deg, #f39c12, #e67e22);
        }
        .btn-danger {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }
        .reports-section {
            margin-top: 30px;
        }
        .report-item {
            background: white;
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .system-status {
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .status-item {
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
        }
        .task-list {
            margin-top: 20px;
        }
        .task-item {
            background: #34495e;
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🤖 自动化选品分析系统 - 优化版</h1>
                <p>智能报告 · 定时任务 · 邮件通知 · 实时监控</p>
            </div>
            <div class="user-info">
                欢迎, <strong>{{ username }}</strong>! 
                <a href="{{ url_for('logout') }}">退出登录</a>
            </div>
        </div>

        <div class="main-content">
            <div class="automation-panel">
                <div class="panel-header">
                    <h2>🔄 自动化任务控制</h2>
                    <div>
                        <button class="btn btn-success" onclick="generateReport()">📊 立即生成报告</button>
                        <button class="btn" onclick="testEmail()">📧 测试邮件发送</button>
                    </div>
                </div>

                <div class="automation-grid">
                    <div class="automation-card">
                        <div class="card-header">
                            <div class="card-icon">📅</div>
                            <h3>定时报告生成</h3>
                        </div>
                        <p>系统将在每天上午9点自动生成选品分析报告，并通过邮件发送给您。</p>
                        <div class="status-item">
                            <span>任务状态:</span>
                            <span style="color: #2ecc71;">运行中</span>
                        </div>
                    </div>

                    <div class="automation-card">
                        <div class="card-header">
                            <div class="card-icon">📧</div>
                            <h3>邮件通知系统</h3>
                        </div>
                        <p>自动将重要分析结果和报告发送到您的注册邮箱，确保您不错过任何商机。</p>
                        <div class="status-item">
                            <span>当前模式:</span>
                            <span id="mailMode">模拟发送</span>
                        </div>
                    </div>

                    <div class="automation-card">
                        <div class="card-header">
                            <div class="card-icon">⚡</div>
                            <h3>后台任务处理</h3>
                        </div>
                        <p>大数据分析和报告生成在后台异步执行，不会影响您的正常使用体验。</p>
                        <div class="status-item">
                            <span>工作线程:</span>
                            <span id="workerCount">4</span>
                        </div>
                    </div>
                </div>

                <div class="system-status">
                    <h3>🖥️ 系统状态监控</h3>
                    <div id="systemStatus">
                        <!-- 系统状态动态加载 -->
                    </div>
                    <div class="task-list" id="taskList">
                        <!-- 定时任务列表动态加载 -->
                    </div>
                </div>

                <!-- 产品列表部分 - 已添加CSV导入功能 -->
                <div class="reports-section">
                    <h3>📦 产品列表</h3>
                    
                    <!-- 添加导入功能 -->
                    <div style="margin-bottom: 20px; display: flex; gap: 10px;">
                        <input type="file" id="csvFile" accept=".csv" style="display: none;">
                        <button class="btn btn-success" onclick="document.getElementById('csvFile').click()">
                            📁 导入CSV文件
                        </button>
                        <button class="btn btn-danger" onclick="clearProducts()">
                            🗑️ 清空产品
                        </button>
                        <button class="btn" onclick="loadProductList()">
                            🔄 刷新列表
                        </button>
                    </div>
                    
                    <div id="importStatus" style="margin-bottom: 10px;"></div>
                    
                    <div id="productList" style="background: white; border-radius: 8px; padding: 20px; margin-top: 15px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #f8f9fa;">
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">产品名称</th>
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">类别</th>
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">价格</th>
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">月销量</th>
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">产品链接</th>
                                </tr>
                            </thead>
                            <tbody id="productTableBody">
                                <!-- 产品数据将通过JavaScript动态加载 -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="reports-section">
                    <h3>📋 最近生成的报告</h3>
                    <div id="reportsList">
                        <!-- 报告列表动态加载 -->
                    </div>
                </div>
            </div>

            <div class="stats-panel">
                <div class="panel-header">
                    <h2>📈 实时数据概览</h2>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="totalProducts">0</div>
                        <div class="stat-label">总产品数</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-number" id="avgRoi">0%</div>
                        <div class="stat-label">平均ROI</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="totalRevenue">$0</div>
                        <div class="stat-label">月收益潜力</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-number" id="highValueCount">0</div>
                        <div class="stat-label">高价值产品</div>
                    </div>
                </div>

                <div style="margin-top: 20px;">
                    <h3>🏆 最佳表现产品</h3>
                    <div id="topProduct" style="padding: 15px; background: #f8f9fa; border-radius: 8px; margin-top: 10px;">
                        加载中...
                    </div>
                </div>

                <div style="margin-top: 20px;">
                    <h3>📊 性能指标</h3>
                    <div id="performanceMetrics" style="padding: 15px; background: #f8f9fa; border-radius: 8px; margin-top: 10px;">
                        加载中...
                    </div>
                </div>

                <div style="margin-top: 20px;">
                    <button class="btn" onclick="refreshStats()" style="width: 100%;">🔄 刷新数据</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadSystemStatus();
            loadReports();
            loadStatsOverview();
            loadProductList();
            setInterval(loadSystemStatus, 30000); // 每30秒刷新系统状态
            setInterval(loadReports, 60000); // 每60秒刷新报告列表
        });

        // 加载系统状态
        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/system/status');
                const data = await response.json();
                
                let statusHtml = `
                    <div class="status-item">
                        <span>系统状态:</span>
                        <span style="color: #2ecc71;">${data.status}</span>
                    </div>
                    <div class="status-item">
                        <span>任务调度器:</span>
                        <span>${data.scheduler_type}</span>
                    </div>
                    <div class="status-item">
                        <span>邮件服务:</span>
                        <span>${data.mail_service}</span>
                    </div>
                    <div class="status-item">
                        <span>服务器时间:</span>
                        <span>${data.server_time}</span>
                    </div>
                `;
                
                document.getElementById('systemStatus').innerHTML = statusHtml;
                
                // 更新邮件模式显示
                document.getElementById('mailMode').textContent = data.mail_service;
                
                // 显示定时任务列表
                if (data.scheduled_jobs && data.scheduled_jobs.length > 0) {
                    let taskHtml = '<h4>📅 定时任务列表</h4>';
                    data.scheduled_jobs.forEach(job => {
                        taskHtml += `
                            <div class="task-item">
                                <span>${job.name || job.id}</span>
                                <span>下次运行: ${job.next_run || '未知'}</span>
                            </div>
                        `;
                    });
                    document.getElementById('taskList').innerHTML = taskHtml;
                }
                
            } catch (error) {
                console.error('加载系统状态失败:', error);
            }
        }

        // 加载报告列表
        async function loadReports() {
            try {
                const response = await fetch('/api/reports');
                const data = await response.json();
                
                let reportsHtml = '';
                if (data.reports && data.reports.length > 0) {
                    data.reports.forEach(report => {
                        reportsHtml += `
                            <div class="report-item">
                                <div>
                                    <strong>${report.report_type}报告</strong>
                                    <p>生成时间: ${report.generated_at}</p>
                                    <p>${report.summary}</p>
                                </div>
                                <div>
                                    ${report.sent_via_email ? '📧 已发送邮件' : '⏳ 处理中'}
                                </div>
                            </div>
                        `;
                    });
                } else {
                    reportsHtml = '<p>暂无报告，点击上方按钮生成第一个报告</p>';
                }
                
                document.getElementById('reportsList').innerHTML = reportsHtml;
                
            } catch (error) {
                console.error('加载报告列表失败:', error);
            }
        }

        // 加载数据概览
        async function loadStatsOverview() {
            try {
                const response = await fetch('/api/products/overview');
                const data = await response.json();
                
                if (data.error) {
                    console.error('加载数据概览失败:', data.error);
                    return;
                }
                
                // 更新基础统计
                document.getElementById('totalProducts').textContent = data.basic_stats.total_products;
                document.getElementById('avgRoi').textContent = data.basic_stats.avg_roi + '%';
                document.getElementById('totalRevenue').textContent = '$' + data.basic_stats.total_revenue.toLocaleString();
                document.getElementById('highValueCount').textContent = data.basic_stats.high_value_count;
                
                // 更新最佳产品
                document.getElementById('topProduct').innerHTML = `
                    <strong>${data.performance_metrics.top_product}</strong>
                    <p style="margin-top: 5px; color: #666;">当前最佳ROI产品</p>
                `;
                
                // 更新性能指标
                document.getElementById('performanceMetrics').innerHTML = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <strong>利润潜力</strong>
                            <p>$${data.performance_metrics.profit_potential.toFixed(2)}</p>
                        </div>
                        <div>
                            <strong>销售速度</strong>
                            <p>${data.performance_metrics.sales_velocity}</p>
                        </div>
                    </div>
                `;
                
            } catch (error) {
                console.error('加载数据概览失败:', error);
            }
        }

        // 加载产品列表 - 新增函数
        async function loadProductList() {
            try {
                const response = await fetch('/api/products');
                const data = await response.json();
                
                let productHtml = '';
                if (data.products && data.products.length > 0) {
                    data.products.forEach(product => {
                        productHtml += `
                            <tr>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">${product.name}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">${product.category}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">¥${product.current_price}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">${product.monthly_sales}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">
                                    ${product.product_url ? 
                                        `<a href="${product.product_url}" target="_blank" style="color: #007bff; text-decoration: none;">🔗 查看产品</a>` : 
                                        '<span style="color: #6c757d;">-</span>'}
                                </td>
                            </tr>
                        `;
                    });
                } else {
                    productHtml = '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #6c757d;">暂无产品数据</td></tr>';
                }
                
                document.getElementById('productTableBody').innerHTML = productHtml;
            } catch (error) {
                console.error('加载产品列表失败:', error);
                document.getElementById('productTableBody').innerHTML = '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #dc3545;">加载失败</td></tr>';
            }
        }

        // CSV文件导入功能
        document.getElementById('csvFile').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                importCSV(file);
            }
        });

        async function importCSV(file) {
            const statusDiv = document.getElementById('importStatus');
            statusDiv.innerHTML = '<div style="color: #007bff;">🔄 正在导入CSV文件...</div>';
            
            const formData = new FormData();
            formData.append('csv_file', file);
            
            try {
                const response = await fetch('/api/import-csv', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.innerHTML = `<div style="color: #28a745;">✅ ${result.message}</div>`;
                    // 导入成功后刷新产品列表
                    setTimeout(() => {
                        loadProductList();
                        loadStatsOverview();
                    }, 1000);
                } else {
                    statusDiv.innerHTML = `<div style="color: #dc3545;">❌ ${result.message}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div style="color: #dc3545;">❌ 导入失败: ${error}</div>`;
            }
            
            // 清空文件输入，允许重复选择同一文件
            document.getElementById('csvFile').value = '';
        }

        // 清空产品功能
        async function clearProducts() {
            if (!confirm('确定要清空所有产品数据吗？此操作不可撤销！')) {
                return;
            }
            
            try {
                const response = await fetch('/api/clear-products', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(result.message);
                    // 清空成功后刷新产品列表和数据概览
                    loadProductList();
                    loadStatsOverview();
                } else {
                    alert('清空失败: ' + result.message);
                }
            } catch (error) {
                alert('请求失败: ' + error);
            }
        }

        // 生成报告
        async function generateReport() {
            try {
                const response = await fetch('/api/generate-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        report_type: 'manual'
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('报告生成任务已启动！请稍后查看报告列表。');
                    setTimeout(loadReports, 2000); // 2秒后刷新报告列表
                } else {
                    alert('生成失败: ' + result.message);
                }
            } catch (error) {
                alert('请求失败: ' + error);
            }
        }

        // 测试邮件发送
        async function testEmail() {
            alert('邮件功能测试中...（当前使用模拟邮件发送）');
        }

        // 刷新数据
        async function refreshStats() {
            await loadStatsOverview();
            await loadReports();
            await loadProductList();
            alert('数据已刷新！');
        }
    </script>
</body>
</html>
'''
    
    # 写入模板文件
    with open(os.path.join(templates_dir, 'login.html'), 'w', encoding='utf-8') as f:
        f.write(login_html)
    
    with open(os.path.join(templates_dir, 'register.html'), 'w', encoding='utf-8') as f:
        f.write(register_html)
        
    with open(os.path.join(templates_dir, 'dashboard_automation_optimized.html'), 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print(f"✅ 优化版模板创建完成: {templates_dir}")

# 添加示例数据
def add_sample_data():
    with app.app_context():
        sample_user = User.query.filter_by(username='demo').first()
        if not sample_user:
            demo_user = User(username='demo', email='demo@example.com', receive_notifications=True)
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            
            sample_products = [
                Product(name='智能保温杯', category='家居', current_price=35.99, estimated_cost=12.50, 
                       monthly_sales=320, competition_level='中', review_rating=4.5, user_id=demo_user.id),
                Product(name='无线充电器', category='数码', current_price=28.50, estimated_cost=9.80, 
                       monthly_sales=480, competition_level='高', review_rating=4.3, user_id=demo_user.id),
                Product(name='便携风扇', category='生活', current_price=19.99, estimated_cost=6.50, 
                       monthly_sales=560, competition_level='中', review_rating=4.7, user_id=demo_user.id),
                Product(name='瑜伽垫', category='运动', current_price=45.00, estimated_cost=18.00, 
                       monthly_sales=280, competition_level='低', review_rating=4.8, user_id=demo_user.id),
                Product(name='电动牙刷', category='个护', current_price=39.90, estimated_cost=15.30, 
                       monthly_sales=390, competition_level='中', review_rating=4.4, user_id=demo_user.id)
            ]
            
            for product in sample_products:
                db.session.add(product)
            
            db.session.commit()
            print("✅ 示例数据添加完成")

# ！！！添加以下健康检查路由！！！
@app.route('/health', methods=['GET'])
def health_check():
    """
    极简健康检查端点，不依赖数据库、邮件等任何外部服务。
    仅用于确认Flask应用进程本身是否存活且能响应请求。
    """
    return {'status': 'healthy', 'service': 'Automation System', 'timestamp': datetime.datetime.utcnow().isoformat()}, 200

if __name__ == '__main__':
    # 设置日志
    setup_logging()
    
    # 创建优化版模板
    create_optimized_templates()
    
    # 添加示例数据
    add_sample_data()
    
    # 注册定时任务
    register_scheduled_tasks()
    
    # 设置模板文件夹
    app.template_folder = 'templates_automation_optimized'
    
    print("\n🚀 自动化选品分析系统（优化版）启动成功！")
    print("📍 访问地址: http://127.0.0.1:5010")
    print("🛠️  优化内容:")
    print("   • ✅ 修复SQLAlchemy警告 (Query.get() → Session.get())")
    print("   • ✅ 增强邮件状态跟踪")
    print("   • ✅ 添加实时产品数据概览")
    print("   • ✅ 改进定时任务管理系统")
    print("   • ✅ 增强数据分析功能")
    print("   • ✅ 新增CSV导入功能")
    print("🤖 新增功能:")
    print("   • 📊 实时数据监控面板")
    print("   • ⚡ 定时任务状态显示")
    print("   • 📈 增强的性能指标")
    print("   • 🔄 自动数据刷新")
    print("   • 📁 CSV文件导入")
    print("   • 🗑️ 一键清空产品")
    print("📋 登录信息: demo / demo123")
    
    try:
        app.run(debug=True, host='127.0.0.1', port=5010, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 正在关闭系统...")
        if hasattr(scheduler, 'shutdown'):
            scheduler.shutdown()
        executor.shutdown(wait=False)
        print("✅ 系统已安全关闭")