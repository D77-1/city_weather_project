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

        # 首次启动自动创建默认管理员 admin / admin123
        try:
            from app.models import User
            from app.utils.auth import hash_password
            if not User.query.filter_by(role='admin').first():
                admin = User(
                    username='admin',
                    password_hash=hash_password('admin123'),
                    nickname='系统管理员',
                    role='admin',
                )
                db.session.add(admin)
                db.session.commit()
                print('[Init] 已创建默认管理员 admin / admin123')
        except Exception as e:
            print(f'[Init] 管理员初始化跳过: {e}')

        # 启动时自动补充最新空气质量数据（Open-Meteo 真实 API）
        try:
            from app.services.aqi_service import refresh_realtime
            refresh_realtime()
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

    @app.cli.command('import-aqi')
    @click.option('--start', default='2022-09-01', help='起始日期 (YYYY-MM-DD)')
    @click.option('--end', default=None, help='截止日期，默认今天')
    @click.option('--clear', is_flag=True, help='导入前清空旧的空气质量记录')
    def import_aqi_command(start, end, clear):
        """从 Open-Meteo 导入真实空气质量历史数据"""
        from app.services.aqi_service import import_all_cities
        from app.models import AirQualityRecord

        if clear:
            count = AirQualityRecord.query.count()
            if count > 0:
                click.echo(f'正在清空 {count} 条旧记录...')
                AirQualityRecord.query.delete()
                db.session.commit()
                click.echo('旧记录已清空')

        click.echo(f'开始从 Open-Meteo 导入真实空气质量数据...')
        click.echo(f'日期范围: {start} ~ {end or "今天"}')
        total = import_all_cities(start_date=start, end_date=end)
        if total > 0:
            click.echo(f'导入完成! 共 {total} 条记录')
            click.echo('提示: 可运行 flask analyze 重新计算预测和异常检测')

    @app.cli.command('fill-gaps')
    def fill_gaps_command():
        """检测并补充缺失的空气质量数据（带重试）"""
        from app.services.aqi_service import fill_gaps
        click.echo('正在检测数据缺口并补充...')
        total = fill_gaps()
        click.echo(f'补充完成! 共 {total} 条')

    @app.cli.command('refresh')
    def refresh_command():
        """补充最新空气质量数据到今天（从 Open-Meteo 真实 API）"""
        from app.services.aqi_service import refresh_realtime
        total = refresh_realtime()
        if total > 0:
            click.echo(f'数据刷新完成，共补充 {total} 条记录')
            click.echo('提示: 可运行 flask analyze 重新计算预测和异常检测')
