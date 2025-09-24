"""
Vercel专用的Flask应用
简化版本，专门为Vercel部署优化
"""

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# 创建Flask应用，指定模板和静态文件路径
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# 配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vercel-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 简化的数据库模型
class ProductionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    product = db.Column(db.Text, nullable=False)
    process = db.Column(db.String(200), nullable=False)
    theoretical_runtime = db.Column(db.String(20), default='')
    actual_runtime = db.Column(db.String(20), default='')
    single_time = db.Column(db.String(20), default='')
    theoretical_qty = db.Column(db.String(20), default='')
    actual_qty = db.Column(db.String(20), default='')
    total_weight = db.Column(db.String(20), default='')
    unit_weight = db.Column(db.String(20), default='')
    tare_weight = db.Column(db.String(20), default='')
    capacity_rate = db.Column(db.String(20), default='')
    time_rate = db.Column(db.String(20), default='')
    downtime_duration = db.Column(db.String(20), default='')
    adjustment_time = db.Column(db.String(20), default='')
    adjustment_master = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/records')
def get_records():
    """获取所有记录"""
    try:
        records = ProductionRecord.query.order_by(ProductionRecord.date.desc()).all()
        result = []
        for record in records:
            record_dict = {
                'id': record.id,
                'date': record.date,
                'name': record.name,
                'position': record.position,
                'product': record.product,
                'process': record.process,
                'theoretical_runtime': record.theoretical_runtime,
                'actual_runtime': record.actual_runtime,
                'single_time': record.single_time,
                'theoretical_qty': record.theoretical_qty,
                'actual_qty': record.actual_qty,
                'total_weight': record.total_weight,
                'unit_weight': record.unit_weight,
                'tare_weight': record.tare_weight,
                'capacity_rate': record.capacity_rate,
                'time_rate': record.time_rate,
                'downtime_duration': record.downtime_duration,
                'adjustment_time': record.adjustment_time,
                'adjustment_master': record.adjustment_master,
                'created_at': record.created_at.isoformat() if record.created_at else None
            }
            result.append(record_dict)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/records', methods=['POST'])
def add_record():
    """添加新记录"""
    try:
        data = request.json
        record = ProductionRecord(
            date=data.get('date', ''),
            name=data.get('name', ''),
            position=data.get('position', ''),
            product=data.get('product', ''),
            process=data.get('process', ''),
            theoretical_runtime=data.get('theoretical_runtime', ''),
            actual_runtime=data.get('actual_runtime', ''),
            single_time=data.get('single_time', ''),
            theoretical_qty=data.get('theoretical_qty', ''),
            actual_qty=data.get('actual_qty', ''),
            total_weight=data.get('total_weight', ''),
            unit_weight=data.get('unit_weight', ''),
            tare_weight=data.get('tare_weight', ''),
            capacity_rate=data.get('capacity_rate', ''),
            time_rate=data.get('time_rate', ''),
            downtime_duration=data.get('downtime_duration', ''),
            adjustment_time=data.get('adjustment_time', ''),
            adjustment_master=data.get('adjustment_master', '')
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'success': True, 'id': record.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """更新记录"""
    try:
        record = ProductionRecord.query.get_or_404(record_id)
        data = request.json
        
        for field in ['date', 'name', 'position', 'product', 'process', 
                      'theoretical_runtime', 'actual_runtime', 'single_time',
                      'theoretical_qty', 'actual_qty', 'total_weight', 
                      'unit_weight', 'tare_weight', 'capacity_rate', 
                      'time_rate', 'downtime_duration', 'adjustment_time', 
                      'adjustment_master']:
            if field in data:
                setattr(record, field, data[field])
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除记录"""
    try:
        record = ProductionRecord.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """获取统计数据"""
    try:
        total_records = ProductionRecord.query.count()
        return jsonify({
            'total_records': total_records,
            'message': 'Vercel部署版本 - 数据存储在内存中'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 初始化数据库
with app.app_context():
    db.create_all()
    
    # 添加一些示例数据
    if ProductionRecord.query.count() == 0:
        sample_record = ProductionRecord(
            date='2024-01-01',
            name='示例用户',
            position='操作员',
            product='示例产品',
            process='示例工序',
            theoretical_runtime='480',
            actual_runtime='450',
            single_time='30',
            theoretical_qty='900',
            actual_qty='850',
            total_weight='1000',
            unit_weight='1.2',
            tare_weight='50',
            capacity_rate='94.4%',
            time_rate='93.8%',
            downtime_duration='30',
            adjustment_time='0',
            adjustment_master=''
        )
        db.session.add(sample_record)
        db.session.commit()

# Vercel需要这个变量
application = app

if __name__ == '__main__':
    app.run(debug=True)
