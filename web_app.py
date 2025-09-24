from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from config import Config, DevelopmentConfig, ProductionConfig
import json
from decimal import Decimal, ROUND_HALF_UP

app = Flask(__name__)

# 根据环境变量选择配置
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

db = SQLAlchemy(app)

# 数据库模型
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('production_record.id'), nullable=False)
    column_key = db.Column(db.String(50), nullable=False)  # 'downtime_duration' or 'adjustment_time'
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    position = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProductionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(200), nullable=False)
    process1 = db.Column(db.String(100))
    qty1 = db.Column(db.Integer, default=0)
    process2 = db.Column(db.String(100))
    qty2 = db.Column(db.Integer, default=0)
    process3 = db.Column(db.String(100))
    qty3 = db.Column(db.Integer, default=0)
    process4 = db.Column(db.String(100))
    qty4 = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Process(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/records')
def get_records():
    """获取所有记录，支持筛选"""
    # 获取筛选参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    name = request.args.get('name')
    product = request.args.get('product')
    process = request.args.get('process')
    adjustment_master = request.args.get('adjustment_master')
    
    # 构建查询
    query = ProductionRecord.query
    
    # 应用筛选条件
    if start_date:
        query = query.filter(ProductionRecord.date >= start_date)
    if end_date:
        query = query.filter(ProductionRecord.date <= end_date)
    if name:
        query = query.filter(ProductionRecord.name == name)
    if product:
        query = query.filter(ProductionRecord.product == product)
    if process:
        query = query.filter(ProductionRecord.process == process)
    if adjustment_master:
        query = query.filter(ProductionRecord.adjustment_master == adjustment_master)
    
    records = query.order_by(ProductionRecord.date.desc()).all()
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
            'created_at': record.created_at.isoformat(),
            'updated_at': record.updated_at.isoformat()
        }
        result.append(record_dict)
    return jsonify(result)

@app.route('/api/records', methods=['POST'])
def add_record():
    """添加新记录"""
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
    
    # 自动计算相关字段
    calculate_derived_fields(record.id)
    db.session.commit()  # 保存计算结果
    
    return jsonify({'success': True, 'id': record.id})

