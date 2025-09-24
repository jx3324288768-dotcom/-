// 全局变量
let records = [];
let employees = [];
let currentCommentRecordId = null;
let currentCommentColumn = null;
let currentCommentDisplay = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('newRecordDate').value = today;
    
    // 设置默认日期范围为昨天到今天
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];
    
    document.getElementById('filterStartDate').value = yesterdayStr;
    document.getElementById('filterEndDate').value = today;
    
    loadEmployees();
    loadRecords();
    updateProductOptions(); // 加载产品规格选项
    
    // 自动应用默认的日期范围筛选
    setTimeout(() => {
        applyFilters();
    }, 1000); // 延迟1秒确保数据加载完成
    
    // 设置自动刷新
    setInterval(refreshData, 30000); // 每30秒刷新一次
    
    // 为筛选条件添加变化监听
    const filterInputs = ['filterStartDate', 'filterEndDate', 'filterName', 'filterProduct', 'filterProcess', 'filterAdjustmentMaster'];
    filterInputs.forEach(inputId => {
        const element = document.getElementById(inputId);
        if (element) {
            element.addEventListener('change', function() {
                // 延迟执行筛选，避免频繁请求
                clearTimeout(window.filterTimeout);
                window.filterTimeout = setTimeout(() => {
                    loadRecords();
                }, 300);
            });
        }
    });
    
    // 为编辑模态框中的重量相关字段添加变化监听
    const weightInputs = ['editTotalWeight', 'editTareWeight', 'editUnitWeight'];
    weightInputs.forEach(inputId => {
        const element = document.getElementById(inputId);
        if (element) {
            element.addEventListener('input', calculateActualQty);
        }
    });
    
    // 初始化拖动功能
    initDraggableModal();
    
    // 初始化产量管理
    initProductionManagement();
    
    // 初始化工序管理
    initProcessManagement();
});

// 加载员工数据
async function loadEmployees() {
    try {
        const response = await fetch('/api/employees');
        employees = await response.json();
        updateEmployeeSelects();
    } catch (error) {
        console.error('加载员工数据失败:', error);
    }
}

// 更新员工选择框
function updateEmployeeSelects() {
    const selects = ['newRecordName', 'editName', 'filterName'];
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        const currentValue = select.value;
        select.innerHTML = selectId === 'filterName' ? '<option value="">全部</option>' : '<option value="">选择姓名</option>';
        
        employees.forEach(emp => {
            const option = document.createElement('option');
            option.value = emp.name;
            option.textContent = emp.name;
            select.appendChild(option);
        });
        
        select.value = currentValue;
    });
    
    // 更新调机师傅选择框
    const adjustmentMasterSelect = document.getElementById('editAdjustmentMaster');
    adjustmentMasterSelect.innerHTML = '<option value="">选择调机师傅</option>';
    employees.filter(emp => emp.position === '调机师傅').forEach(emp => {
        const option = document.createElement('option');
        option.value = emp.name;
        option.textContent = emp.name;
        adjustmentMasterSelect.appendChild(option);
    });
}

// 加载记录数据
async function loadRecords() {
    try {
        // 构建筛选参数
        const params = new URLSearchParams();
        const startDate = document.getElementById('filterStartDate').value;
        const endDate = document.getElementById('filterEndDate').value;
        const name = document.getElementById('filterName').value;
        const product = document.getElementById('filterProduct').value;
        const process = document.getElementById('filterProcess').value;
        const adjustmentMaster = document.getElementById('filterAdjustmentMaster').value;
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (name) params.append('name', name);
        if (product) params.append('product', product);
        if (process) params.append('process', process);
        if (adjustmentMaster) params.append('adjustment_master', adjustmentMaster);
        
        const url = '/api/records' + (params.toString() ? '?' + params.toString() : '');
        const response = await fetch(url);
        records = await response.json();
        displayRecords();
        updateFilterOptions();
        calculateStats();
    } catch (error) {
        console.error('加载记录数据失败:', error);
    }
}

// 显示记录
function displayRecords() {
    const tbody = document.getElementById('recordsTableBody');
    tbody.innerHTML = '';
    
    records.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="display: none;" class="checkbox-cell">
                <input type="checkbox" class="record-checkbox" value="${record.id}" onchange="updateBatchDeleteButtons()">
            </td>
            <td>${record.date}</td>
            <td>${record.name}</td>
            <td>${record.position}</td>
            <td>${record.product}</td>
            <td>
                <select class="form-select form-select-sm" onchange="updateRecordProcess(${record.id}, this.value)" data-current-value="${record.process || ''}">
                    <option value="">选择工序</option>
                </select>
            </td>
            <td>${record.theoretical_runtime}</td>
            <td>${record.actual_runtime}</td>
            <td class="editable" onclick="editCell(${record.id}, 'single_time')">${record.single_time}</td>
            <td>${record.theoretical_qty}</td>
            <td class="editable" onclick="editCell(${record.id}, 'actual_qty')">${record.actual_qty}</td>
            <td class="editable" onclick="editCell(${record.id}, 'total_weight')">${record.total_weight}</td>
            <td class="editable" onclick="editCell(${record.id}, 'unit_weight')">${record.unit_weight}</td>
            <td class="editable" onclick="editCell(${record.id}, 'tare_weight')">${record.tare_weight}</td>
            <td>${record.capacity_rate}</td>
            <td>${record.time_rate}</td>
            <td class="editable" onclick="editCell(${record.id}, 'downtime_duration')">
                ${record.downtime_duration}
                <span class="comment-indicator" onclick="toggleComment(${record.id}, 'downtime_duration', event)" ondblclick="editComment(${record.id}, 'downtime_duration', event)" title="单击查看注释，双击编辑注释">📝</span>
            </td>
            <td class="editable" onclick="editCell(${record.id}, 'adjustment_time')">
                ${record.adjustment_time}
                <span class="comment-indicator" onclick="toggleComment(${record.id}, 'adjustment_time', event)" ondblclick="editComment(${record.id}, 'adjustment_time', event)" title="单击查看注释，双击编辑注释">📝</span>
            </td>
            <td class="editable" onclick="editCell(${record.id}, 'adjustment_master')">${record.adjustment_master}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editRecord(${record.id})">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deleteRecord(${record.id})">删除</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 更新筛选选项
function updateFilterOptions() {
    // 并行获取记录数据和工序数据
    Promise.all([
        fetch('/api/records').then(response => response.json()),
        fetch('/api/processes').then(response => response.json())
    ])
        .then(([allRecords, processes]) => {
            const products = [...new Set(allRecords.map(r => r.product).filter(p => p))];
            const processNames = processes.map(p => p.name);
            const names = [...new Set(allRecords.map(r => r.name).filter(n => n))];
            const adjustmentMasters = [...new Set(allRecords.map(r => r.adjustment_master).filter(m => m))];
            
            const productSelect = document.getElementById('filterProduct');
            const processSelect = document.getElementById('filterProcess');
            const nameSelect = document.getElementById('filterName');
            const adjustmentMasterSelect = document.getElementById('filterAdjustmentMaster');
            
            // 保存当前选择的值
            const currentProduct = productSelect.value;
            const currentProcess = processSelect.value;
            const currentName = nameSelect.value;
            const currentAdjustmentMaster = adjustmentMasterSelect.value;
            
            // 更新产品选项
            productSelect.innerHTML = '<option value="">全部</option>';
            products.forEach(product => {
                const option = document.createElement('option');
                option.value = product;
                option.textContent = product;
                productSelect.appendChild(option);
            });
            
            // 更新工序选项
            processSelect.innerHTML = '<option value="">全部</option>';
            processNames.forEach(process => {
                const option = document.createElement('option');
                option.value = process;
                option.textContent = process;
                processSelect.appendChild(option);
            });
            
            // 更新姓名选项
            nameSelect.innerHTML = '<option value="">全部</option>';
            names.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                nameSelect.appendChild(option);
            });
            
            // 更新调机师傅选项
            adjustmentMasterSelect.innerHTML = '<option value="">全部</option>';
            adjustmentMasters.forEach(master => {
                const option = document.createElement('option');
                option.value = master;
                option.textContent = master;
                adjustmentMasterSelect.appendChild(option);
            });
            
            // 恢复之前的选择
            productSelect.value = currentProduct;
            processSelect.value = currentProcess;
            nameSelect.value = currentName;
            adjustmentMasterSelect.value = currentAdjustmentMaster;
            
            
            
            // 更新添加记录的产品规格选择框
            const newRecordProductSelect = document.getElementById('newRecordProduct');
            if (newRecordProductSelect) {
                const currentValue = newRecordProductSelect.value;
                newRecordProductSelect.innerHTML = '<option value="">选择产品规格</option>';
                products.forEach(product => {
                    const option = document.createElement('option');
                    option.value = product;
                    option.textContent = product;
                    newRecordProductSelect.appendChild(option);
                });
                newRecordProductSelect.value = currentValue;
            }
            
            // 更新添加记录的工序选择框
            const newRecordProcessSelect = document.getElementById('newRecordProcess');
            if (newRecordProcessSelect) {
                const currentValue = newRecordProcessSelect.value;
                newRecordProcessSelect.innerHTML = '<option value="">选择工序</option>';
                processNames.forEach(process => {
                    const option = document.createElement('option');
                    option.value = process;
                    option.textContent = process;
                    newRecordProcessSelect.appendChild(option);
                });
                newRecordProcessSelect.value = currentValue;
            }
            
            // 更新记录表格中的工序选择框
            const recordProcessSelects = document.querySelectorAll('select[data-current-value]');
            recordProcessSelects.forEach(select => {
                const currentValue = select.getAttribute('data-current-value');
                select.innerHTML = '<option value="">选择工序</option>';
                processNames.forEach(process => {
                    const option = document.createElement('option');
                    option.value = process;
                    option.textContent = process;
                    select.appendChild(option);
                });
                select.value = currentValue;
            });
            
            // 更新编辑模态框中的工序选择框
            const editProcessSelect = document.getElementById('editProcess');
            if (editProcessSelect) {
                const currentValue = editProcessSelect.value;
                editProcessSelect.innerHTML = '<option value="">选择工序</option>';
                processNames.forEach(process => {
                    const option = document.createElement('option');
                    option.value = process;
                    option.textContent = process;
                    editProcessSelect.appendChild(option);
                });
                editProcessSelect.value = currentValue;
            }
        })
        .catch(error => {
            console.error('更新筛选选项失败:', error);
        });
}

