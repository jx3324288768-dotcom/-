import csv
import json
import os
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont


APP_TITLE = "产量记录"
CSV_FILE = "records.csv"
STATE_FILE = "app_state.json"


def get_app_dir() -> str:
    # 使用脚本所在目录作为应用数据目录
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_file_path(name: str) -> str:
    return os.path.join(get_app_dir(), name)


def load_state() -> dict:
    state_path = get_file_path(STATE_FILE)
    if not os.path.exists(state_path):
        return {}
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f) or {}
    except Exception:
        return {}


def save_state(state: dict) -> None:
    state_path = get_file_path(STATE_FILE)
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def is_first_run() -> bool:
    data = load_state()
    return not bool(data.get('first_run_completed'))


def mark_first_run_completed() -> None:
    data = load_state()
    data["first_run_completed"] = True
    save_state(data)


def center_window(window: tk.Tk) -> None:
    window.update_idletasks()
    w = window.winfo_width()
    h = window.winfo_height()
    # 若尚未布局完成，给一个基础尺寸
    if w <= 1 or h <= 1:
        w, h = 800, 500
        window.geometry(f"{w}x{h}")
        window.update_idletasks()
        w = window.winfo_width()
        h = window.winfo_height()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    x = int((sw - w) / 2)
    y = int((sh - h) / 2)
    window.geometry(f"{w}x{h}+{x}+{y}")


class ProductionApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)

        # 内存中的完整数据集，用于过滤和保存
        self.all_records = []  # List[Dict[str, str]]: {date,product,process,qty,note,name,position}
        # 顶部个人信息
        self.var_name = tk.StringVar()
        self.var_position = tk.StringVar()
        # 人员名单：name -> position
        self.employees = {}
        self.current_filter = {"start_month": None, "start_day": None, "end_month": None, "end_day": None, "name": None, "product": None, "process": None}
        
        # 弹窗状态跟踪
        self.open_windows = {}  # 跟踪已打开的弹窗

        self._build_ui()
        self._load_records()
        
        # 绑定快捷键
        self.root.bind('<Control-s>', lambda e: self.save_all_records())

        if is_first_run():
            center_window(self.root)
            mark_first_run_completed()

    def _build_ui(self) -> None:
        # 人员管理（新增/删除）
        manage = ttk.Frame(self.root, padding=(12, 8, 12, 0))
        manage.grid(row=0, column=0, sticky="ew")
        ttk.Label(manage, text="新增姓名").pack(side=tk.LEFT)
        self.var_new_name = tk.StringVar()
        ent_new_name = ttk.Entry(manage, textvariable=self.var_new_name, width=12)
        ent_new_name.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Label(manage, text="职位").pack(side=tk.LEFT)
        self.var_new_position = tk.StringVar()
        ent_new_pos = ttk.Entry(manage, textvariable=self.var_new_position, width=12)
        ent_new_pos.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(manage, text="添加人员", command=self.on_add_employee).pack(side=tk.LEFT)
        ttk.Button(manage, text="删除所选人员", command=self.on_delete_selected_employee).pack(side=tk.LEFT, padx=(8, 0))
        # 按要求移除“保存个人信息”按钮，姓名与职位仅随记录保存

        # 顶部表单区域（仅日期 + 添加记录）
        form = ttk.Frame(self.root, padding=(12, 8, 12, 6))
        form.grid(row=1, column=0, sticky="ew")
        self.root.columnconfigure(0, weight=1)

        ttk.Label(form, text="日期 (YYYY-MM-DD)").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.var_date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ent_date = ttk.Entry(form, textvariable=self.var_date, width=18)
        ent_date.grid(row=0, column=1, sticky="w")

        # 按钮
        btns = ttk.Frame(self.root, padding=(12, 6, 12, 6))
        btns.grid(row=2, column=0, sticky="ew")
        btn_add = ttk.Button(btns, text="添加记录", command=self.on_add)
        btn_add.pack(side=tk.LEFT)
        btn_del = ttk.Button(btns, text="删除选中", command=self.on_delete)
        btn_del.pack(side=tk.LEFT, padx=(8, 0))
        btn_save = ttk.Button(btns, text="保存 (Ctrl+S)", command=self.save_all_records)
        btn_save.pack(side=tk.LEFT, padx=(8, 0))

        # 筛选区域（日期范围与统计）
        filter_bar = ttk.Frame(self.root, padding=(12, 0, 12, 6))
        filter_bar.grid(row=3, column=0, sticky="ew")
        
        # 左侧：日期范围筛选（垂直布局）
        date_filter_frame = ttk.Frame(filter_bar)
        date_filter_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        # 是否启用日期筛选
        self.var_enable_date = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(date_filter_frame, text="启用日期筛选", variable=self.var_enable_date)
        chk.pack(anchor=tk.W)
        
        # 开始日期行
        start_date_frame = ttk.Frame(date_filter_frame)
        start_date_frame.pack(anchor=tk.W, pady=(4, 2))
        ttk.Label(start_date_frame, text="从").pack(side=tk.LEFT)
        self.var_start_year = tk.StringVar()
        self.cbo_start_year = ttk.Combobox(start_date_frame, textvariable=self.var_start_year, width=6, state="readonly",
                                          values=[str(i) for i in range(2020, 2031)])
        self.cbo_start_year.pack(side=tk.LEFT, padx=(4, 2))
        ttk.Label(start_date_frame, text="年").pack(side=tk.LEFT)
        self.var_start_month = tk.StringVar()
        self.cbo_start_month = ttk.Combobox(start_date_frame, textvariable=self.var_start_month, width=4, state="readonly",
                                           values=[str(i) for i in range(1, 13)])
        self.cbo_start_month.pack(side=tk.LEFT, padx=(4, 2))
        ttk.Label(start_date_frame, text="月").pack(side=tk.LEFT)
        self.var_start_day = tk.StringVar()
        self.cbo_start_day = ttk.Combobox(start_date_frame, textvariable=self.var_start_day, width=4, state="readonly",
                                         values=[str(i) for i in range(1, 32)])
        self.cbo_start_day.pack(side=tk.LEFT, padx=(4, 2))
        ttk.Label(start_date_frame, text="日").pack(side=tk.LEFT)
        
        # 结束日期行（与开始日期对齐）
        end_date_frame = ttk.Frame(date_filter_frame)
        end_date_frame.pack(anchor=tk.W, pady=(2, 4))
        ttk.Label(end_date_frame, text="到").pack(side=tk.LEFT)
        self.var_end_year = tk.StringVar()
        self.cbo_end_year = ttk.Combobox(end_date_frame, textvariable=self.var_end_year, width=6, state="readonly",
                                        values=[str(i) for i in range(2020, 2031)])
        self.cbo_end_year.pack(side=tk.LEFT, padx=(4, 2))
        ttk.Label(end_date_frame, text="年").pack(side=tk.LEFT)
        self.var_end_month = tk.StringVar()
        self.cbo_end_month = ttk.Combobox(end_date_frame, textvariable=self.var_end_month, width=4, state="readonly",
                                         values=[str(i) for i in range(1, 13)])
        self.cbo_end_month.pack(side=tk.LEFT, padx=(4, 2))
        ttk.Label(end_date_frame, text="月").pack(side=tk.LEFT)
        self.var_end_day = tk.StringVar()
        self.cbo_end_day = ttk.Combobox(end_date_frame, textvariable=self.var_end_day, width=4, state="readonly",
                                       values=[str(i) for i in range(1, 32)])
        self.cbo_end_day.pack(side=tk.LEFT, padx=(4, 2))
        ttk.Label(end_date_frame, text="日").pack(side=tk.LEFT)
        
        # 筛选按钮
        btn_filter = ttk.Button(date_filter_frame, text="筛选", command=self.on_filter)
        btn_filter.pack(anchor=tk.W, pady=(4, 0))
        # 姓名筛选
        ttk.Label(filter_bar, text="姓名").pack(side=tk.LEFT)
        self.var_filter_name = tk.StringVar()
        self.cbo_filter_name = ttk.Combobox(filter_bar, textvariable=self.var_filter_name, width=12, state="readonly")
        self.cbo_filter_name.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Button(filter_bar, text="浏览", command=lambda: self._show_name_browser()).pack(side=tk.LEFT, padx=(0, 12))
        
        # 产品规格筛选
        ttk.Label(filter_bar, text="产品规格").pack(side=tk.LEFT)
        self.var_filter_product = tk.StringVar()
        self.cbo_filter_product = ttk.Combobox(filter_bar, textvariable=self.var_filter_product, width=12, state="readonly")
        self.cbo_filter_product.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Button(filter_bar, text="浏览", command=lambda: self._show_product_browser()).pack(side=tk.LEFT, padx=(0, 12))
        
        # 工序筛选
        ttk.Label(filter_bar, text="工序").pack(side=tk.LEFT)
        self.var_filter_process = tk.StringVar()
        self.cbo_filter_process = ttk.Combobox(filter_bar, textvariable=self.var_filter_process, width=12, state="readonly")
        self.cbo_filter_process.pack(side=tk.LEFT, padx=(4, 12))
        
        # 调机师傅筛选
        ttk.Label(filter_bar, text="调机师傅:").pack(side=tk.LEFT, padx=(0, 4))
        self.var_filter_adjustment_master = tk.StringVar(value="全部")
        self.cbo_filter_adjustment_master = ttk.Combobox(filter_bar, textvariable=self.var_filter_adjustment_master, width=12, state="readonly")
        self.cbo_filter_adjustment_master.pack(side=tk.LEFT, padx=(4, 12))
        
        btn_clear = ttk.Button(filter_bar, text="清除筛选", command=self.on_clear_filter)
        btn_clear.pack(side=tk.LEFT, padx=(8, 12))
        self.var_total = tk.StringVar(value="合计数量: 0")
        ttk.Label(filter_bar, textvariable=self.var_total).pack(side=tk.LEFT)
        
        # 添加平均产能稼动率和平均时间稼动率显示
        self.var_avg_capacity_rate = tk.StringVar(value="平均产能稼动率: 0.00%")
        ttk.Label(filter_bar, textvariable=self.var_avg_capacity_rate).pack(side=tk.LEFT, padx=(20, 0))
        
        self.var_avg_time_rate = tk.StringVar(value="平均时间稼动率: 0.00%")
        ttk.Label(filter_bar, textvariable=self.var_avg_time_rate).pack(side=tk.LEFT, padx=(20, 0))

        # 表格
        table_frame = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        table_frame.grid(row=4, column=0, sticky="nsew")
        self.root.rowconfigure(4, weight=1)

        columns = ("date", "name", "position", "product", "process", "theoretical_runtime", "actual_runtime", "single_time", "theoretical_qty", "actual_qty", "total_weight", "unit_weight", "tare_weight", "capacity_rate", "time_rate", "downtime_duration", "adjustment_time", "adjustment_master")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=16)
        self.tree.heading("date", text="日期")
        self.tree.heading("name", text="姓名")
        self.tree.heading("position", text="职位")
        self.tree.heading("product", text="产品规格")
        self.tree.heading("process", text="工序")
        self.tree.heading("theoretical_runtime", text="理论运行时长(分钟)")
        self.tree.heading("actual_runtime", text="实际运行时长(分钟)")
        self.tree.heading("single_time", text="单个时间(秒)")
        self.tree.heading("theoretical_qty", text="理论数量")
        self.tree.heading("actual_qty", text="实际数量")
        self.tree.heading("total_weight", text="总重")
        self.tree.heading("unit_weight", text="单重")
        self.tree.heading("tare_weight", text="去皮重量")
        self.tree.heading("capacity_rate", text="产能稼动率")
        self.tree.heading("time_rate", text="时间稼动率")
        self.tree.heading("downtime_duration", text="异常停机时长(分钟)")
        self.tree.heading("adjustment_time", text="计划停机时长(分钟)")
        self.tree.heading("adjustment_master", text="调机师傅")
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("name", width=100, anchor="w")
        self.tree.column("position", width=100, anchor="w")
        self.tree.column("product", width=140, anchor="w")
        self.tree.column("process", width=140, anchor="w")
        self.tree.column("theoretical_runtime", width=120, anchor="center")
        self.tree.column("actual_runtime", width=120, anchor="center")
        self.tree.column("single_time", width=90, anchor="e")
        self.tree.column("theoretical_qty", width=90, anchor="e")
        self.tree.column("actual_qty", width=80, anchor="e")
        self.tree.column("total_weight", width=90, anchor="e")
        self.tree.column("unit_weight", width=90, anchor="e")
        self.tree.column("tare_weight", width=90, anchor="e")
        self.tree.column("capacity_rate", width=100, anchor="center")
        self.tree.column("time_rate", width=100, anchor="center")
        self.tree.column("downtime_duration", width=120, anchor="center")
        self.tree.column("adjustment_time", width=120, anchor="center")
        self.tree.column("adjustment_master", width=100, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        # Treeview 行高样式与字体
        self.style = ttk.Style(self.root)
        try:
            self._tv_font = tkfont.nametofont('TkDefaultFont')
            self._line_space = int(self._tv_font.metrics('linespace')) or 16
        except Exception:
            self._tv_font = None
            self._line_space = 16

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 单元格编辑
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.tree.bind('<Button-3>', self.on_tree_right_click)  # 右键菜单
        self.tree.bind('<Button-1>', self.on_tree_left_click)  # 左键单击事件
        self._editor = None  # 当前单元格编辑控件
        self._editor_var = None
        
        # 注释数据存储
        self.comments = {}  # 存储注释数据，格式：{(record_key, column_key): comment_text}
        # 记录映射：row_id -> record_key
        self.row_to_record_map = {}  # 格式：{row_id: record_key}
        
        # 工具提示相关
        self.tooltip = None
        self.current_tooltip_item = None
        self.current_comment_display = None  # 当前显示的注释

    def _get_record_key(self, record: dict) -> str:
        """生成记录的唯一标识符"""
        # 使用日期、姓名、产品规格、工序等关键字段生成唯一标识
        date = record.get('date', '')
        name = record.get('name', '')
        product = record.get('product', '')
        process = record.get('process', '')
        return f"{date}|{name}|{product}|{process}"

    def _restore_comments_for_row(self, row_id: str, record_key: str) -> None:
        """为指定行恢复注释显示"""
        # 检查该记录是否有注释
        for column_key in ('downtime_duration', 'adjustment_time'):
            comment_key = (record_key, column_key)
            if comment_key in self.comments:
                # 恢复注释标记
                self._update_cell_comment_indicator(row_id, column_key)

    def _load_records(self) -> None:
        path = get_file_path(CSV_FILE)
        self.all_records = []
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 兼容旧CSV：若存在 item 字段则拆分到 product/process（均为同值或空）
                        item_legacy = row.get('item', '')
                        product = row.get('product', '') or item_legacy
                        process = row.get('process', '')
                        name_val = row.get('name', '')
                        position_val = row.get('position', '')
                        total_weight = row.get('total_weight', '')
                        unit_weight = row.get('unit_weight', '')
                        tare_weight = row.get('tare_weight', '')
                        single_time = row.get('single_time', '')
                        theoretical_qty = row.get('theoretical_qty', '')
                        actual_qty = row.get('actual_qty', '')
                        capacity_rate = row.get('capacity_rate', '')
                        time_rate = row.get('time_rate', '')
                        master = row.get('master', '')
                        downtime_duration = row.get('downtime_duration', '')
                        theoretical_runtime = row.get('theoretical_runtime', '')  # 动态计算
                        actual_runtime = row.get('actual_runtime', '')
                        adjustment_time = row.get('adjustment_time', '')
                        adjustment_master = row.get('adjustment_master', '')
                        self.all_records.append({
                            'date': row.get('date', ''),
                            'name': name_val,
                            'position': position_val,
                            'product': product,
                            'process': process,
                            'theoretical_runtime': theoretical_runtime,
                            'actual_runtime': actual_runtime,
                            'single_time': single_time,
                            'theoretical_qty': theoretical_qty,
                            'actual_qty': actual_qty,
                            'total_weight': total_weight,
                            'unit_weight': unit_weight,
                            'tare_weight': tare_weight,
                            'capacity_rate': capacity_rate,
                            'time_rate': time_rate,
                            'downtime_duration': downtime_duration,
                            'adjustment_time': adjustment_time,
                            'adjustment_master': adjustment_master,
                        })
            except Exception as e:
                messagebox.showerror("读取失败", f"无法读取CSV: {e}")
        # 加载人员名单
        self._load_employees()
        self._refresh_form_name_options()
        # 不再从状态文件读取/保存个人信息
        # 刷新筛选选项与表格
        self._update_filter_options()
        self.refresh_table(self.all_records)

    def save_all_records(self) -> None:
        # 在保存前先根据当前表格重构 all_records，以保证删除后的同步
        self._rebuild_all_records_from_table()
        path = get_file_path(CSV_FILE)
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(
                    f, fieldnames=['date', 'name', 'position', 'product', 'process', 'theoretical_runtime', 'actual_runtime', 'single_time', 'theoretical_qty', 'actual_qty', 'total_weight', 'unit_weight', 'tare_weight', 'capacity_rate', 'time_rate', 'downtime_duration', 'adjustment_time', 'adjustment_master']
                )
                writer.writeheader()
                writer.writerows(self.all_records)
            messagebox.showinfo("保存成功", f"已保存到 {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("保存失败", f"无法写入CSV: {e}")

    def on_add(self) -> None:
        date_str = (self.var_date.get() or '').strip()
        name_val = (self.var_name.get() or '').strip()
        position_val = (self.var_position.get() or '').strip()

        # 校验日期
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showwarning("输入有误", "日期格式应为 YYYY-MM-DD")
            return

        # 不再强制校验姓名与职位，允许先添加再在表格中选择


        # 加入内存数据（先留空，由用户在表格内填写）
        self.all_records.append({
            'date': date_str,
            'name': name_val,
            'position': position_val,
            'product': '',
            'process': '',
            'theoretical_runtime': '',  # 动态计算
            'actual_runtime': '',
            'single_time': '',
            'theoretical_qty': '',
            'actual_qty': '',
            'total_weight': '',
            'unit_weight': '',
            'tare_weight': '',
            'capacity_rate': '',
            'time_rate': '',
            'downtime_duration': '',
            'adjustment_time': '',
            'adjustment_master': '',
        })
        # 添加后显示新记录：清除筛选，展示全部
        self.on_clear_filter()
        # 更新筛选选项以包含新的产品/工序
        self._update_filter_options()
        # 聚焦到新行的产品单元格并开始编辑
        try:
            last_item = self.tree.get_children('')[-1]
            self.tree.selection_set(last_item)
            self.tree.focus(last_item)
            self.start_edit_cell(last_item, 'product')
        except Exception:
            pass

    def on_delete(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的记录")
            return
        if not messagebox.askyesno("确认", f"确认删除选中的 {len(selection)} 条记录？"):
            return
        for iid in selection:
            self.tree.delete(iid)
        # 从表格重建内存数据
        self._rebuild_all_records_from_table()

    # ===== 筛选与表格刷新 =====
    def _update_filter_options(self) -> None:
        # 更新姓名筛选项（员工名单 ∪ 记录中已有姓名）
        names_from_records = {r.get('name','') for r in self.all_records if r.get('name','')}
        names = sorted(set(self.employees.keys()) | names_from_records)
        self.cbo_filter_name['values'] = ['全部'] + names
        
        # 更新产品规格筛选项
        products = sorted({r.get('product','') for r in self.all_records if r.get('product','')})
        self.cbo_filter_product['values'] = ['全部'] + products
        
        # 更新工序筛选项
        processes = sorted({r.get('process','') for r in self.all_records if r.get('process','')})
        self.cbo_filter_process['values'] = ['全部'] + processes
        
        # 更新调机师傅筛选项（只显示职位是调机师傅的姓名）
        adjustment_masters = []
        for name, position in self.employees.items():
            if position == '调机师傅':
                adjustment_masters.append(name)
        # 添加记录中已有的调机师傅
        masters_from_records = {r.get('adjustment_master','') for r in self.all_records if r.get('adjustment_master','')}
        adjustment_masters.extend(masters_from_records)
        adjustment_masters = sorted(set(adjustment_masters))
        self.cbo_filter_adjustment_master['values'] = ['全部'] + adjustment_masters

    # ===== 员工名单管理 =====
    def _employees_file(self) -> str:
        return get_file_path('employees.json')

    def _load_employees(self) -> None:
        path = self._employees_file()
        self.employees = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.employees = json.load(f) or {}
            except Exception:
                self.employees = {}

    def _save_employees(self) -> None:
        try:
            with open(self._employees_file(), 'w', encoding='utf-8') as f:
                json.dump(self.employees, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _refresh_form_name_options(self) -> None:
        names = sorted(self.employees.keys())
        # 顶部姓名下拉可能已被移除，存在才更新
        if hasattr(self, 'cbo_form_name') and self.cbo_form_name is not None:
            self.cbo_form_name['values'] = names
            # 若当前选择的名字不在列表中，清空职位
            cur = self.var_name.get()
            if cur in self.employees:
                self.var_position.set(self.employees[cur])
            else:
                self.var_position.set('')

    def on_form_name_selected(self, event=None) -> None:
        name = self.var_name.get()
        self.var_position.set(self.employees.get(name, ''))

    # 人员浏览对话框
    def open_employee_browser(self) -> None:
        win = tk.Toplevel(self.root)
        win.title('人员浏览')
        win.transient(self.root)
        win.grab_set()
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text='搜索').pack(anchor='w')
        var_q = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=var_q)
        ent.pack(fill=tk.X, pady=(0,6))
        lst = tk.Listbox(frm, height=12)
        lst.pack(fill=tk.BOTH, expand=True)
        # 数据
        data = sorted(self.employees.items(), key=lambda x: x[0])
        def refresh():
            q = (var_q.get() or '').strip()
            lst.delete(0, tk.END)
            for n, p in data:
                if not q or (q in n) or (q in p):
                    lst.insert(tk.END, f"{n}  -  {p}")
        refresh()
        def on_select(event=None):
            try:
                idx = lst.curselection()[0]
                text = lst.get(idx)
                name = text.split('  -  ')[0]
            except Exception:
                name = ''
            if name:
                self.var_filter_name.set(name)
                self.on_filter()
                win.destroy()
        lst.bind('<Double-1>', on_select)
        ent.bind('<KeyRelease>', lambda e: refresh())
        ttk.Button(frm, text='确定', command=on_select).pack(side=tk.RIGHT, pady=(6,0))
        ttk.Button(frm, text='取消', command=win.destroy).pack(side=tk.RIGHT, padx=(0,6), pady=(6,0))

    def on_add_employee(self) -> None:
        name = (self.var_new_name.get() or '').strip()
        pos = (self.var_new_position.get() or '').strip()
        if not name or not pos:
            messagebox.showwarning('输入有误', '请填写新增姓名与职位')
            return
        self.employees[name] = pos
        self._save_employees()
        self._refresh_form_name_options()
        self.var_new_name.set('')
        self.var_new_position.set('')

    def on_delete_selected_employee(self) -> None:
        # 弹出选择对话框供用户选择要删除的人员
        self._open_employee_delete_dialog()

    def _open_employee_delete_dialog(self) -> None:
        win = tk.Toplevel(self.root)
        win.title('删除人员')
        win.transient(self.root)
        win.grab_set()
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text='搜索').pack(anchor='w')
        var_q = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=var_q)
        ent.pack(fill=tk.X, pady=(0,6))
        lst = tk.Listbox(frm, height=12)
        lst.pack(fill=tk.BOTH, expand=True)

        data = sorted(self.employees.items(), key=lambda x: x[0])
        def refresh():
            q = (var_q.get() or '').strip()
            lst.delete(0, tk.END)
            for n, p in data:
                if not q or (q in n) or (q in p):
                    lst.insert(tk.END, f"{n}  -  {p}")
        refresh()

        def do_delete():
            try:
                idx = lst.curselection()[0]
                text = lst.get(idx)
                name = text.split('  -  ')[0]
            except Exception:
                name = ''
            if not name:
                messagebox.showinfo('提示', '请先选择人员')
                return
            if not messagebox.askyesno('确认', f'确认删除人员：{name}？'):
                return
            self.employees.pop(name, None)
            self._save_employees()
            self._refresh_form_name_options()
            # 更新筛选姓名下拉与对话框数据
            self._update_filter_options()
            # 从浏览器中移除此项并关闭
            win.destroy()

        btn_bar = ttk.Frame(frm)
        btn_bar.pack(fill=tk.X, pady=(6,0))
        ttk.Button(btn_bar, text='删除', command=do_delete).pack(side=tk.RIGHT)
        ttk.Button(btn_bar, text='取消', command=win.destroy).pack(side=tk.RIGHT, padx=(0,6))
        ent.bind('<KeyRelease>', lambda e: refresh())


    def on_filter(self) -> None:
        name = (self.var_filter_name.get() or '').strip()
        product = (self.var_filter_product.get() or '').strip()
        process = (self.var_filter_process.get() or '').strip()
        adjustment_master = (self.var_filter_adjustment_master.get() or '').strip()
        
        # 如果选择的是"全部"，则视为空值
        if name == '全部':
            name = ''
        if product == '全部':
            product = ''
        if process == '全部':
            process = ''
        if adjustment_master == '全部':
            adjustment_master = ''
            
        if self.var_enable_date.get():
            start_year = (self.var_start_year.get() or '').strip()
            start_month = (self.var_start_month.get() or '').strip()
            start_day = (self.var_start_day.get() or '').strip()
            end_year = (self.var_end_year.get() or '').strip()
            end_month = (self.var_end_month.get() or '').strip()
            end_day = (self.var_end_day.get() or '').strip()
        else:
            start_year = start_month = start_day = end_year = end_month = end_day = None
        self.current_filter = {
            "start_year": start_year if start_year else None,
            "start_month": start_month if start_month else None,
            "start_day": start_day if start_day else None,
            "end_year": end_year if end_year else None,
            "end_month": end_month if end_month else None,
            "end_day": end_day if end_day else None,
            "name": name if name else None,
            "product": product if product else None,
            "process": process if process else None,
            "adjustment_master": adjustment_master if adjustment_master else None
        }
        self._refresh_by_current_filter()

    def on_clear_filter(self) -> None:
        self.var_filter_name.set('全部')
        self.var_filter_product.set('全部')
        self.var_filter_process.set('全部')
        self.var_filter_adjustment_master.set('全部')
        self.var_enable_date.set(False)
        self.var_start_year.set('')
        self.var_start_month.set('')
        self.var_start_day.set('')
        self.var_end_year.set('')
        self.var_end_month.set('')
        self.var_end_day.set('')
        self.current_filter = {"start_year": None, "start_month": None, "start_day": None, "end_year": None, "end_month": None, "end_day": None, "name": None, "product": None, "process": None, "adjustment_master": None}
        self.refresh_table(self.all_records)

    def _refresh_by_current_filter(self) -> None:
        f = self.current_filter
        if not f.get("start_year") and not f.get("start_month") and not f.get("start_day") and not f.get("end_year") and not f.get("end_month") and not f.get("end_day") and not f.get('name') and not f.get('product') and not f.get('process') and not f.get('adjustment_master'):
            self.refresh_table(self.all_records)
            return
        filtered = []
        for r in self.all_records:
            d = r.get('date', '')
            if len(d) < 7:
                continue
            
            # 日期范围筛选逻辑
            date_ok = True
            if f.get('start_year') or f.get('start_month') or f.get('start_day') or f.get('end_year') or f.get('end_month') or f.get('end_day'):
                # 解析记录中的日期 (格式: YYYY-MM-DD)
                if len(d) >= 10:
                    record_year = int(d[0:4])
                    record_month = int(d[5:7])
                    record_day = int(d[8:10])
                else:
                    date_ok = False
                
                if date_ok:
                    # 检查开始日期
                    if f.get('start_year') and f.get('start_month') and f.get('start_day'):
                        start_year = int(f['start_year'])
                        start_month = int(f['start_month'])
                        start_day = int(f['start_day'])
                        if (record_year < start_year or 
                            (record_year == start_year and record_month < start_month) or 
                            (record_year == start_year and record_month == start_month and record_day < start_day)):
                            date_ok = False
                    elif f.get('start_year') and f.get('start_month'):
                        start_year = int(f['start_year'])
                        start_month = int(f['start_month'])
                        if (record_year < start_year or 
                            (record_year == start_year and record_month < start_month)):
                            date_ok = False
                    elif f.get('start_year'):
                        start_year = int(f['start_year'])
                        if record_year < start_year:
                            date_ok = False
                    elif f.get('start_month') and f.get('start_day'):
                        start_month = int(f['start_month'])
                        start_day = int(f['start_day'])
                        if record_month < start_month or (record_month == start_month and record_day < start_day):
                            date_ok = False
                    elif f.get('start_month'):
                        start_month = int(f['start_month'])
                        if record_month < start_month:
                            date_ok = False
                    elif f.get('start_day'):
                        start_day = int(f['start_day'])
                        if record_day < start_day:
                            date_ok = False
                    
                    # 检查结束日期
                    if date_ok and (f.get('end_year') or f.get('end_month') or f.get('end_day')):
                        if f.get('end_year') and f.get('end_month') and f.get('end_day'):
                            end_year = int(f['end_year'])
                            end_month = int(f['end_month'])
                            end_day = int(f['end_day'])
                            if (record_year > end_year or 
                                (record_year == end_year and record_month > end_month) or 
                                (record_year == end_year and record_month == end_month and record_day > end_day)):
                                date_ok = False
                        elif f.get('end_year') and f.get('end_month'):
                            end_year = int(f['end_year'])
                            end_month = int(f['end_month'])
                            if (record_year > end_year or 
                                (record_year == end_year and record_month > end_month)):
                                date_ok = False
                        elif f.get('end_year'):
                            end_year = int(f['end_year'])
                            if record_year > end_year:
                                date_ok = False
                        elif f.get('end_month') and f.get('end_day'):
                            end_month = int(f['end_month'])
                            end_day = int(f['end_day'])
                            if record_month > end_month or (record_month == end_month and record_day > end_day):
                                date_ok = False
                        elif f.get('end_month'):
                            end_month = int(f['end_month'])
                            if record_month > end_month:
                                date_ok = False
                        elif f.get('end_day'):
                            end_day = int(f['end_day'])
                            if record_day > end_day:
                                date_ok = False
            
            name_ok = True if not f.get('name') else (r.get('name', '') == f['name'])
            product_ok = True if not f.get('product') else (r.get('product', '') == f['product'])
            process_ok = True if not f.get('process') else (r.get('process', '') == f['process'])
            adjustment_master_ok = True if not f.get('adjustment_master') else (r.get('adjustment_master', '') == f['adjustment_master'])
            if date_ok and name_ok and product_ok and process_ok and adjustment_master_ok:
                filtered.append(r)
        self.refresh_table(filtered)

    def refresh_table(self, records) -> None:
        # 清空现有表格和映射
        for iid in self.tree.get_children(''):
            self.tree.delete(iid)
        self.row_to_record_map.clear()
        
        # 填充
        max_product_lines = 1
        for r in records:
            product_text = r.get('product', '')
            wrapped = self._wrap_text_to_column(product_text, 'product')
            if wrapped:
                lines = wrapped.count('\n') + 1
                if lines > max_product_lines:
                    max_product_lines = lines
            
            # 插入记录并获取row_id
            row_id = self.tree.insert('', tk.END, values=(
                r.get('date', ''),
                r.get('name', ''),
                r.get('position', ''),
                wrapped,
                r.get('process', ''),
                r.get('theoretical_runtime', ''),
                r.get('actual_runtime', ''),
                r.get('single_time', ''),
                r.get('theoretical_qty', ''),
                r.get('actual_qty', ''),
                r.get('total_weight', ''),
                r.get('unit_weight', ''),
                r.get('tare_weight', ''),
                r.get('capacity_rate', ''),
                r.get('time_rate', ''),
                r.get('downtime_duration', ''),
                r.get('adjustment_time', ''),
                r.get('adjustment_master', ''),
            ))
            
            # 建立row_id到record_key的映射
            record_key = self._get_record_key(r)
            self.row_to_record_map[row_id] = record_key
            
            # 恢复注释显示
            self._restore_comments_for_row(row_id, record_key)
            
        self._update_tree_rowheight(max_product_lines)
        # 统计
        total = 0
        capacity_rates = []
        time_rates = []
        
        for r in records:
            # 计算合计实际数量
            q = str(r.get('actual_qty', '')).strip()
            if q.isdigit():
                total += int(q)
            
            # 收集产能稼动率数据
            capacity_rate_str = str(r.get('capacity_rate', '')).strip()
            if capacity_rate_str and capacity_rate_str.endswith('%'):
                try:
                    # 去掉%符号并转换为数字
                    capacity_rate = float(capacity_rate_str[:-1])
                    capacity_rates.append(capacity_rate)
                except ValueError:
                    pass
            
            # 收集时间稼动率数据
            time_rate_str = str(r.get('time_rate', '')).strip()
            if time_rate_str and time_rate_str.endswith('%'):
                try:
                    # 去掉%符号并转换为数字
                    time_rate = float(time_rate_str[:-1])
                    time_rates.append(time_rate)
                except ValueError:
                    pass
        
        # 更新合计实际数量
        self.var_total.set(f"合计实际数量: {total}")
        
        # 计算平均产能稼动率
        if capacity_rates:
            avg_capacity_rate = sum(capacity_rates) / len(capacity_rates)
            self.var_avg_capacity_rate.set(f"平均产能稼动率: {avg_capacity_rate:.2f}%")
        else:
            self.var_avg_capacity_rate.set("平均产能稼动率: 0.00%")
        
        # 计算平均时间稼动率
        if time_rates:
            avg_time_rate = sum(time_rates) / len(time_rates)
            self.var_avg_time_rate.set(f"平均时间稼动率: {avg_time_rate:.2f}%")
        else:
            self.var_avg_time_rate.set("平均时间稼动率: 0.00%")

    def _rebuild_all_records_from_table(self) -> None:
        # 基于当前表格重建记录，按列名读取，避免列顺序依赖
        rows = []
        for iid in self.tree.get_children(''):
            # 反保存时，需要将"产品规格"列中的换行去掉还原原文
            product_display = self.tree.set(iid, 'product')
            product_raw = product_display.replace('\n', ' ') if product_display else ''
            record = {
                'date': self.tree.set(iid, 'date'),
                'name': self.tree.set(iid, 'name'),
                'position': self.tree.set(iid, 'position'),
                'product': product_raw,
                'process': self.tree.set(iid, 'process'),
                'theoretical_runtime': self.tree.set(iid, 'theoretical_runtime'),
                'actual_runtime': self.tree.set(iid, 'actual_runtime'),
                'single_time': self.tree.set(iid, 'single_time'),
                'theoretical_qty': self.tree.set(iid, 'theoretical_qty'),
                'actual_qty': self.tree.set(iid, 'actual_qty'),
                'total_weight': self.tree.set(iid, 'total_weight'),
                'unit_weight': self.tree.set(iid, 'unit_weight'),
                'tare_weight': self.tree.set(iid, 'tare_weight'),
                'capacity_rate': self.tree.set(iid, 'capacity_rate'),
                'time_rate': self.tree.set(iid, 'time_rate'),
                'downtime_duration': self.tree.set(iid, 'downtime_duration').replace(' 📝', ''),
                'adjustment_time': self.tree.set(iid, 'adjustment_time').replace(' 📝', ''),
                'adjustment_master': self.tree.set(iid, 'adjustment_master'),
            }
            rows.append(record)
            
            # 更新映射关系
            record_key = self._get_record_key(record)
            self.row_to_record_map[iid] = record_key

        self.all_records = rows
        # 更新筛选选项（可能有新年份出现或删除）
        self._update_filter_options()

    # ====== 表格内编辑 ======
    def on_tree_double_click(self, event) -> None:
        # 如果已有编辑器在运行，先销毁它
        if self._editor is not None:
            self._destroy_editor()
            
        region = self.tree.identify('region', event.x, event.y)
        if region != 'cell':
            return
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)  # e.g. '#1'
        col_index = int(col_id.replace('#', '')) - 1
        columns = self.tree['columns']
        if col_index < 0 or col_index >= len(columns):
            return
        column_key = columns[col_index]
        # 允许编辑：姓名(下拉)、产品规格、工序、单个时间、实际数量（可手填）、权重、异常停机时长、计划停机时长、调机师傅(下拉)
        if column_key not in ('name', 'product', 'process', 'single_time', 'actual_qty', 'total_weight', 'unit_weight', 'tare_weight', 'downtime_duration', 'adjustment_time', 'adjustment_master'):
            return
        
        # 延迟启动编辑器，确保双击事件完全处理完毕
        def delayed_start_edit():
            self.start_edit_cell(row_id, column_key)
        
        self.root.after(50, delayed_start_edit)

    def on_tree_right_click(self, event) -> None:
        """处理表格右键点击事件"""
        # 获取点击的单元格
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        # 获取列索引
        col_index = int(column.replace('#', '')) - 1
        columns = self.tree['columns']
        if col_index < 0 or col_index >= len(columns):
            return
        
        column_key = columns[col_index]
        
        # 只对异常停机时长和计划停机时长列显示右键菜单
        if column_key not in ('downtime_duration', 'adjustment_time'):
            return
        
        # 创建右键菜单
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # 检查是否已有注释
        record_key = self.row_to_record_map.get(item)
        if not record_key:
            return
        comment_key = (record_key, column_key)
        has_comment = comment_key in self.comments
        
        if has_comment:
            context_menu.add_command(label="编辑注释", command=lambda: self._edit_comment(item, column_key))
            context_menu.add_command(label="删除注释", command=lambda: self._delete_comment(item, column_key))
        else:
            context_menu.add_command(label="添加注释", command=lambda: self._add_comment(item, column_key))
        
        # 显示菜单
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def _add_comment(self, row_id: str, column_key: str) -> None:
        """添加注释"""
        self._edit_comment(row_id, column_key)

    def _edit_comment(self, row_id: str, column_key: str) -> None:
        """编辑注释"""
        # 获取记录键
        record_key = self.row_to_record_map.get(row_id)
        if not record_key:
            return
        
        # 获取现有注释
        comment_key = (record_key, column_key)
        current_comment = self.comments.get(comment_key, "")
        
        # 创建注释编辑对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑注释")
        dialog.geometry("400x300")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # 创建文本输入框
        text_frame = ttk.Frame(dialog, padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(text_frame, text="注释内容:").pack(anchor=tk.W)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, height=10)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        text_widget.insert(tk.END, current_comment)
        text_widget.focus_set()
        
        # 创建按钮框架
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill=tk.X)
        
        def save_comment():
            comment_text = text_widget.get(1.0, tk.END).strip()
            if comment_text:
                self.comments[comment_key] = comment_text
                # 如果当前显示的是这个注释，更新显示内容
                if self.current_comment_display == comment_key:
                    self._update_current_comment_display(comment_text)
            else:
                # 如果注释为空，删除注释
                self.comments.pop(comment_key, None)
                # 如果当前显示的是这个注释，隐藏显示
                if self.current_comment_display == comment_key:
                    self._hide_comment_display()
            
            # 更新单元格显示
            self._update_cell_comment_indicator(row_id, column_key)
            dialog.destroy()
        
        def cancel_edit():
            dialog.destroy()
        
        ttk.Button(button_frame, text="保存", command=save_comment).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_edit).pack(side=tk.RIGHT)
        
        # 绑定快捷键
        dialog.bind('<Return>', lambda e: save_comment())
        dialog.bind('<Escape>', lambda e: cancel_edit())

    def _delete_comment(self, row_id: str, column_key: str) -> None:
        """删除注释"""
        # 获取记录键
        record_key = self.row_to_record_map.get(row_id)
        if not record_key:
            return
            
        comment_key = (record_key, column_key)
        if comment_key in self.comments:
            del self.comments[comment_key]
            # 如果当前显示的是这个注释，隐藏显示
            if self.current_comment_display == comment_key:
                self._hide_comment_display()
            # 更新单元格显示
            self._update_cell_comment_indicator(row_id, column_key)

    def _update_cell_comment_indicator(self, row_id: str, column_key: str) -> None:
        """更新单元格的注释指示器"""
        # 获取记录键
        record_key = self.row_to_record_map.get(row_id)
        if not record_key:
            return
            
        comment_key = (record_key, column_key)
        has_comment = comment_key in self.comments
        
        # 获取当前单元格的值
        current_value = self.tree.set(row_id, column_key)
        
        if has_comment:
            # 添加注释标记（在值后面添加特殊字符）
            if not current_value.endswith(' 📝'):
                new_value = current_value + ' 📝'
                self.tree.set(row_id, column_key, new_value)
        else:
            # 移除注释标记
            if current_value.endswith(' 📝'):
                new_value = current_value[:-2]  # 移除 ' 📝'
                self.tree.set(row_id, column_key, new_value)

    def on_tree_left_click(self, event) -> None:
        """处理左键单击事件，显示/隐藏注释"""
        # 获取点击的单元格
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        # 获取列索引
        col_index = int(column.replace('#', '')) - 1
        columns = self.tree['columns']
        if col_index < 0 or col_index >= len(columns):
            return
        
        column_key = columns[col_index]
        
        # 只对异常停机时长和计划停机时长列处理单击事件
        if column_key not in ('downtime_duration', 'adjustment_time'):
            return
        
        # 检查是否有注释
        record_key = self.row_to_record_map.get(item)
        if not record_key:
            return
            
        comment_key = (record_key, column_key)
        if comment_key not in self.comments:
            return
        
        # 如果当前显示的注释就是点击的这个，则隐藏
        if self.current_comment_display == comment_key:
            self._hide_comment_display()
        else:
            # 显示新的注释
            self._show_comment_display(event, self.comments[comment_key], comment_key)

    def _show_comment_display(self, event, text: str, comment_key) -> None:
        """显示注释内容"""
        self._hide_comment_display()  # 先隐藏之前的注释显示
        
        # 创建注释显示窗口
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_attributes('-topmost', True)  # 保持在最前面
        
        # 计算位置：在鼠标位置的右上角
        tooltip_x = event.x_root + 20
        tooltip_y = event.y_root - 10
        
        # 确保注释显示不会超出屏幕边界
        screen_width = self.tooltip.winfo_screenwidth()
        screen_height = self.tooltip.winfo_screenheight()
        
        # 创建注释显示内容
        frame = ttk.Frame(self.tooltip, relief=tk.SOLID, borderwidth=2)
        frame.pack()
        
        # 设置背景色
        frame.configure(style='Comment.TFrame')
        
        # 创建标签显示文本（直接显示注释内容，不显示标题）
        label = ttk.Label(frame, text=text, wraplength=300, justify=tk.LEFT, font=('Arial', 9))
        label.pack(padx=8, pady=6)
        
        # 配置样式
        style = ttk.Style()
        style.configure('Comment.TFrame', background='lightblue')
        style.configure('Comment.TLabel', background='lightblue', foreground='black')
        
        # 更新窗口以获取实际大小
        self.tooltip.update_idletasks()
        
        # 获取注释显示的实际大小
        tooltip_width = self.tooltip.winfo_width()
        tooltip_height = self.tooltip.winfo_height()
        
        # 调整位置，确保不超出屏幕
        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = event.x_root - tooltip_width - 20
        if tooltip_y < 0:
            tooltip_y = event.y_root + 20
        
        # 设置最终位置
        self.tooltip.wm_geometry(f"+{tooltip_x}+{tooltip_y}")
        
        # 记录当前显示的注释
        self.current_comment_display = comment_key

    def _hide_comment_display(self) -> None:
        """隐藏注释显示"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        self.current_comment_display = None

    def _update_current_comment_display(self, new_text: str) -> None:
        """更新当前显示的注释内容"""
        if self.tooltip and self.tooltip.winfo_exists():
            # 销毁当前显示窗口
            self.tooltip.destroy()
            self.tooltip = None
            
            # 重新创建显示窗口，使用新的文本内容
            # 获取鼠标当前位置（使用一个默认位置）
            x = self.root.winfo_rootx() + 100
            y = self.root.winfo_rooty() + 100
            
            # 创建模拟事件对象
            class MockEvent:
                def __init__(self, x_root, y_root):
                    self.x_root = x_root
                    self.y_root = y_root
            
            mock_event = MockEvent(x, y)
            self._show_comment_display(mock_event, new_text, self.current_comment_display)

    def start_edit_cell(self, row_id: str, column_key: str) -> None:
        # 销毁已有编辑器
        self._destroy_editor()
        col_index = self.tree['columns'].index(column_key) + 1
        bbox = self.tree.bbox(row_id, f'#{col_index}')
        if not bbox:
            return
        x, y, w, h = bbox
        value = self.tree.set(row_id, column_key)
        self._editor_var = tk.StringVar(value=value)
        # 为不同列选择不同编辑器：姓名/稼动率/停机原因使用下拉，其它使用输入框
        if column_key == 'name':
            # 姓名下拉来源：员工名单 ∪ 记录中已有姓名
            names_from_records = {self.tree.set(i, 'name') for i in self.tree.get_children('') if self.tree.set(i, 'name')}
            name_values = sorted(set(self.employees.keys()) | names_from_records)
            editor = ttk.Combobox(self.tree, textvariable=self._editor_var, state='readonly', values=name_values)
        elif column_key == 'downtime_duration':
            # 停机时长特殊处理：创建时间输入编辑器
            self._create_downtime_duration_editor(row_id, column_key, x, y, w, h, value)
            return
        elif column_key == 'capacity_rate':
            # 产能稼动率特殊处理：自动计算
            self._create_capacity_rate_editor(row_id, column_key, x, y, w, h, value)
            return
        elif column_key == 'time_rate':
            # 时间稼动率特殊处理：自动计算
            self._create_time_rate_editor(row_id, column_key, x, y, w, h, value)
            return
        elif column_key == 'theoretical_runtime':
            # 理论运行时长特殊处理：自动计算
            self._create_theoretical_runtime_editor(row_id, column_key, x, y, w, h, value)
            return
        elif column_key == 'actual_runtime':
            # 实际运行时长特殊处理：自动计算
            self._create_actual_runtime_editor(row_id, column_key, x, y, w, h, value)
            return
        elif column_key == 'adjustment_time':
            # 调机时长特殊处理：创建分钟输入编辑器
            self._create_adjustment_time_editor(row_id, column_key, x, y, w, h, value)
            return
        elif column_key == 'adjustment_master':
            # 调机师傅特殊处理：创建下拉选择编辑器
            self._create_adjustment_master_editor(row_id, column_key, x, y, w, h, value)
            return
        elif column_key == 'single_time':
            # 单个时间特殊处理：只接受数字输入
            self._create_single_time_editor(row_id, column_key, x, y, w, h, value)
            return
        else:
            editor = ttk.Entry(self.tree, textvariable=self._editor_var)
        editor.place(x=x, y=y, width=w, height=h)
        editor.focus_set()

        def commit(event=None):
            new_val = self._editor_var.get().strip()
            # 校验
            if column_key in ('product', 'process', 'master'):
                if new_val == '':
                    label = '产品规格' if column_key=='product' else ('工序' if column_key=='process' else '负责师傅')
                    messagebox.showwarning('输入有误', f'请填写{label}')
                    return
            if column_key == 'name':
                # 选择姓名后联动职位列
                pos = self.employees.get(new_val, '')
                self.tree.set(row_id, 'position', pos)
            # 写入表格（产品规格列需要包裹）
            display_val = new_val
            if column_key == 'product':
                display_val = self._wrap_text_to_column(new_val, 'product')
            self.tree.set(row_id, column_key, display_val)
            # 若编辑了权重，自动计算实际数量 = (总重-去皮)/单重（四舍五入）
            if column_key in ('total_weight', 'unit_weight', 'tare_weight'):
                try:
                    tw = float(self.tree.set(row_id, 'total_weight') or 0) if (self.tree.set(row_id, 'total_weight') or '').strip() != '' else 0.0
                    uw = float(self.tree.set(row_id, 'unit_weight') or 0) if (self.tree.set(row_id, 'unit_weight') or '').strip() != '' else 0.0
                    tar = float(self.tree.set(row_id, 'tare_weight') or 0) if (self.tree.set(row_id, 'tare_weight') or '').strip() != '' else 0.0
                except ValueError:
                    # 非法数字直接不计算
                    tw = uw = tar = 0.0
                qty_val = ''
                if uw > 0:
                    # 四舍五入取整（ROUND_HALF_UP）
                    from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, getcontext
                    getcontext().prec = 28
                    try:
                        qty_calc = (Decimal(str(tw)) - Decimal(str(tar))) / Decimal(str(uw))
                        qty_int = int(qty_calc.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
                        if qty_int < 0:
                            qty_int = 0
                        qty_val = str(qty_int)
                    except (InvalidOperation, ZeroDivisionError):
                        qty_val = ''
                self.tree.set(row_id, 'actual_qty', qty_val)
            # 同步数据
            self._rebuild_all_records_from_table()
            self._destroy_editor()
            # 根据产品规格的行数更新行高
            if column_key == 'product':
                max_lines = 1
                for iid2 in self.tree.get_children(''):
                    txt = self.tree.set(iid2, 'product')
                    if txt:
                        lines = txt.count('\n') + 1
                        if lines > max_lines:
                            max_lines = lines
                self._update_tree_rowheight(max_lines)

        def cancel(event=None):
            self._destroy_editor()

        editor.bind('<Return>', commit)
        editor.bind('<KP_Enter>', commit)
        editor.bind('<Escape>', cancel)
        editor.bind('<FocusOut>', commit)
        self._editor = editor

    def _wrap_text_to_column(self, text: str, column_key: str) -> str:
        # 根据列宽按像素自动断行，返回含换行符的文本
        if not text:
            return text
        try:
            col_width = int(self.tree.column(column_key, 'width'))
            target_width = max(20, col_width - 12)
        except Exception:
            target_width = 120
        font = self._tv_font
        if not font:
            # 退化：按字符估算宽度
            max_chars = max(5, target_width // 7)
            lines = []
            s = text
            while s:
                lines.append(s[:max_chars])
                s = s[max_chars:]
            return "\n".join(lines)
        lines = []
        current = ''
        for ch in text:
            trial = current + ch
            try:
                w = font.measure(trial)
            except Exception:
                w = len(trial) * 7
            if w <= target_width:
                current = trial
            else:
                lines.append(current)
                current = ch
        if current:
            lines.append(current)
        return "\n".join(lines)

    def _update_tree_rowheight(self, max_lines: int) -> None:
        # 依据最大行数调整 Treeview 行高（全局生效）
        max_lines = max(1, int(max_lines))
        row_h = self._line_space * max_lines + 6
        try:
            self.style.configure('Treeview', rowheight=row_h)
        except Exception:
            pass



    def _create_downtime_duration_editor(self, row_id: str, column_key: str, x: int, y: int, w: int, h: int, value: str) -> None:
        """创建停机时长编辑器，支持输入分钟数"""
        # 销毁已有编辑器
        self._destroy_editor()
        
        # 创建主框架
        editor_frame = ttk.Frame(self.tree)
        editor_frame.place(x=x, y=y, width=w, height=h)
        
        # 创建输入框，支持输入分钟数
        # 移除注释标记（📝）用于编辑
        clean_value = value.replace(' 📝', '') if value else ''
        self._editor_var = tk.StringVar(value=clean_value)
        editor = ttk.Entry(editor_frame, textvariable=self._editor_var, width=10)
        editor.pack(fill=tk.BOTH, expand=True)
        
        # 存储引用
        self._editor = editor_frame
        
        # 设置焦点
        editor.focus_set()
        editor.select_range(0, tk.END)
        
        def commit(event=None):
            if self._editor_var is None:
                return
            new_val = self._editor_var.get().strip()
            
            # 如果输入了内容，验证是否为数字
            if new_val:
                try:
                    minutes = int(new_val)
                    if minutes < 0:
                        messagebox.showwarning('输入有误', '分钟数不能为负数')
                        return
                    final_value = str(minutes)
                except ValueError:
                    messagebox.showwarning('输入有误', '请输入有效的分钟数（整数）')
                    return
            else:
                final_value = ''
            
            # 写入表格
            self.tree.set(row_id, column_key, final_value)
            # 重新添加注释标记（如果有注释的话）
            self._update_cell_comment_indicator(row_id, column_key)
            # 自动计算实际运行时长
            self._calculate_actual_runtime(row_id)
            # 自动计算理论数量
            self._calculate_theoretical_qty(row_id)
            # 同步数据
            self._rebuild_all_records_from_table()
            self._destroy_editor()
        
        def cancel(event=None):
            self._destroy_editor()
        
        # 绑定事件
        editor.bind('<Return>', commit)
        editor.bind('<KP_Enter>', commit)
        editor.bind('<Escape>', cancel)
        
        # 失去焦点时自动保存
        def on_focus_out(event=None):
            # 延迟执行，避免在切换焦点时立即保存
            self.root.after(200, commit)
        
        editor.bind('<FocusOut>', on_focus_out)

    def _create_capacity_rate_editor(self, row_id: str, column_key: str, x: int, y: int, w: int, h: int, value: str) -> None:
        """创建产能稼动率编辑器，自动计算"""
        # 销毁已有编辑器
        self._destroy_editor()
        
        # 创建主框架
        editor_frame = ttk.Frame(self.tree)
        editor_frame.place(x=x, y=y, width=w, height=h)
        
        # 创建只读输入框
        self._editor_var = tk.StringVar()
        editor = ttk.Entry(editor_frame, textvariable=self._editor_var, state='readonly', width=10)
        editor.pack(fill=tk.BOTH, expand=True)
        
        # 存储引用
        self._editor = editor_frame
        
        # 计算并显示产能稼动率
        self._calculate_capacity_rate(row_id)

    def _create_time_rate_editor(self, row_id: str, column_key: str, x: int, y: int, w: int, h: int, value: str) -> None:
        """创建时间稼动率编辑器，自动计算"""
        # 销毁已有编辑器
        self._destroy_editor()
        
        # 创建主框架
        editor_frame = ttk.Frame(self.tree)
        editor_frame.place(x=x, y=y, width=w, height=h)
        
        # 创建只读输入框
        self._editor_var = tk.StringVar()
        editor = ttk.Entry(editor_frame, textvariable=self._editor_var, state='readonly', width=10)
        editor.pack(fill=tk.BOTH, expand=True)
        
        # 存储引用
        self._editor = editor_frame
        
        # 计算并显示时间稼动率
        self._calculate_time_rate(row_id)

    def _create_theoretical_runtime_editor(self, row_id: str, column_key: str, x: int, y: int, w: int, h: int, value: str) -> None:
        """创建理论运行时长编辑器，自动计算"""
        # 销毁已有编辑器
        self._destroy_editor()
        
        # 创建主框架
        editor_frame = ttk.Frame(self.tree)
        editor_frame.place(x=x, y=y, width=w, height=h)
        
        # 创建只读输入框，显示计算结果
        self._editor_var = tk.StringVar(value=value)
        editor = ttk.Entry(editor_frame, textvariable=self._editor_var, width=10, state='readonly')
        editor.pack(fill=tk.BOTH, expand=True)
        
        # 存储引用
        self._editor = editor_frame
        
        # 自动计算理论运行时长
        self._calculate_theoretical_runtime(row_id)
        
        def commit(event=None):
            # 理论运行时长是自动计算的，不需要手动保存
            self._destroy_editor()
        
        def cancel(event=None):
            self._destroy_editor()
        
        # 绑定事件
        editor.bind('<Return>', commit)
        editor.bind('<KP_Enter>', commit)
        editor.bind('<Escape>', cancel)

    def _create_actual_runtime_editor(self, row_id: str, column_key: str, x: int, y: int, w: int, h: int, value: str) -> None:
        """创建实际运行时长编辑器，自动计算"""
        # 销毁已有编辑器
        self._destroy_editor()
        
        # 创建主框架
        editor_frame = ttk.Frame(self.tree)
        editor_frame.place(x=x, y=y, width=w, height=h)
        
        # 创建只读输入框，显示计算结果
        self._editor_var = tk.StringVar(value=value)
        editor = ttk.Entry(editor_frame, textvariable=self._editor_var, width=10, state='readonly')
        editor.pack(fill=tk.BOTH, expand=True)
        
        # 存储引用
        self._editor = editor_frame
        
        # 自动计算理论运行时长和实际运行时长
        self._calculate_actual_runtime(row_id)
        
        def commit(event=None):
            # 实际运行时长是自动计算的，不需要手动保存
            self._destroy_editor()
        
        def cancel(event=None):
            self._destroy_editor()
        
        # 绑定事件
        editor.bind('<Return>', commit)
        editor.bind('<KP_Enter>', commit)
        editor.bind('<Escape>', cancel)

    def _create_adjustment_time_editor(self, row_id: str, column_key: str, x: int, y: int, w: int, h: int, value: str) -> None:
        """创建调机时长编辑器，支持输入分钟数"""
        # 销毁已有编辑器
        self._destroy_editor()
        
        # 创建主框架
        editor_frame = ttk.Frame(self.tree)
        editor_frame.place(x=x, y=y, width=w, height=h)
        
        # 创建输入框，支持输入分钟数
        # 移除注释标记（📝）用于编辑
        clean_value = value.replace(' 📝', '') if value else ''
        self._editor_var = tk.StringVar(value=clean_value)
        editor = ttk.Entry(editor_frame, textvariable=self._editor_var, width=10)
        editor.pack(fill=tk.BOTH, expand=True)
        
        # 存储引用
        self._editor = editor_frame
        
        # 设置焦点
        editor.focus_set()
        editor.select_range(0, tk.END)
        
        def commit(event=None):
            if self._editor_var is None:
                return
            new_val = self._editor_var.get().strip()
            
            # 如果输入了内容，验证是否为数字
            if new_val:
                try:
                    minutes = int(new_val)
                    if minutes < 0:
                        messagebox.showwarning('输入有误', '调机时长不能为负数')
                        return
                    final_value = str(minutes)
                except ValueError:
                    messagebox.showwarning('输入有误', '请输入有效的调机时长（整数分钟）')
                    return
            else:
                final_value = ''
            
            # 写入表格
            self.tree.set(row_id, column_key, final_value)
            # 重新添加注释标记（如果有注释的话）
            self._update_cell_comment_indicator(row_id, column_key)
            # 自动计算理论运行时长和实际运行时长
            self._calculate_actual_runtime(row_id)
            # 自动计算理论数量
            self._calculate_theoretical_qty(row_id)
            # 同步数据
            self._rebuild_all_records_from_table()
            self._destroy_editor()
        
        def cancel(event=None):
            self._destroy_editor()
        
        # 绑定事件
        editor.bind('<Return>', commit)
        editor.bind('<KP_Enter>', commit)
        editor.bind('<Escape>', cancel)
        
        # 失去焦点时自动保存
        def on_focus_out(event=None):
            # 延迟执行，避免在切换焦点时立即保存
            self.root.after(200, commit)
        
        editor.bind('<FocusOut>', on_focus_out)

    def _create_adjustment_master_editor(self, row_id: str, column_key: str, x: int, y: int, w: int, h: int, value: str) -> None:
        """创建调机师傅编辑器，下拉选择职位是调机师傅的姓名"""
        # 销毁已有编辑器
        self._destroy_editor()
        
        # 创建主框架
        editor_frame = ttk.Frame(self.tree)
        editor_frame.place(x=x, y=y, width=w, height=h)
        
        # 获取调机师傅列表（职位是调机师傅的姓名）
        adjustment_masters = []
        for name, position in self.employees.items():
            if position == '调机师傅':
                adjustment_masters.append(name)
        
        # 添加空选项
        adjustment_masters.insert(0, '')
        
        # 创建下拉选择框
        self._editor_var = tk.StringVar(value=value)
        editor = ttk.Combobox(editor_frame, textvariable=self._editor_var, 
                             values=adjustment_masters, state='readonly', width=15)
        editor.pack(fill=tk.BOTH, expand=True)
        
        # 存储引用
        self._editor = editor_frame
        
        # 设置焦点
        editor.focus_set()
        
        def commit(event=None):
            if self._editor_var is None:
                return
            new_val = self._editor_var.get().strip()
            # 写入表格
            self.tree.set(row_id, column_key, new_val)
            # 同步数据
            self._rebuild_all_records_from_table()
            self._destroy_editor()
        
        def cancel(event=None):
            self._destroy_editor()
        
        # 绑定事件
        editor.bind('<Return>', commit)
        editor.bind('<KP_Enter>', commit)
        editor.bind('<Escape>', cancel)

    def _create_single_time_editor(self, row_id: str, column_key: str, x: int, y: int, w: int, h: int, value: str) -> None:
        """创建单个时间编辑器，只接受数字输入（秒）"""
        # 销毁已有编辑器
        self._destroy_editor()
        
        # 创建主框架
        editor_frame = ttk.Frame(self.tree)
        editor_frame.place(x=x, y=y, width=w, height=h)
        
        # 创建输入框，只接受数字输入
        self._editor_var = tk.StringVar(value=value)
        editor = ttk.Entry(editor_frame, textvariable=self._editor_var, width=10)
        editor.pack(fill=tk.BOTH, expand=True)
        
        # 存储引用
        self._editor = editor_frame
        
        # 设置焦点
        editor.focus_set()
        editor.select_range(0, tk.END)
        
        def commit(event=None):
            new_val = self._editor_var.get().strip()
            
            # 如果输入了内容，验证是否为数字
            if new_val:
                try:
                    seconds = int(new_val)
                    if seconds < 0:
                        messagebox.showwarning('输入有误', '单个时间不能为负数')
                        return
                    final_value = str(seconds)
                except ValueError:
                    messagebox.showwarning('输入有误', '请输入有效的单个时间（整数秒）')
                    return
            else:
                final_value = ''
            
            # 写入表格
            self.tree.set(row_id, column_key, final_value)
            # 自动计算理论数量
            self._calculate_theoretical_qty(row_id)
            # 同步数据
            self._rebuild_all_records_from_table()
            self._destroy_editor()
        
        def cancel(event=None):
            self._destroy_editor()
        
        # 绑定事件
        editor.bind('<Return>', commit)
        editor.bind('<KP_Enter>', commit)
        editor.bind('<Escape>', cancel)
        
        # 失去焦点时自动保存
        def on_focus_out(event=None):
            # 延迟执行，避免在切换焦点时立即保存
            self.root.after(200, commit)
        
        editor.bind('<FocusOut>', on_focus_out)

    def _calculate_theoretical_runtime(self, row_id: str) -> None:
        """计算理论运行时长 = 480 - 调机时长"""
        try:
            # 获取调机时长
            adjustment_time = self.tree.set(row_id, 'adjustment_time').replace(' 📝', '')
            if not adjustment_time:
                adjustment_time = '0'
            
            # 计算理论运行时长
            adjustment_minutes = int(adjustment_time)
            theoretical_minutes = 480 - adjustment_minutes
            
            # 确保不为负数
            if theoretical_minutes < 0:
                theoretical_minutes = 0
            
            # 更新表格
            self.tree.set(row_id, 'theoretical_runtime', str(theoretical_minutes))
            # 更新时间稼动率
            self._calculate_time_rate(row_id)
            
        except (ValueError, TypeError):
            # 如果计算失败，设置为480
            self.tree.set(row_id, 'theoretical_runtime', '480')
            self._calculate_time_rate(row_id)

    def _calculate_actual_runtime(self, row_id: str) -> None:
        """计算实际运行时长 = 理论运行时长 - 停机时长"""
        try:
            # 先计算理论运行时长
            self._calculate_theoretical_runtime(row_id)
            
            # 获取理论运行时长
            theoretical_runtime = self.tree.set(row_id, 'theoretical_runtime')
            if not theoretical_runtime:
                theoretical_runtime = '480'
            
            # 获取停机时长
            downtime_duration = self.tree.set(row_id, 'downtime_duration').replace(' 📝', '')
            if not downtime_duration:
                downtime_duration = '0'
            
            # 计算实际运行时长
            theoretical_minutes = int(theoretical_runtime)
            downtime_minutes = int(downtime_duration)
            actual_minutes = theoretical_minutes - downtime_minutes
            
            # 确保不为负数
            if actual_minutes < 0:
                actual_minutes = 0
            
            # 更新表格
            self.tree.set(row_id, 'actual_runtime', str(actual_minutes))
            # 更新时间稼动率
            self._calculate_time_rate(row_id)
            
        except (ValueError, TypeError):
            # 如果计算失败，设置为空
            self.tree.set(row_id, 'actual_runtime', '')
            self._calculate_time_rate(row_id)

    def _calculate_theoretical_qty(self, row_id: str) -> None:
        """计算理论数量 = 实际运行时长 / 单个实际"""
        try:
            # 获取实际运行时长（分钟）
            actual_runtime = self.tree.set(row_id, 'actual_runtime')
            if not actual_runtime:
                return
            
            # 获取单个实际（秒）
            single_time = self.tree.set(row_id, 'single_time')
            if not single_time:
                return
            
            # 计算理论数量
            actual_minutes = int(actual_runtime)
            single_seconds = int(single_time)
            
            if single_seconds > 0:
                # 将分钟转换为秒，然后除以单个时间
                actual_seconds = actual_minutes * 60
                theoretical_qty = actual_seconds / single_seconds
                # 四舍五入到整数
                theoretical_qty = round(theoretical_qty)
            else:
                theoretical_qty = 0
            
            # 更新表格
            self.tree.set(row_id, 'theoretical_qty', str(theoretical_qty))
            # 更新产能稼动率
            self._calculate_capacity_rate(row_id)
            
        except (ValueError, TypeError):
            # 如果计算失败，设置为空
            self.tree.set(row_id, 'theoretical_qty', '')
            self._calculate_capacity_rate(row_id)

    def _calculate_capacity_rate(self, row_id: str) -> None:
        """计算产能稼动率 = 实际数量 / 理论数量"""
        try:
            # 获取实际数量
            actual_qty = self.tree.set(row_id, 'actual_qty')
            if not actual_qty:
                actual_qty = '0'
            
            # 获取理论数量
            theoretical_qty = self.tree.set(row_id, 'theoretical_qty')
            if not theoretical_qty:
                theoretical_qty = '0'
            
            # 计算产能稼动率
            actual = int(actual_qty)
            theoretical = int(theoretical_qty)
            
            if theoretical > 0:
                capacity_rate = actual / theoretical
                # 转换为百分比，保留2位小数
                capacity_rate_percent = round(capacity_rate * 100, 2)
            else:
                capacity_rate_percent = 0
            
            # 更新表格
            self.tree.set(row_id, 'capacity_rate', f"{capacity_rate_percent}%")
            
        except (ValueError, TypeError):
            # 如果计算失败，设置为空
            self.tree.set(row_id, 'capacity_rate', '')

    def _calculate_time_rate(self, row_id: str) -> None:
        """计算时间稼动率 = 实际运行时长 / 理论运行时长"""
        try:
            # 获取实际运行时长
            actual_runtime = self.tree.set(row_id, 'actual_runtime')
            if not actual_runtime:
                actual_runtime = '0'
            
            # 获取理论运行时长
            theoretical_runtime = self.tree.set(row_id, 'theoretical_runtime')
            if not theoretical_runtime:
                theoretical_runtime = '0'
            
            # 计算时间稼动率
            actual = int(actual_runtime)
            theoretical = int(theoretical_runtime)
            
            if theoretical > 0:
                time_rate = actual / theoretical
                # 转换为百分比，保留2位小数
                time_rate_percent = round(time_rate * 100, 2)
            else:
                time_rate_percent = 0
            
            # 更新表格
            self.tree.set(row_id, 'time_rate', f"{time_rate_percent}%")
            
        except (ValueError, TypeError):
            # 如果计算失败，设置为空
            self.tree.set(row_id, 'time_rate', '')

    def _destroy_editor(self) -> None:
        if self._editor is not None:
            try:
                self._editor.destroy()
            except Exception:
                pass
            self._editor = None
            self._editor_var = None
            # 清理停机时长编辑器的额外引用（简化版本不需要）
            # 清理根窗口的点击事件绑定
            try:
                self.root.unbind('<Button-1>')
            except:
                pass

    # 按要求移除保存个人信息功能


    def _show_product_browser(self) -> None:
        """显示产品规格浏览对话框"""
        self._manage_window("product_browser", self._create_product_browser)

    def _create_product_browser(self) -> tk.Toplevel:
        """创建产品规格浏览窗口"""
        # 获取所有产品规格
        all_products = sorted({r.get('product','') for r in self.all_records if r.get('product','')})
        
        if not all_products:
            messagebox.showinfo("提示", "暂无产品规格信息")
            return None
            
        # 创建浏览窗口
        win = tk.Toplevel(self.root)
        win.title("产品规格浏览")
        win.geometry("500x450")
        win.resizable(True, True)
        
        # 创建主框架
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="产品规格列表：", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # 搜索框
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # 创建带滚动条的列表框
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # 填充数据
        def update_list():
            search_text = search_var.get().lower().strip()
            listbox.delete(0, tk.END)
            # 总是先添加"全部"选项
            listbox.insert(tk.END, "全部")
            if search_text:
                # 有搜索条件时显示过滤结果
                filtered_products = [p for p in all_products if search_text in p.lower()]
            else:
                # 无搜索条件时显示全部数据
                filtered_products = all_products
            for product in filtered_products:
                listbox.insert(tk.END, product)
        
        # 绑定搜索事件
        search_var.trace('w', lambda *args: update_list())
        search_entry.bind('<KeyRelease>', lambda e: update_list())
        
        # 初始填充
        update_list()
        
        # 添加选择按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        def select_product():
            selection = listbox.curselection()
            if selection:
                product = listbox.get(selection[0])
                self.var_filter_product.set(product)
                win.destroy()
            else:
                messagebox.showwarning("提示", "请选择一个产品规格")
        
        ttk.Button(btn_frame, text="选择", command=select_product).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=win.destroy).pack(side=tk.LEFT)
        
        return win

    def _show_name_browser(self) -> None:
        """显示姓名浏览对话框"""
        self._manage_window("name_browser", self._create_name_browser)

    def _create_name_browser(self) -> tk.Toplevel:
        """创建姓名浏览窗口"""
        # 获取所有姓名
        all_names = sorted({r.get('name','') for r in self.all_records if r.get('name','')})
        
        if not all_names:
            messagebox.showinfo("提示", "暂无人员信息")
            return None
            
        # 创建浏览窗口
        win = tk.Toplevel(self.root)
        win.title("姓名浏览")
        win.geometry("500x450")
        win.resizable(True, True)
        
        # 创建主框架
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="姓名列表：", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # 搜索框
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # 创建带滚动条的列表框
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # 填充数据
        def update_list():
            search_text = search_var.get().lower().strip()
            listbox.delete(0, tk.END)
            # 总是先添加"全部"选项
            listbox.insert(tk.END, "全部")
            if search_text:
                # 有搜索条件时显示过滤结果
                filtered_names = [n for n in all_names if search_text in n.lower()]
            else:
                # 无搜索条件时显示全部数据
                filtered_names = all_names
            for name in filtered_names:
                listbox.insert(tk.END, name)
        
        # 绑定搜索事件
        search_var.trace('w', lambda *args: update_list())
        search_entry.bind('<KeyRelease>', lambda e: update_list())
        
        # 初始填充
        update_list()
        
        # 添加选择按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        def select_name():
            selection = listbox.curselection()
            if selection:
                name = listbox.get(selection[0])
                self.var_filter_name.set(name)
                win.destroy()
            else:
                messagebox.showwarning("提示", "请选择一个姓名")
        
        ttk.Button(btn_frame, text="选择", command=select_name).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=win.destroy).pack(side=tk.LEFT)
        
        return win

    def _manage_window(self, window_name: str, window_func) -> None:
        """管理弹窗单例和闪烁提醒"""
        if window_name in self.open_windows and self.open_windows[window_name].winfo_exists():
            # 窗口已存在，闪烁提醒
            window = self.open_windows[window_name]
            self._flash_window(window)
        else:
            # 创建新窗口
            window = window_func()
            self.open_windows[window_name] = window
            
            # 绑定窗口关闭事件，清理状态
            def on_close():
                if window_name in self.open_windows:
                    del self.open_windows[window_name]
                window.destroy()
            
            window.protocol("WM_DELETE_WINDOW", on_close)

    def _flash_window(self, window: tk.Toplevel) -> None:
        """闪烁窗口提醒"""
        original_bg = window.cget('bg')
        flash_colors = ['red', 'yellow', 'red', 'yellow']
        
        def flash_step(step=0):
            if step < len(flash_colors):
                window.configure(bg=flash_colors[step])
                window.after(200, lambda: flash_step(step + 1))
            else:
                window.configure(bg=original_bg)
                window.lift()  # 将窗口提到最前
                window.focus_force()  # 强制获取焦点
        
        flash_step()


def main() -> None:
    root = tk.Tk()
    # 非首次启动不给窗口强设位置，交由首次启动逻辑决定是否居中
    app = ProductionApp(root)
    root.minsize(720, 420)
    root.mainloop()


if __name__ == "__main__":
    main()