@app.route('/api/records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """更新记录"""
    record = ProductionRecord.query.get_or_404(record_id)
    data = request.json
    
    # 更新字段
    for field in ['date', 'name', 'position', 'product', 'process', 
                  'theoretical_runtime', 'actual_runtime', 'single_time',
                  'theoretical_qty', 'actual_qty', 'total_weight', 
                  'unit_weight', 'tare_weight', 'capacity_rate', 
                  'time_rate', 'downtime_duration', 'adjustment_time', 
                  'adjustment_master']:
        if field in data:
            setattr(record, field, data[field])
    
    record.updated_at = datetime.utcnow()
    db.session.commit()
    
    # 自动计算相关字段
    calculate_derived_fields(record_id)
    db.session.commit()  # 保存计算结果
    
    return jsonify({'success': True})

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除记录"""
    record = ProductionRecord.query.get_or_404(record_id)
    
    # 删除相关注释
    Comment.query.filter_by(record_id=record_id).delete()
    
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/employees')
def get_employees():
    """获取员工列表"""
    employees = Employee.query.all()
    result = [{'id': emp.id, 'name': emp.name, 'position': emp.position} for emp in employees]
    return jsonify(result)

@app.route('/api/employees', methods=['POST'])
def add_employee():
    """添加员工"""
    data = request.json
    employee = Employee(name=data['name'], position=data['position'])
    db.session.add(employee)
    db.session.commit()
    return jsonify({'success': True, 'id': employee.id})

@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """删除员工"""
    employee = Employee.query.get_or_404(employee_id)
    
    # 检查是否有记录使用此员工
    records_using_employee = ProductionRecord.query.filter(
        (ProductionRecord.name == employee.name)
    ).count()
    
    if records_using_employee > 0:
        return jsonify({'success': False, 'message': f'无法删除，有 {records_using_employee} 条记录正在使用此员工'}), 400
    
    db.session.delete(employee)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '员工删除成功'})

@app.route('/api/comments/<int:record_id>/<column_key>')
def get_comment(record_id, column_key):
    """获取注释"""
    comment = Comment.query.filter_by(record_id=record_id, column_key=column_key).first()
    if comment:
        return jsonify({'comment': comment.comment_text})
    return jsonify({'comment': ''})

@app.route('/api/comments/<int:record_id>/<column_key>', methods=['POST'])
def save_comment(record_id, column_key):
    """保存注释"""
    data = request.json
    comment_text = data.get('comment', '').strip()
    
    comment = Comment.query.filter_by(record_id=record_id, column_key=column_key).first()
    
    if comment_text:
        if comment:
            comment.comment_text = comment_text
            comment.updated_at = datetime.utcnow()
        else:
            comment = Comment(record_id=record_id, column_key=column_key, comment_text=comment_text)
            db.session.add(comment)
    else:
        if comment:
            db.session.delete(comment)
    
    db.session.commit()
    return jsonify({'success': True})

def calculate_derived_fields(record_id):
    """计算派生字段"""
    record = ProductionRecord.query.get(record_id)
    if not record:
        return
    
    # 计算理论运行时长 = 480 - 调机时长
    try:
        adjustment_time = int(record.adjustment_time) if record.adjustment_time else 0
        theoretical_runtime = max(0, 480 - adjustment_time)
        record.theoretical_runtime = str(theoretical_runtime)
    except (ValueError, TypeError):
        record.theoretical_runtime = '480'
    
    # 计算实际运行时长 = 理论运行时长 - 停机时长
    try:
        theoretical_runtime = int(record.theoretical_runtime) if record.theoretical_runtime else 480
        downtime_duration = int(record.downtime_duration) if record.downtime_duration else 0
        actual_runtime = max(0, theoretical_runtime - downtime_duration)
        record.actual_runtime = str(actual_runtime)
    except (ValueError, TypeError):
        record.actual_runtime = ''
    
    # 计算理论数量 = 实际运行时长 / 单个时间
    try:
        actual_runtime = int(record.actual_runtime) if record.actual_runtime else 0
        single_time = int(record.single_time) if record.single_time else 0
        if single_time > 0:
            theoretical_qty = round((actual_runtime * 60) / single_time)
            record.theoretical_qty = str(theoretical_qty)
        else:
            record.theoretical_qty = ''
    except (ValueError, TypeError):
        record.theoretical_qty = ''
    
    # 计算实际数量 = (总重 - 去皮重量) / 单重
    try:
        total_weight = float(record.total_weight) if record.total_weight else 0
        tare_weight = float(record.tare_weight) if record.tare_weight else 0
        unit_weight = float(record.unit_weight) if record.unit_weight else 0
        if unit_weight > 0:
            actual_qty = (total_weight - tare_weight) / unit_weight
            record.actual_qty = str(round(actual_qty))
        else:
            record.actual_qty = ''
    except (ValueError, TypeError):
        record.actual_qty = ''
    
    # 计算产能稼动率 = 实际数量 / 理论数量
    try:
        actual_qty = int(record.actual_qty) if record.actual_qty else 0
        theoretical_qty = int(record.theoretical_qty) if record.theoretical_qty else 0
        if theoretical_qty > 0:
            capacity_rate = round((actual_qty / theoretical_qty) * 100, 2)
            record.capacity_rate = f"{capacity_rate}%"
        else:
            record.capacity_rate = ''
    except (ValueError, TypeError):
        record.capacity_rate = ''
    
    # 计算时间稼动率 = 实际运行时长 / 理论运行时长
    try:
        actual_runtime = int(record.actual_runtime) if record.actual_runtime else 0
        theoretical_runtime = int(record.theoretical_runtime) if record.theoretical_runtime else 0
        if theoretical_runtime > 0:
            time_rate = round((actual_runtime / theoretical_runtime) * 100, 2)
            record.time_rate = f"{time_rate}%"
        else:
            record.time_rate = ''
    except (ValueError, TypeError):
        record.time_rate = ''
    
    db.session.commit()

# 产量管理API
@app.route('/api/statistics')
def get_statistics():
    """获取统计数据"""
    try:
        # 计算合计实际数量
        total_actual_qty = db.session.query(db.func.sum(ProductionRecord.actual_qty)).scalar() or 0
        
        # 计算平均产能稼动率
        records_with_capacity = ProductionRecord.query.filter(
            ProductionRecord.capacity_rate != '',
            ProductionRecord.capacity_rate.isnot(None)
        ).all()
        
        if records_with_capacity:
            capacity_rates = []
            for record in records_with_capacity:
                try:
                    rate = float(record.capacity_rate.replace('%', ''))
                    capacity_rates.append(rate)
                except (ValueError, AttributeError):
                    continue
            avg_capacity_rate = sum(capacity_rates) / len(capacity_rates) if capacity_rates else 0
        else:
            avg_capacity_rate = 0
        
        # 计算平均时间稼动率
        records_with_time = ProductionRecord.query.filter(
            ProductionRecord.time_rate != '',
            ProductionRecord.time_rate.isnot(None)
        ).all()
        
        if records_with_time:
            time_rates = []
            for record in records_with_time:
                try:
                    rate = float(record.time_rate.replace('%', ''))
                    time_rates.append(rate)
                except (ValueError, AttributeError):
                    continue
            avg_time_rate = sum(time_rates) / len(time_rates) if time_rates else 0
        else:
            avg_time_rate = 0
        
        return jsonify({
            'total_actual_qty': total_actual_qty,
            'avg_capacity_rate': round(avg_capacity_rate, 2),
            'avg_time_rate': round(avg_time_rate, 2),
            'total_records': ProductionRecord.query.count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/production-plans')
def get_production_plans():
    """获取所有产量计划"""
    plans = ProductionPlan.query.all()
    result = []
    for plan in plans:
        # 计算每个工序的完成率
        process_completion = {}
        
        # 工序1
        if plan.process1 and plan.qty1 > 0:
            actual_qty = db.session.query(db.func.sum(ProductionRecord.actual_qty)).filter(
                ProductionRecord.product == plan.product,
                ProductionRecord.process == plan.process1
            ).scalar() or 0
            completion_rate = (actual_qty / plan.qty1) * 100 if plan.qty1 > 0 else 0
            process_completion[plan.process1] = {
                'planned_qty': plan.qty1,
                'actual_qty': actual_qty,
                'completion_rate': round(completion_rate, 1)
            }
        
        # 工序2
        if plan.process2 and plan.qty2 > 0:
            actual_qty = db.session.query(db.func.sum(ProductionRecord.actual_qty)).filter(
                ProductionRecord.product == plan.product,
                ProductionRecord.process == plan.process2
            ).scalar() or 0
            completion_rate = (actual_qty / plan.qty2) * 100 if plan.qty2 > 0 else 0
            process_completion[plan.process2] = {
                'planned_qty': plan.qty2,
                'actual_qty': actual_qty,
                'completion_rate': round(completion_rate, 1)
            }
        
        # 工序3
        if plan.process3 and plan.qty3 > 0:
            actual_qty = db.session.query(db.func.sum(ProductionRecord.actual_qty)).filter(
                ProductionRecord.product == plan.product,
                ProductionRecord.process == plan.process3
            ).scalar() or 0
            completion_rate = (actual_qty / plan.qty3) * 100 if plan.qty3 > 0 else 0
            process_completion[plan.process3] = {
                'planned_qty': plan.qty3,
                'actual_qty': actual_qty,
                'completion_rate': round(completion_rate, 1)
            }
        
        # 工序4
        if plan.process4 and plan.qty4 > 0:
            actual_qty = db.session.query(db.func.sum(ProductionRecord.actual_qty)).filter(
                ProductionRecord.product == plan.product,
                ProductionRecord.process == plan.process4
            ).scalar() or 0
            completion_rate = (actual_qty / plan.qty4) * 100 if plan.qty4 > 0 else 0
            process_completion[plan.process4] = {
                'planned_qty': plan.qty4,
                'actual_qty': actual_qty,
                'completion_rate': round(completion_rate, 1)
            }
        
        result.append({
            'id': plan.id,
            'product': plan.product,
            'process1': plan.process1,
            'qty1': plan.qty1,
            'process2': plan.process2,
            'qty2': plan.qty2,
            'process3': plan.process3,
            'qty3': plan.qty3,
            'process4': plan.process4,
            'qty4': plan.qty4,
            'process_completion': process_completion,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'updated_at': plan.updated_at.isoformat() if plan.updated_at else None
        })
    return jsonify(result)

@app.route('/api/production-plans', methods=['POST'])
def save_production_plan():
    """保存产量计划"""
    data = request.json
    
    # 检查是否已存在相同产品的计划
    existing_plan = ProductionPlan.query.filter_by(product=data['product']).first()
    
    if existing_plan:
        # 更新现有计划
        existing_plan.process1 = data.get('process1', '')
        existing_plan.qty1 = data.get('qty1', 0)
        existing_plan.process2 = data.get('process2', '')
        existing_plan.qty2 = data.get('qty2', 0)
        existing_plan.process3 = data.get('process3', '')
        existing_plan.qty3 = data.get('qty3', 0)
        existing_plan.process4 = data.get('process4', '')
        existing_plan.qty4 = data.get('qty4', 0)
        existing_plan.updated_at = datetime.utcnow()
    else:
        # 创建新计划
        plan = ProductionPlan(
            product=data['product'],
            process1=data.get('process1', ''),
            qty1=data.get('qty1', 0),
            process2=data.get('process2', ''),
            qty2=data.get('qty2', 0),
            process3=data.get('process3', ''),
            qty3=data.get('qty3', 0),
            process4=data.get('process4', ''),
            qty4=data.get('qty4', 0)
        )
        db.session.add(plan)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/production-plans/<int:plan_id>', methods=['DELETE'])
def delete_production_plan(plan_id):
    """删除产量计划"""
    plan = ProductionPlan.query.get_or_404(plan_id)
    db.session.delete(plan)
    db.session.commit()
    return jsonify({'success': True})

# 工序管理API
@app.route('/api/processes')
def get_processes():
    """获取所有工序"""
    processes = Process.query.order_by(Process.name).all()
    result = []
    for process in processes:
        result.append({
            'id': process.id,
            'name': process.name,
            'description': process.description,
            'created_at': process.created_at.isoformat() if process.created_at else None
        })
    return jsonify(result)

@app.route('/api/processes', methods=['POST'])
def add_process():
    """添加工序"""
    data = request.json
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': '工序名称不能为空'}), 400
    
    # 检查工序名称是否已存在
    existing_process = Process.query.filter_by(name=name).first()
    if existing_process:
        return jsonify({'success': False, 'message': '工序名称已存在'}), 400
    
    process = Process(name=name, description=description)
    db.session.add(process)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '工序添加成功'})

@app.route('/api/processes/<int:process_id>', methods=['DELETE'])
def delete_process(process_id):
    """删除工序"""
    process = Process.query.get_or_404(process_id)
    
    # 检查是否有记录使用此工序
    records_using_process = ProductionRecord.query.filter(
        (ProductionRecord.process == process.name)
    ).count()
    
    if records_using_process > 0:
        return jsonify({'success': False, 'message': f'无法删除，有 {records_using_process} 条记录正在使用此工序'}), 400
    
    # 检查是否有产量计划使用此工序
    plans_using_process = ProductionPlan.query.filter(
        (ProductionPlan.process1 == process.name) |
        (ProductionPlan.process2 == process.name) |
        (ProductionPlan.process3 == process.name) |
        (ProductionPlan.process4 == process.name)
    ).count()
    
    if plans_using_process > 0:
        return jsonify({'success': False, 'message': f'无法删除，有 {plans_using_process} 个产量计划正在使用此工序'}), 400
    
    db.session.delete(process)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '工序删除成功'})

# 产品规格管理API
@app.route('/api/products')
def get_products():
    """获取所有产品规格"""
    products = Product.query.all()
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'created_at': product.created_at.isoformat() if product.created_at else None
        })
    return jsonify(result)

@app.route('/api/products', methods=['POST'])
def add_product():
    """添加产品规格"""
    data = request.json
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'error': '产品规格名称不能为空'}), 400
    
    # 检查是否已存在
    existing_product = Product.query.filter_by(name=name).first()
    if existing_product:
        return jsonify({'error': '产品规格已存在'}), 400
    
    product = Product(name=name, description=description)
    db.session.add(product)
    db.session.commit()
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'created_at': product.created_at.isoformat() if product.created_at else None
    })

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """删除产品规格"""
    product = Product.query.get_or_404(product_id)
    
    # 检查是否有记录使用此产品规格
    records_using_product = ProductionRecord.query.filter_by(product=product.name).count()
    if records_using_product > 0:
        return jsonify({'success': False, 'message': f'无法删除，有 {records_using_product} 条记录正在使用此产品规格'}), 400
    
    # 检查是否有产量计划使用此产品规格
    plans_using_product = ProductionPlan.query.filter_by(product=product.name).count()
    if plans_using_product > 0:
        return jsonify({'success': False, 'message': f'无法删除，有 {plans_using_product} 个产量计划正在使用此产品规格'}), 400
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '产品规格删除成功'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # 获取端口号
    port = int(os.environ.get('PORT', 5000))
    
    # 生产环境使用gunicorn，开发环境使用Flask内置服务器
    if os.environ.get('FLASK_ENV') == 'production':
        print(f"🚀 阳昶产量记录管理系统启动中...")
        print(f"📊 访问地址: http://localhost:{port}")
        print(f"🔧 运行模式: 生产环境")
        app.run(host='0.0.0.0', port=port)
    else:
        print(f"🚀 阳昶产量记录管理系统启动中...")
        print(f"📊 访问地址: http://localhost:{port}")
        print(f"🔧 运行模式: 开发环境")
        print(f"💡 提示: 按 Ctrl+C 停止服务器")
        app.run(debug=True, host='0.0.0.0', port=port)