// 计算统计信息
function calculateStats() {
    let totalActualQty = 0;
    let capacityRates = [];
    let timeRates = [];
    
    records.forEach(record => {
        if (record.actual_qty) {
            totalActualQty += parseInt(record.actual_qty) || 0;
        }
        
        if (record.capacity_rate && record.capacity_rate.endsWith('%')) {
            const rate = parseFloat(record.capacity_rate.replace('%', ''));
            if (!isNaN(rate)) capacityRates.push(rate);
        }
        
        if (record.time_rate && record.time_rate.endsWith('%')) {
            const rate = parseFloat(record.time_rate.replace('%', ''));
            if (!isNaN(rate)) timeRates.push(rate);
        }
    });
    
    document.getElementById('totalActualQty').textContent = totalActualQty;
    
    const avgCapacityRate = capacityRates.length > 0 ? 
        (capacityRates.reduce((a, b) => a + b, 0) / capacityRates.length).toFixed(2) : 0;
    document.getElementById('avgCapacityRate').textContent = avgCapacityRate + '%';
    
    const avgTimeRate = timeRates.length > 0 ? 
        (timeRates.reduce((a, b) => a + b, 0) / timeRates.length).toFixed(2) : 0;
    document.getElementById('avgTimeRate').textContent = avgTimeRate + '%';
}

// 添加员工
async function addEmployee() {
    const name = document.getElementById('newEmployeeName').value.trim();
    const position = document.getElementById('newEmployeePosition').value.trim();
    
    if (!name || !position) {
        alert('请填写姓名和职位');
        return;
    }
    
    try {
        const response = await fetch('/api/employees', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, position })
        });
        
        if (response.ok) {
            alert('员工添加成功！');
            document.getElementById('newEmployeeName').value = '';
            document.getElementById('newEmployeePosition').value = '';
            // 更新员工选项
            updateFilterOptions();
            
            // 如果员工管理模态框是打开的，刷新员工列表
            if (document.getElementById('employeeManagementModal').classList.contains('show')) {
                loadEmployeesForManagement();
            }
        } else {
            alert('添加员工失败');
        }
    } catch (error) {
        console.error('添加员工失败:', error);
        alert('添加员工失败');
    }
}

// 添加记录
async function addRecord() {
    const date = document.getElementById('newRecordDate').value;
    const name = document.getElementById('newRecordName').value;
    const product = document.getElementById('newRecordProduct').value;
    const process = document.getElementById('newRecordProcess').value;
    
    console.log('添加记录 - 产品规格:', product); // 调试信息
    
    if (!date || !name) {
        alert('请选择日期和姓名');
        return;
    }
    
    const employee = employees.find(emp => emp.name === name);
    
    try {
        const response = await fetch('/api/records', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date,
                name,
                position: employee ? employee.position : '',
                product: product || '',
                process: process || '',
                theoretical_runtime: '',
                actual_runtime: '',
                single_time: '',
                theoretical_qty: '',
                actual_qty: '',
                total_weight: '',
                unit_weight: '',
                tare_weight: '',
                capacity_rate: '',
                time_rate: '',
                downtime_duration: '',
                adjustment_time: '',
                adjustment_master: ''
            })
        });
        
        if (response.ok) {
            // 清空表单（保留日期）
            document.getElementById('newRecordName').value = '';
            document.getElementById('newRecordPosition').value = '';
            document.getElementById('newRecordProductSearch').value = '';
            document.getElementById('newRecordProduct').value = '';
            document.getElementById('newRecordProcess').value = '';
            document.getElementById('productionPlanInfo').style.display = 'none';
            
            loadRecords();
            // 实时更新产量计划信息
            refreshProductionPlanInfo();
        } else {
            alert('添加记录失败');
        }
    } catch (error) {
        console.error('添加记录失败:', error);
        alert('添加记录失败');
    }
}

