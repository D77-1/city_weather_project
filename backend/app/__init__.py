from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import click

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # 插件初始化
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    # 注册蓝图
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # 在应用上下文中自动建表（开发用）
    with app.app_context():
        from app import models  # noqa: F401 - 确保所有模型被导入
        db.create_all()

        # 自动检测并补充数据到今天（开发环境自动刷新 mock 数据）
        try:
            from app.services.mock_data import refresh_records
            refresh_records()
        except Exception as e:
            print(f'[Auto-refresh] 跳过: {e}')

    # 注册 CLI 命令
    _register_commands(app)

    return app


def _register_commands(app):
    @app.cli.command('seed')
    @click.option('--days', default=365, help='生成多少天的历史数据')
    def seed_command(days):
        """生成模拟数据并写入数据库"""
        from app.services.mock_data import seed_all
        seed_all(days=days)

    @app.cli.command('drop')
    @click.confirmation_option(prompt='确定要清空所有数据表吗？')
    def drop_command():
        """清空所有数据表（危险操作）"""
        db.drop_all()
        db.create_all()
        click.echo('所有表已重建。')

    @app.cli.command('analyze')
    def analyze_command():
        """对所有城市运行预测+异常检测并持久化结果"""
        from app.services.algorithm import run_all_predictions, run_all_anomaly_detection
        click.echo('正在运行移动平均预测...')
        pred_results = run_all_predictions()
        click.echo(f'预测完成: {len(pred_results)} 条记录')
        click.echo('正在运行 IQR 异常检测...')
        anomaly_results = run_all_anomaly_detection()
        click.echo(f'异常检测完成: {len(anomaly_results)} 条记录')

    @app.cli.command('refresh')
    def refresh_command():
        """将 mock 数据续期到今天（自动补充缺口天数）"""
        from app.services.mock_data import refresh_records
        total = refresh_records()
        if total > 0:
            click.echo(f'数据刷新完成，共补充 {total} 条记录')
            click.echo('提示: 可运行 flask analyze 重新计算预测和异常检测')