// 编辑记录
function editRecord(recordId) {
    const record = records.find(r => r.id === recordId);
    if (!record) return;
    
    document.getElementById('editRecordId').value = record.id;
    document.getElementById('editDate').value = record.date;
    document.getElementById('editName').value = record.name;
    document.getElementById('editPosition').value = record.position;
    document.getElementById('editProduct').value = record.product;
    document.getElementById('editProcess').value = record.process;
    document.getElementById('editSingleTime').value = record.single_time;
    document.getElementById('editActualQty').value = record.actual_qty;
    document.getElementById('editTotalWeight').value = record.total_weight;
    document.getElementById('editUnitWeight').value = record.unit_weight;
    document.getElementById('editTareWeight').value = record.tare_weight;
    document.getElementById('editDowntimeDuration').value = record.downtime_duration;
    document.getElementById('editAdjustmentTime').value = record.adjustment_time;
    document.getElementById('editAdjustmentMaster').value = record.adjustment_master;
    
    // 更新职位
    const employee = employees.find(emp => emp.name === record.name);
    if (employee) {
        document.getElementById('editPosition').value = employee.position;
    }
    
    // 计算实际数量
    calculateActualQty();
    
    new bootstrap.Modal(document.getElementById('editModal')).show();
}

// 初始化拖动模态框功能
function initDraggableModal() {
    const modal = document.getElementById('editModal');
    const modalDialog = modal.querySelector('.modal-dialog');
    const modalHeader = document.getElementById('editModalHeader');
    
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;
    
    // 鼠标按下事件
    modalHeader.addEventListener('mousedown', dragStart);
    
    // 鼠标移动事件
    document.addEventListener('mousemove', drag);
    
    // 鼠标释放事件
    document.addEventListener('mouseup', dragEnd);
    
    function dragStart(e) {
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;
        
        if (e.target === modalHeader || modalHeader.contains(e.target)) {
            isDragging = true;
            modalDialog.classList.add('dragging');
        }
    }
    
    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            
            xOffset = currentX;
            yOffset = currentY;
            
            modalDialog.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
        }
    }
    
    function dragEnd(e) {
        initialX = currentX;
        initialY = currentY;
        isDragging = false;
        modalDialog.classList.remove('dragging');
    }
    
    // 模态框显示时重置位置
    modal.addEventListener('show.bs.modal', function() {
        modalDialog.style.transform = 'translate3d(0, 0, 0)';
        xOffset = 0;
        yOffset = 0;
    });
}

// 初始化产量管理
function initProductionManagement() {
    // 产量管理现在使用模态框，不需要初始化内联元素
}

// 打开产量计划模态框
function openProductionPlanning() {
    const modal = new bootstrap.Modal(document.getElementById('productionPlanningModal'));
    modal.show();
    loadProductionPlansForPlanning();
}

// 加载产量计划用于计划管理
async function loadProductionPlansForPlanning() {
    try {
        // 获取所有记录中的产品规格
        const recordsResponse = await fetch('/api/records');
        const records = await recordsResponse.json();
        const products = [...new Set(records.map(r => r.product).filter(p => p))];
        
        // 获取现有产量计划
        const plansResponse = await fetch('/api/production-plans');
        const plans = await plansResponse.json();
        
        displayProductionPlansForPlanning(products, plans);
    } catch (error) {
        console.error('加载产量计划失败:', error);
    }
}

// 显示产量计划在计划模态框中
function displayProductionPlansForPlanning(products, plans) {
    const tbody = document.getElementById('productionPlanningList');
    tbody.innerHTML = '';
    
    products.forEach(product => {
        const plan = plans.find(p => p.product === product);
        const row = document.createElement('tr');
        
        // 构建工序配置显示（包含完成率）
        let processConfig = '';
        if (plan) {
            const processes = [];
            if (plan.process1) {
                const completion = plan.process_completion && plan.process_completion[plan.process1];
                const completionText = completion ? ` (完成率: ${completion.completion_rate}%)` : '';
                processes.push(`${plan.process1}: ${plan.qty1 || 0}${completionText}`);
            }
            if (plan.process2) {
                const completion = plan.process_completion && plan.process_completion[plan.process2];
                const completionText = completion ? ` (完成率: ${completion.completion_rate}%)` : '';
                processes.push(`${plan.process2}: ${plan.qty2 || 0}${completionText}`);
            }
            if (plan.process3) {
                const completion = plan.process_completion && plan.process_completion[plan.process3];
                const completionText = completion ? ` (完成率: ${completion.completion_rate}%)` : '';
                processes.push(`${plan.process3}: ${plan.qty3 || 0}${completionText}`);
            }
            if (plan.process4) {
                const completion = plan.process_completion && plan.process_completion[plan.process4];
                const completionText = completion ? ` (完成率: ${completion.completion_rate}%)` : '';
                processes.push(`${plan.process4}: ${plan.qty4 || 0}${completionText}`);
            }
            processConfig = processes.length > 0 ? processes.join('<br>') : '未配置';
        } else {
            processConfig = '未配置';
        }
        
        row.innerHTML = `
            <td>${product}</td>
            <td>${processConfig}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editProductionPlan('${product}')">配置</button>
                ${plan ? `<button class="btn btn-sm btn-danger" onclick="deleteProductionPlan(${plan.id})">删除</button>` : ''}
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 编辑产量计划
function editProductionPlan(product) {
    // 创建编辑模态框
    const editModal = document.createElement('div');
    editModal.className = 'modal fade';
    editModal.id = 'editProductionPlanModal';
    editModal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">配置产量计划 - ${product}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div id="processConfigContainer">
                        <!-- 工序配置将在这里动态生成 -->
                    </div>
                    <div class="mt-3">
                        <button class="btn btn-success" onclick="addProcessToPlan()">+ 添加工序</button>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary" onclick="saveProductionPlan('${product}')">保存</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(editModal);
    const modal = new bootstrap.Modal(editModal);
    modal.show();
    
    // 加载现有配置
    loadProductionPlanConfig(product);
    
    // 模态框关闭时移除DOM元素
    editModal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(editModal);
    });
}

// 加载产量计划配置
async function loadProductionPlanConfig(product) {
    try {
        const response = await fetch('/api/production-plans');
        const plans = await response.json();
        const plan = plans.find(p => p.product === product);
        
        const container = document.getElementById('processConfigContainer');
        container.innerHTML = '';
        
        // 默认至少有一个工序
        const processes = [];
        if (plan) {
            if (plan.process1) processes.push({process: plan.process1, qty: plan.qty1 || 0});
            if (plan.process2) processes.push({process: plan.process2, qty: plan.qty2 || 0});
            if (plan.process3) processes.push({process: plan.process3, qty: plan.qty3 || 0});
            if (plan.process4) processes.push({process: plan.process4, qty: plan.qty4 || 0});
        }
        
        // 如果没有工序，添加一个默认的
        if (processes.length === 0) {
            processes.push({process: '', qty: 0});
        }
        
        processes.forEach((proc, index) => {
            addProcessConfigRow(index + 1, proc.process, proc.qty);
        });
    } catch (error) {
        console.error('加载产量计划配置失败:', error);
    }
}

// 添加工序配置行
function addProcessConfigRow(processNum, selectedProcess = '', qty = 0) {
    const container = document.getElementById('processConfigContainer');
    const row = document.createElement('div');
    row.className = 'row mb-2';
    row.id = `processRow${processNum}`;
    
    row.innerHTML = `
        <div class="col-md-4">
            <label class="form-label">工序${processNum}</label>
            <select class="form-select process-select" data-process-num="${processNum}">
                <option value="">选择工序</option>
            </select>
        </div>
        <div class="col-md-3">
            <label class="form-label">产量</label>
            <input type="number" class="form-control process-qty" data-process-num="${processNum}" 
                   value="${qty}" min="0" step="1" placeholder="产量">
        </div>
        <div class="col-md-2">
            <label class="form-label">&nbsp;</label>
            <button class="btn btn-danger d-block" onclick="removeProcessConfig(${processNum})">删除</button>
        </div>
    `;
    
    container.appendChild(row);
    
    // 填充工序选项
    loadProcessOptions(processNum, selectedProcess);
}

// 加载工序选项
async function loadProcessOptions(processNum, selectedProcess = '') {
    try {
        const response = await fetch('/api/processes');
        const processes = await response.json();
        
        const select = document.querySelector(`select[data-process-num="${processNum}"]`);
        select.innerHTML = '<option value="">选择工序</option>';
        
        processes.forEach(process => {
            const option = document.createElement('option');
            option.value = process.name;
            option.textContent = process.name;
            if (process.name === selectedProcess) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载工序选项失败:', error);
    }
}

// 添加工序到计划
function addProcessToPlan() {
    const existingRows = document.querySelectorAll('#processConfigContainer .row').length;
    addProcessConfigRow(existingRows + 1);
}

// 删除工序配置
function removeProcessConfig(processNum) {
    const row = document.getElementById(`processRow${processNum}`);
    if (row) {
        row.remove();
    }
}

// 保存产量计划
async function saveProductionPlan(product) {
    const processRows = document.querySelectorAll('#processConfigContainer .row');
    const planData = {
        product: product,
        process1: '',
        qty1: 0,
        process2: '',
        qty2: 0,
        process3: '',
        qty3: 0,
        process4: '',
        qty4: 0
    };
    
    processRows.forEach((row, index) => {
        const processSelect = row.querySelector('.process-select');
        const qtyInput = row.querySelector('.process-qty');
        
        if (processSelect && qtyInput) {
            const processNum = index + 1;
            planData[`process${processNum}`] = processSelect.value;
            planData[`qty${processNum}`] = parseInt(qtyInput.value) || 0;
        }
    });
    
    try {
        const response = await fetch('/api/production-plans', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(planData)
        });
        
        if (response.ok) {
            alert('产量计划保存成功');
            // 关闭编辑模态框
            const editModal = document.getElementById('editProductionPlanModal');
            const modal = bootstrap.Modal.getInstance(editModal);
            modal.hide();
            // 刷新产量计划列表
            loadProductionPlansForPlanning();
        } else {
            alert('保存失败，请重试');
        }
    } catch (error) {
        console.error('保存产量计划失败:', error);
        alert('保存失败，请重试');
    }
}

// 搜索产量计划
function searchProductionPlans() {
    const searchTerm = document.getElementById('productionSearchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#productionPlanningList tr');
    
    rows.forEach(row => {
        const product = row.cells[0].textContent.toLowerCase();
        if (product.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// 清除产量计划搜索
function clearProductionSearch() {
    document.getElementById('productionSearchInput').value = '';
    loadProductionPlansForPlanning();
}

// 删除产量计划
async function deleteProductionPlan(planId) {
    if (!confirm('确定要删除这个产量计划吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/production-plans/${planId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('产量计划删除成功');
            loadProductionPlansForPlanning();
        } else {
            alert('删除失败，请重试');
        }
    } catch (error) {
        console.error('删除产量计划失败:', error);
        alert('删除失败，请重试');
    }
}

// 加载产量计划信息（添加记录时使用）
async function loadProductionPlanInfo(product) {
    const infoDiv = document.getElementById('productionPlanInfo');
    const detailsDiv = document.getElementById('productionPlanDetails');
    
    if (!product) {
        infoDiv.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch('/api/production-plans');
        const plans = await response.json();
        const plan = plans.find(p => p.product === product);
        
        if (plan) {
            const processes = [];
            if (plan.process1) processes.push(`${plan.process1}: ${plan.qty1 || 0}`);
            if (plan.process2) processes.push(`${plan.process2}: ${plan.qty2 || 0}`);
            if (plan.process3) processes.push(`${plan.process3}: ${plan.qty3 || 0}`);
            if (plan.process4) processes.push(`${plan.process4}: ${plan.qty4 || 0}`);
            
            if (processes.length > 0) {
                detailsDiv.innerHTML = `
                    <div class="row">
                        ${processes.map(process => `
                            <div class="col-md-3 mb-2">
                                <span class="badge bg-primary">${process}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
                infoDiv.style.display = 'block';
            } else {
                detailsDiv.innerHTML = '<span class="text-muted">该产品规格暂无产量计划配置</span>';
                infoDiv.style.display = 'block';
            }
        } else {
            detailsDiv.innerHTML = '<span class="text-muted">该产品规格暂无产量计划配置</span>';
            infoDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('加载产量计划信息失败:', error);
        detailsDiv.innerHTML = '<span class="text-danger">加载失败，请重试</span>';
        infoDiv.style.display = 'block';
    }
}

// 导出数据到Excel
async function exportToExcel() {
    try {
        // 显示加载提示
        const exportBtn = event.target.closest('button');
        const originalText = exportBtn.innerHTML;
        exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>导出中...';
        exportBtn.disabled = true;
        
        // 获取筛选后的数据
        const filterProduct = document.getElementById('filterProduct')?.value || '';
        const filterProcess = document.getElementById('filterProcess')?.value || '';
        const filterName = document.getElementById('filterName')?.value || '';
        const filterAdjustmentMaster = document.getElementById('filterAdjustmentMaster')?.value || '';
        const startDate = document.getElementById('filterStartDate')?.value || '';
        const endDate = document.getElementById('filterEndDate')?.value || '';
        
        // 构建筛选URL
        let recordsUrl = '/api/records';
        const params = new URLSearchParams();
        if (filterProduct) params.append('product', filterProduct);
        if (filterProcess) params.append('process', filterProcess);
        if (filterName) params.append('name', filterName);
        if (filterAdjustmentMaster) params.append('adjustment_master', filterAdjustmentMaster);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (params.toString()) {
            recordsUrl += '?' + params.toString();
        }
        
        // 获取筛选后的数据和统计数据
        const [recordsResponse, statisticsResponse] = await Promise.all([
            fetch(recordsUrl),
            fetch('/api/statistics')
        ]);
        
        const records = await recordsResponse.json();
        const statistics = await statisticsResponse.json();
        
        // 调试信息
        console.log('筛选条件:', {
            product: filterProduct,
            process: filterProcess,
            name: filterName,
            adjustment_master: filterAdjustmentMaster,
            start_date: startDate,
            end_date: endDate
        });
        console.log('筛选后的记录数量:', records.length);
        console.log('统计数据:', statistics);
        
        // 创建工作簿
        const wb = XLSX.utils.book_new();
        
        // 创建产量记录格式的数据表
        const recordsData = [];
        
        // 添加筛选后的产量记录数据（与页面表格格式一致）
        records.forEach(record => {
            recordsData.push({
                '日期': record.date,
                '姓名': record.name,
                '职位': record.position,
                '产品规格': record.product,
                '工序': record.process,
                '单件时间': record.single_time,
                '实际数量': record.actual_qty,
                '总重量': record.total_weight,
                '单重': record.unit_weight,
                '皮重': record.tare_weight,
                '停机时长': record.downtime_duration,
                '调机时间': record.adjustment_time,
                '调机师傅': record.adjustment_master,
                '创建时间': record.created_at ? new Date(record.created_at).toLocaleString('zh-CN') : '',
                '更新时间': record.updated_at ? new Date(record.updated_at).toLocaleString('zh-CN') : ''
            });
        });
        
        // 创建产量记录工作表
        const recordsWS = XLSX.utils.json_to_sheet(recordsData);
        XLSX.utils.book_append_sheet(wb, recordsWS, '产量记录');
        
        // 创建统计数据工作表
        const statisticsData = [
            { '统计项目': '合计实际数量', '数值': statistics.total_actual_qty, '单位': '件' },
            { '统计项目': '平均产能稼动率', '数值': statistics.avg_capacity_rate, '单位': '%' },
            { '统计项目': '平均时间稼动率', '数值': statistics.avg_time_rate, '单位': '%' },
            { '统计项目': '总记录数', '数值': statistics.total_records, '单位': '条' },
            { '统计项目': '导出时间', '数值': new Date().toLocaleString('zh-CN'), '单位': '' }
        ];
        
        const statisticsWS = XLSX.utils.json_to_sheet(statisticsData);
        XLSX.utils.book_append_sheet(wb, statisticsWS, '统计数据');
        
        // 生成文件名
        const now = new Date();
        const timestamp = now.toISOString().slice(0, 19).replace(/[:-]/g, '');
        const filename = `阳昶产量记录管理系统_${timestamp}.xlsx`;
        
        // 导出文件
        XLSX.writeFile(wb, filename);
        
        // 恢复按钮状态
        exportBtn.innerHTML = originalText;
        exportBtn.disabled = false;
        
        // 显示导出的工作表信息
        const sheetNames = wb.SheetNames;
        console.log('导出的工作表:', sheetNames);
        alert(`数据导出成功！包含 ${sheetNames.length} 个工作表：${sheetNames.join(', ')}`);
        
    } catch (error) {
        console.error('导出失败:', error);
        console.error('错误详情:', error.message);
        console.error('错误堆栈:', error.stack);
        alert('导出失败，请重试。错误信息：' + error.message);
        
        // 恢复按钮状态
        const exportBtn = event.target.closest('button');
        exportBtn.innerHTML = '<i class="fas fa-file-excel me-2"></i>导出数据';
        exportBtn.disabled = false;
    }
}

// 批量删除相关功能
let batchDeleteMode = false;

// 切换批量删除模式
function toggleBatchDelete() {
    batchDeleteMode = !batchDeleteMode;
    const checkboxHeader = document.getElementById('checkboxHeader');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const checkboxes = document.querySelectorAll('.checkbox-cell');
    
    if (batchDeleteMode) {
        // 进入批量删除模式
        checkboxHeader.style.display = 'table-cell';
        selectAllBtn.style.display = 'inline-block';
        checkboxes.forEach(cell => cell.style.display = 'table-cell');
        
        // 更新按钮文本
        event.target.innerHTML = '<i class="fas fa-times me-1"></i>取消批量删除';
        event.target.className = 'btn btn-secondary';
    } else {
        // 退出批量删除模式
        checkboxHeader.style.display = 'none';
        selectAllBtn.style.display = 'none';
        checkboxes.forEach(cell => cell.style.display = 'none');
        
        // 清除所有选择
        document.querySelectorAll('.record-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('selectAllCheckbox').checked = false;
        
        // 更新按钮文本
        event.target.innerHTML = '<i class="fas fa-trash me-1"></i>批量删除';
        event.target.className = 'btn btn-danger';
    }
    
    updateBatchDeleteButtons();
}

// 全选/取消全选
function selectAllRecords() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const recordCheckboxes = document.querySelectorAll('.record-checkbox');
    
    recordCheckboxes.forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
    });
    
    updateBatchDeleteButtons();
}

// 切换全选状态
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const recordCheckboxes = document.querySelectorAll('.record-checkbox');
    
    recordCheckboxes.forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
    });
    
    updateBatchDeleteButtons();
}

// 更新批量删除按钮状态
function updateBatchDeleteButtons() {
    const selectedCheckboxes = document.querySelectorAll('.record-checkbox:checked');
    const selectAllBtn = document.getElementById('selectAllBtn');
    
    if (selectedCheckboxes.length > 0) {
        selectAllBtn.innerHTML = `<i class="fas fa-trash me-1"></i>删除选中(${selectedCheckboxes.length})`;
        selectAllBtn.className = 'btn btn-danger';
        selectAllBtn.onclick = deleteSelectedRecords;
    } else {
        selectAllBtn.innerHTML = '<i class="fas fa-check-square me-1"></i>全选';
        selectAllBtn.className = 'btn btn-success';
        selectAllBtn.onclick = selectAllRecords;
    }
}

// 删除选中的记录
async function deleteSelectedRecords() {
    const selectedCheckboxes = document.querySelectorAll('.record-checkbox:checked');
    const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (selectedIds.length === 0) {
        alert('请先选择要删除的记录');
        return;
    }
    
    if (!confirm(`确定要删除选中的 ${selectedIds.length} 条记录吗？此操作不可撤销！`)) {
        return;
    }
    
    try {
        // 显示加载状态
        const deleteBtn = event.target;
        const originalText = deleteBtn.innerHTML;
        deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>删除中...';
        deleteBtn.disabled = true;
        
        // 并行删除所有选中的记录
        const deletePromises = selectedIds.map(id => 
            fetch(`/api/records/${id}`, { method: 'DELETE' })
        );
        
        const responses = await Promise.all(deletePromises);
        
        // 检查所有删除操作是否成功
        const failedDeletes = responses.filter(response => !response.ok);
        
        if (failedDeletes.length > 0) {
            alert(`删除失败：${failedDeletes.length} 条记录删除失败`);
        } else {
            alert(`成功删除 ${selectedIds.length} 条记录`);
        }
        
        // 重新加载数据
        loadRecords();
        refreshProductionPlanInfo();
        
        // 退出批量删除模式
        toggleBatchDelete();
        
    } catch (error) {
        console.error('批量删除失败:', error);
        alert('批量删除失败，请重试');
    } finally {
        // 恢复按钮状态
        const deleteBtn = event.target;
        deleteBtn.innerHTML = originalText;
        deleteBtn.disabled = false;
    }
}

// 刷新产量计划信息（实时更新用）
function refreshProductionPlanInfo() {
    // 获取当前筛选的产品规格
    const filterProduct = document.getElementById('filterProduct').value;
    const newRecordProduct = document.getElementById('newRecordProduct').value;
    
    // 如果筛选区域有产品规格，刷新筛选区域的产量计划信息
    if (filterProduct) {
        loadProductionPlanInfoForFilter(filterProduct);
    }
    
    // 如果添加记录区域有产品规格，刷新添加记录区域的产量计划信息
    if (newRecordProduct) {
        loadProductionPlanInfo(newRecordProduct);
    }
    
    // 如果产量计划弹窗是打开的，也刷新弹窗内容
    const productionPlanningModal = document.getElementById('productionPlanningModal');
    if (productionPlanningModal && productionPlanningModal.classList.contains('show')) {
        loadProductionPlansForPlanning();
    }
}

// 加载产量计划信息（筛选时使用）
async function loadProductionPlanInfoForFilter(product) {
    const infoDiv = document.getElementById('filterProductionPlanInfo');
    const detailsDiv = document.getElementById('filterProductionPlanDetails');
    
    if (!product) {
        infoDiv.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch('/api/production-plans');
        const plans = await response.json();
        const plan = plans.find(p => p.product === product);
        
        if (plan) {
            const processes = [];
            if (plan.process1) {
                const completion = plan.process_completion && plan.process_completion[plan.process1];
                processes.push({
                    name: plan.process1,
                    qty: plan.qty1 || 0,
                    completion: completion
                });
            }
            if (plan.process2) {
                const completion = plan.process_completion && plan.process_completion[plan.process2];
                processes.push({
                    name: plan.process2,
                    qty: plan.qty2 || 0,
                    completion: completion
                });
            }
            if (plan.process3) {
                const completion = plan.process_completion && plan.process_completion[plan.process3];
                processes.push({
                    name: plan.process3,
                    qty: plan.qty3 || 0,
                    completion: completion
                });
            }
            if (plan.process4) {
                const completion = plan.process_completion && plan.process_completion[plan.process4];
                processes.push({
                    name: plan.process4,
                    qty: plan.qty4 || 0,
                    completion: completion
                });
            }
            
            if (processes.length > 0) {
                detailsDiv.innerHTML = `
                    <div class="row">
                        ${processes.map(process => {
                            const completion = process.completion;
                            let progressColor = 'bg-secondary';
                            let progressWidth = 0;
                            
                            if (completion) {
                                progressWidth = Math.min(completion.completion_rate, 100);
                                if (completion.completion_rate >= 100) {
                                    progressColor = 'bg-success';
                                } else if (completion.completion_rate >= 51) {
                                    progressColor = 'bg-primary';
                                } else if (completion.completion_rate >= 0) {
                                    progressColor = 'bg-warning';
                                }
                            }
                            
                            return `
                                <div class="col-md-6 mb-3">
                                    <div class="card">
                                        <div class="card-body p-2">
                                            <div class="d-flex justify-content-between align-items-center mb-1">
                                                <span class="fw-bold">${process.name}</span>
                                                <span class="badge bg-info">计划: ${process.qty}</span>
                                            </div>
                                            ${completion ? `
                                                <div class="d-flex justify-content-between align-items-center mb-1">
                                                    <small class="text-muted">实际: ${completion.actual_qty}</small>
                                                    <small class="fw-bold">完成率: ${completion.completion_rate}%</small>
                                                </div>
                                                <div class="progress" style="height: 8px;">
                                                    <div class="progress-bar ${progressColor}" 
                                                         style="width: ${progressWidth}%" 
                                                         role="progressbar" 
                                                         aria-valuenow="${progressWidth}" 
                                                         aria-valuemin="0" 
                                                         aria-valuemax="100">
                                                    </div>
                                                </div>
                                            ` : `
                                                <div class="text-muted">
                                                    <small>暂无实际产量数据</small>
                                                </div>
                                                <div class="progress" style="height: 8px;">
                                                    <div class="progress-bar bg-secondary" style="width: 0%"></div>
                                                </div>
                                            `}
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
                infoDiv.style.display = 'block';
            } else {
                detailsDiv.innerHTML = '<span class="text-muted">该产品规格暂无产量计划配置</span>';
                infoDiv.style.display = 'block';
            }
        } else {
            detailsDiv.innerHTML = '<span class="text-muted">该产品规格暂无产量计划配置</span>';
            infoDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('加载产量计划信息失败:', error);
        detailsDiv.innerHTML = '<span class="text-danger">加载失败，请重试</span>';
        infoDiv.style.display = 'block';
    }
}

// 初始化工序管理
function initProcessManagement() {
    // 不再自动加载工序列表，改为在弹窗中加载
}

// 加载工序列表
async function loadProcesses() {
    try {
        const response = await fetch('/api/processes');
        const processes = await response.json();
        displayProcesses(processes);
        updateProcessOptions(processes);
    } catch (error) {
        console.error('加载工序列表失败:', error);
    }
}

// 显示工序列表
function displayProcesses(processes) {
    const tbody = document.getElementById('processList');
    tbody.innerHTML = '';
    
    processes.forEach(process => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${process.name}</td>
            <td>${process.description || '-'}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteProcess(${process.id})">删除</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 更新所有工序选项
function updateProcessOptions(processes) {
    const processNames = processes.map(p => p.name);
    
    // 更新筛选区域的工序选项
    const processSelect = document.getElementById('filterProcess');
    if (processSelect) {
        const currentValue = processSelect.value;
        processSelect.innerHTML = '<option value="">全部</option>';
        processNames.forEach(process => {
            const option = document.createElement('option');
            option.value = process;
            option.textContent = process;
            processSelect.appendChild(option);
        });
        processSelect.value = currentValue;
    }
    
    
    // 更新记录表格中的工序选择框
    const recordProcessSelects = document.querySelectorAll('select[data-current-value]');
    recordProcessSelects.forEach(select => {
        const currentValue = select.getAttribute('data-current-value');
        select.innerHTML = '<option value="">选择工序</option>';
        processNames.forEach(process => {
            const option = document.createElement('option');
            option.value = process;
            option.textContent = process;
            select.appendChild(option);
        });
        select.value = currentValue;
    });
    
    // 更新编辑模态框中的工序选择框
    const editProcessSelect = document.getElementById('editProcess');
    if (editProcessSelect) {
        const currentValue = editProcessSelect.value;
        editProcessSelect.innerHTML = '<option value="">选择工序</option>';
        processNames.forEach(process => {
            const option = document.createElement('option');
            option.value = process;
            option.textContent = process;
            editProcessSelect.appendChild(option);
        });
        editProcessSelect.value = currentValue;
    }
}

// 添加工序
async function addProcess() {
    const name = document.getElementById('newProcessName').value.trim();
    const description = document.getElementById('newProcessDescription').value.trim();
    
    if (!name) {
        alert('请输入工序名称');
        return;
    }
    
    try {
        const response = await fetch('/api/processes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, description })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            // 清空输入框
            document.getElementById('newProcessName').value = '';
            document.getElementById('newProcessDescription').value = '';
            // 更新工序选项
            updateFilterOptions();
            
            // 如果工序管理模态框是打开的，刷新工序列表
            if (document.getElementById('processManagementModal').classList.contains('show')) {
                loadProcessesForManagement();
            }
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('添加工序失败:', error);
        alert('添加工序失败，请重试');
    }
}

// 删除工序
async function deleteProcess(processId) {
    if (!confirm('确定要删除这个工序吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/processes/${processId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            // 重新加载工序列表
            loadProcessesForManagement();
            // 更新工序选项
            updateFilterOptions();
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('删除工序失败:', error);
        alert('删除工序失败，请重试');
    }
}

// 打开工序管理弹窗
function openProcessManagement() {
    loadProcessesForManagement();
    new bootstrap.Modal(document.getElementById('processManagementModal')).show();
}

// 为工序管理弹窗加载工序列表
async function loadProcessesForManagement() {
    try {
        const response = await fetch('/api/processes');
        const processes = await response.json();
        displayProcessesForManagement(processes);
    } catch (error) {
        console.error('加载工序列表失败:', error);
    }
}

// 在工序管理弹窗中显示工序列表
function displayProcessesForManagement(processes) {
    const tbody = document.getElementById('processManagementList');
    tbody.innerHTML = '';
    
    processes.forEach(process => {
        const row = document.createElement('tr');
        const createdDate = process.created_at ? new Date(process.created_at).toLocaleDateString() : '-';
        row.innerHTML = `
            <td>${process.name}</td>
            <td>${process.description || '-'}</td>
            <td>${createdDate}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteProcess(${process.id})">删除</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 搜索工序
function searchProcesses() {
    const searchTerm = document.getElementById('processSearchInput').value.toLowerCase().trim();
    if (!searchTerm) {
        loadProcessesForManagement();
        return;
    }
    
    fetch('/api/processes')
        .then(response => response.json())
        .then(processes => {
            const filteredProcesses = processes.filter(process => 
                process.name.toLowerCase().includes(searchTerm) ||
                (process.description && process.description.toLowerCase().includes(searchTerm))
            );
            displayProcessesForManagement(filteredProcesses);
        })
        .catch(error => {
            console.error('搜索工序失败:', error);
        });
}

// 清除工序搜索
function clearProcessSearch() {
    document.getElementById('processSearchInput').value = '';
    loadProcessesForManagement();
}

// 打开员工管理弹窗
function openEmployeeManagement() {
    loadEmployeesForManagement();
    new bootstrap.Modal(document.getElementById('employeeManagementModal')).show();
}

// 为员工管理弹窗加载员工列表
async function loadEmployeesForManagement() {
    try {
        const response = await fetch('/api/employees');
        const employees = await response.json();
        displayEmployeesForManagement(employees);
    } catch (error) {
        console.error('加载员工列表失败:', error);
    }
}

// 在员工管理弹窗中显示员工列表
function displayEmployeesForManagement(employees) {
    const tbody = document.getElementById('employeeManagementList');
    tbody.innerHTML = '';
    
    employees.forEach(employee => {
        const row = document.createElement('tr');
        const createdDate = employee.created_at ? new Date(employee.created_at).toLocaleDateString() : '-';
        row.innerHTML = `
            <td>${employee.name}</td>
            <td>${employee.position}</td>
            <td>${createdDate}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteEmployee(${employee.id})">删除</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 搜索员工
function searchEmployees() {
    const searchTerm = document.getElementById('employeeSearchInput').value.toLowerCase().trim();
    if (!searchTerm) {
        loadEmployeesForManagement();
        return;
    }
    
    fetch('/api/employees')
        .then(response => response.json())
        .then(employees => {
            const filteredEmployees = employees.filter(employee => 
                employee.name.toLowerCase().includes(searchTerm) ||
                employee.position.toLowerCase().includes(searchTerm)
            );
            displayEmployeesForManagement(filteredEmployees);
        })
        .catch(error => {
            console.error('搜索员工失败:', error);
        });
}

// 清除员工搜索
function clearEmployeeSearch() {
    document.getElementById('employeeSearchInput').value = '';
    loadEmployeesForManagement();
}

// 删除员工
async function deleteEmployee(employeeId) {
    if (!confirm('确定要删除这个员工吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/employees/${employeeId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            // 重新加载员工列表
            loadEmployeesForManagement();
            // 更新员工选项
            updateFilterOptions();
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('删除员工失败:', error);
        alert('删除员工失败，请重试');
    }
}

// 更新记录中的工序
async function updateRecordProcess(recordId, processValue) {
    try {
        const response = await fetch(`/api/records/${recordId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ process: processValue })
        });
        
        if (response.ok) {
            // 更新成功，重新加载记录
            loadRecords();
            // 实时更新产量计划信息
            refreshProductionPlanInfo();
        } else {
            alert('更新工序失败，请重试');
        }
    } catch (error) {
        console.error('更新工序失败:', error);
        alert('更新工序失败，请重试');
    }
}

// 计算实际数量
function calculateActualQty() {
    const totalWeight = parseFloat(document.getElementById('editTotalWeight').value) || 0;
    const tareWeight = parseFloat(document.getElementById('editTareWeight').value) || 0;
    const unitWeight = parseFloat(document.getElementById('editUnitWeight').value) || 0;
    
    if (unitWeight > 0) {
        const actualQty = (totalWeight - tareWeight) / unitWeight;
        document.getElementById('editActualQty').value = Math.round(actualQty);
    } else {
        document.getElementById('editActualQty').value = '';
    }
}

// 保存记录
async function saveRecord() {
    const recordId = document.getElementById('editRecordId').value;
    const data = {
        date: document.getElementById('editDate').value,
        name: document.getElementById('editName').value,
        position: document.getElementById('editPosition').value,
        product: document.getElementById('editProduct').value,
        process: document.getElementById('editProcess').value,
        single_time: document.getElementById('editSingleTime').value,
        actual_qty: document.getElementById('editActualQty').value,
        total_weight: document.getElementById('editTotalWeight').value,
        unit_weight: document.getElementById('editUnitWeight').value,
        tare_weight: document.getElementById('editTareWeight').value,
        downtime_duration: document.getElementById('editDowntimeDuration').value,
        adjustment_time: document.getElementById('editAdjustmentTime').value,
        adjustment_master: document.getElementById('editAdjustmentMaster').value
    };
    
    try {
        const response = await fetch(`/api/records/${recordId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
            loadRecords();
            // 实时更新产量计划信息
            refreshProductionPlanInfo();
        } else {
            alert('保存记录失败');
        }
    } catch (error) {
        console.error('保存记录失败:', error);
        alert('保存记录失败');
    }
}

// 删除记录
async function deleteRecord(recordId) {
    if (!confirm('确定要删除这条记录吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/records/${recordId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadRecords();
            // 实时更新产量计划信息
            refreshProductionPlanInfo();
        } else {
            alert('删除记录失败');
        }
    } catch (error) {
        console.error('删除记录失败:', error);
        alert('删除记录失败');
    }
}

// 编辑单元格
function editCell(recordId, field) {
    editRecord(recordId);
}

// 切换注释显示
async function toggleComment(recordId, columnKey, event) {
    event.stopPropagation();
    
    const commentKey = `${recordId}-${columnKey}`;
    
    // 如果当前显示的就是这个注释，则隐藏
    if (currentCommentDisplay === commentKey) {
        hideCommentDisplay();
        return;
    }
    
    // 获取注释内容
    try {
        const response = await fetch(`/api/comments/${recordId}/${columnKey}`);
        const data = await response.json();
        
        if (data.comment) {
            showCommentDisplay(event, data.comment, commentKey);
        } else {
            // 没有注释，打开编辑对话框
            editComment(recordId, columnKey);
        }
    } catch (error) {
        console.error('获取注释失败:', error);
    }
}

// 显示注释
function showCommentDisplay(event, text, commentKey) {
    hideCommentDisplay();
    
    const popup = document.createElement('div');
    popup.className = 'comment-popup';
    popup.textContent = text;
    popup.id = 'commentDisplay';
    
    document.body.appendChild(popup);
    
    // 设置位置
    const rect = event.target.getBoundingClientRect();
    popup.style.left = (rect.right + 10) + 'px';
    popup.style.top = (rect.top - 10) + 'px';
    
    currentCommentDisplay = commentKey;
}

// 隐藏注释显示
function hideCommentDisplay() {
    const popup = document.getElementById('commentDisplay');
    if (popup) {
        popup.remove();
    }
    currentCommentDisplay = null;
}

// 编辑注释
async function editComment(recordId, columnKey, event) {
    if (event) {
        event.stopPropagation();
    }
    
    currentCommentRecordId = recordId;
    currentCommentColumn = columnKey;
    
    try {
        const response = await fetch(`/api/comments/${recordId}/${columnKey}`);
        const data = await response.json();
        document.getElementById('commentText').value = data.comment || '';
    } catch (error) {
        console.error('获取注释失败:', error);
        document.getElementById('commentText').value = '';
    }
    
    new bootstrap.Modal(document.getElementById('commentModal')).show();
}

// 保存注释
async function saveComment() {
    const commentText = document.getElementById('commentText').value.trim();
    
    try {
        const response = await fetch(`/api/comments/${currentCommentRecordId}/${currentCommentColumn}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ comment: commentText })
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('commentModal')).hide();
            loadRecords(); // 重新加载以更新注释标记
            
            // 如果当前显示的是这个注释，更新显示内容
            const commentKey = `${currentCommentRecordId}-${currentCommentColumn}`;
            if (currentCommentDisplay === commentKey) {
                if (commentText) {
                    // 更新显示内容
                    const popup = document.getElementById('commentDisplay');
                    if (popup) {
                        popup.textContent = commentText;
                    }
                } else {
                    // 隐藏显示
                    hideCommentDisplay();
                }
            }
        } else {
            alert('保存注释失败');
        }
    } catch (error) {
        console.error('保存注释失败:', error);
        alert('保存注释失败');
    }
}

// 应用筛选
function applyFilters() {
    loadRecords();
}

// 清除筛选
function clearFilters() {
    document.getElementById('filterStartDate').value = '';
    document.getElementById('filterEndDate').value = '';
    document.getElementById('filterName').value = '';
    document.getElementById('filterProduct').value = '';
    document.getElementById('filterProcess').value = '';
    document.getElementById('filterAdjustmentMaster').value = '';
    
    // 隐藏筛选时的产量计划信息
    document.getElementById('filterProductionPlanInfo').style.display = 'none';
    
    loadRecords();
}

// 刷新数据
function refreshData() {
    loadRecords();
    loadEmployees();
}

// 姓名选择变化时更新职位
document.getElementById('newRecordName').addEventListener('change', function() {
    const selectedName = this.value;
    const employee = employees.find(emp => emp.name === selectedName);
    document.getElementById('newRecordPosition').value = employee ? employee.position : '';
});

document.getElementById('editName').addEventListener('change', function() {
    const selectedName = this.value;
    const employee = employees.find(emp => emp.name === selectedName);
    document.getElementById('editPosition').value = employee ? employee.position : '';
});

// 点击其他地方隐藏注释显示
document.addEventListener('click', function(event) {
    if (!event.target.closest('.comment-indicator') && !event.target.closest('.comment-popup')) {
        hideCommentDisplay();
    }
});

// 产品规格管理相关功能
let allProducts = []; // 存储所有产品规格

// 打开产品规格管理模态框
function openProductManagement() {
    const modal = new bootstrap.Modal(document.getElementById('productManagementModal'));
    modal.show();
    loadProductsForManagement();
}

// 加载产品规格列表用于管理
async function loadProductsForManagement() {
    try {
        const response = await fetch('/api/products');
        const products = await response.json();
        allProducts = products;
        displayProductsForManagement(products);
    } catch (error) {
        console.error('加载产品规格失败:', error);
        alert('加载产品规格失败');
    }
}

// 显示产品规格列表
function displayProductsForManagement(products) {
    const tbody = document.getElementById('productManagementList');
    tbody.innerHTML = '';
    
    products.forEach(product => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${product.name}</td>
            <td>${product.description || '-'}</td>
            <td>${product.created_at ? new Date(product.created_at).toLocaleDateString() : '-'}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteProduct(${product.id})">删除</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 添加产品规格
async function addProduct() {
    const name = document.getElementById('newProductName').value.trim();
    const description = document.getElementById('newProductDescription').value.trim();
    
    if (!name) {
        alert('请输入产品规格名称');
        return;
    }
    
    try {
        const response = await fetch('/api/products', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('产品规格添加成功');
            document.getElementById('newProductName').value = '';
            document.getElementById('newProductDescription').value = '';
            loadProductsForManagement();
            updateProductOptions(); // 更新添加记录中的产品规格选项
        } else {
            alert('添加失败: ' + result.error);
        }
    } catch (error) {
        console.error('添加产品规格失败:', error);
        alert('添加失败，请重试');
    }
}

// 删除产品规格
async function deleteProduct(productId) {
    if (!confirm('确定要删除这个产品规格吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/products/${productId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('产品规格删除成功');
            loadProductsForManagement();
            updateProductOptions(); // 更新添加记录中的产品规格选项
        } else {
            alert('删除失败: ' + result.message);
        }
    } catch (error) {
        console.error('删除产品规格失败:', error);
        alert('删除失败，请重试');
    }
}

// 搜索产品规格
function searchProducts() {
    const searchTerm = document.getElementById('productSearchInput').value.toLowerCase();
    const filteredProducts = allProducts.filter(product => 
        product.name.toLowerCase().includes(searchTerm) ||
        (product.description && product.description.toLowerCase().includes(searchTerm))
    );
    displayProductsForManagement(filteredProducts);
}

// 清除产品规格搜索
function clearProductSearch() {
    document.getElementById('productSearchInput').value = '';
    displayProductsForManagement(allProducts);
}

// 更新产品规格选项（用于添加记录）
async function updateProductOptions() {
    try {
        const response = await fetch('/api/products');
        const products = await response.json();
        allProducts = products;
        
        // 更新产品规格下拉框选项
        const dropdown = document.getElementById('productDropdown');
        dropdown.innerHTML = '';
        
        products.forEach(product => {
            const option = document.createElement('div');
            option.className = 'dropdown-item';
            option.style.cursor = 'pointer';
            option.textContent = product.name;
            option.onclick = () => selectProduct(product.name);
            dropdown.appendChild(option);
        });
    } catch (error) {
        console.error('更新产品规格选项失败:', error);
    }
}

// 选择产品规格
function selectProduct(productName) {
    console.log('选择产品规格:', productName); // 调试信息
    document.getElementById('newRecordProductSearch').value = productName;
    document.getElementById('newRecordProduct').value = productName;
    hideProductDropdown();
    loadProductionPlanInfo(productName);
}

// 显示产品规格下拉框
function showProductDropdown() {
    const dropdown = document.getElementById('productDropdown');
    if (dropdown.children.length > 0) {
        dropdown.style.display = 'block';
    }
}

// 隐藏产品规格下拉框
function hideProductDropdown() {
    setTimeout(() => {
        document.getElementById('productDropdown').style.display = 'none';
    }, 200);
}

// 搜索产品规格选项
function searchProductOptions() {
    const searchTerm = document.getElementById('newRecordProductSearch').value.toLowerCase();
    const dropdown = document.getElementById('productDropdown');
    const options = dropdown.children;
    
    let hasVisibleOptions = false;
    for (let option of options) {
        if (option.textContent.toLowerCase().includes(searchTerm)) {
            option.style.display = 'block';
            hasVisibleOptions = true;
        } else {
            option.style.display = 'none';
        }
    }
    
    dropdown.style.display = hasVisibleOptions ? 'block' : 'none';
}

