// AI SQL Review Tool - 前端应用逻辑

let currentSQLId = null;
let currentReportId = null;
let currentConnectionId = null;
let currentLLMConfigId = null;
let currentSQLPage = 1;
let sqlPageSize = 10;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDatabaseConnections();
    loadSQLStatements();
    loadLLMConfigs();
    
    // 数据库连接下拉框事件（如果存在的话）
    const dbSelect = document.getElementById('db-connection-select');
    if (dbSelect) {
        // 这里可以添加数据库连接选择的事件处理
    }
    
    // LLM配置下拉框事件（如果存在的话）
    const llmSelect = document.getElementById('llm-config-select');
    if (llmSelect) {
        // 这里可以添加LLM配置选择的事件处理
    }
    
    // 添加折叠图标切换事件
    document.addEventListener('shown.bs.collapse', function (e) {
        const icon = document.querySelector(`[data-bs-target="#${e.target.id}"] i`);
        if (icon) icon.classList.remove('collapsed');
    });
    
    document.addEventListener('hidden.bs.collapse', function (e) {
        const icon = document.querySelector(`[data-bs-target="#${e.target.id}"] i`);
        if (icon) icon.classList.add('collapsed');
    });
});

// 显示添加数据库连接模态框
function showAddConnectionModal() {
    currentConnectionId = null;
    document.getElementById('connection-form').reset();
    document.querySelector('#addConnectionModal .modal-title').textContent = '添加数据库连接';
    const modal = new bootstrap.Modal(document.getElementById('addConnectionModal'));
    modal.show();
}

// 编辑数据库连接
async function editConnection(connectionId) {
    try {
        const response = await fetch(`/api/db-connections/${connectionId}`);
        const connection = await response.json();
        
        currentConnectionId = connectionId;
        document.getElementById('conn-name').value = connection.name || '';
        document.getElementById('conn-type').value = connection.db_type || '';
        document.getElementById('conn-host').value = connection.host || '';
        document.getElementById('conn-port').value = connection.port || '';
        document.getElementById('conn-database').value = connection.database_name || '';
        document.getElementById('conn-username').value = connection.username || '';
        document.getElementById('conn-password').value = ''; // 不显示密码
        
        document.querySelector('#addConnectionModal .modal-title').textContent = '编辑数据库连接';
        const modal = new bootstrap.Modal(document.getElementById('addConnectionModal'));
        modal.show();
    } catch (error) {
        showAlert('加载连接信息失败: ' + error.message, 'danger');
    }
}

// 显示LLM配置模态框
function showLLMConfigModal() {
    currentLLMConfigId = null;
    document.getElementById('llm-config-form').reset();
    document.querySelector('#llmConfigModal .modal-title').textContent = '添加AI模型配置';
    const modal = new bootstrap.Modal(document.getElementById('llmConfigModal'));
    modal.show();
}

// 编辑LLM配置
async function editLLMConfig(configId) {
    try {
        const response = await fetch(`/api/llm-configs/${configId}`);
        const config = await response.json();
        
        currentLLMConfigId = configId;
        document.getElementById('llm-name').value = config.name || '';
        document.getElementById('llm-provider').value = config.provider || '';
        document.getElementById('llm-model').value = config.model_name || '';
        document.getElementById('llm-api-key').value = ''; // 不显示API密钥
        document.getElementById('llm-base-url').value = config.base_url || '';
        
        document.querySelector('#llmConfigModal .modal-title').textContent = '编辑AI模型配置';
        const modal = new bootstrap.Modal(document.getElementById('llmConfigModal'));
        modal.show();
    } catch (error) {
        showAlert('加载配置信息失败: ' + error.message, 'danger');
    }
}

// 删除SQL语句
async function deleteSQLStatement(sqlId) {
    if (!confirm('确定要删除这个SQL语句吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/sql-statements/${sqlId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadSQLStatements(currentSQLPage);
            if (currentSQLId === sqlId) {
                addNewSQL(); // 清空编辑器
            }
            showAlert('SQL语句删除成功', 'success');
        } else {
            const error = await response.json();
            showAlert('删除失败: ' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('删除失败: ' + error.message, 'danger');
    }
}

// 删除LLM配置
async function deleteLLMConfig(configId) {
    if (!confirm('确定要删除这个AI模型配置吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/llm-configs/${configId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadLLMConfigs();
            showAlert('AI模型配置删除成功', 'success');
        } else {
            const error = await response.json();
            showAlert('删除失败: ' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('删除失败: ' + error.message, 'danger');
    }
}

// 测试数据库连接
async function testConnection() {
    const formData = {
        name: document.getElementById('conn-name').value,
        db_type: document.getElementById('conn-type').value,
        host: document.getElementById('conn-host').value,
        port: parseInt(document.getElementById('conn-port').value) || null,
        database_name: document.getElementById('conn-database').value,
        username: document.getElementById('conn-username').value,
        password: document.getElementById('conn-password').value
    };

    const spinner = document.getElementById('test-spinner');
    const button = event.target;
    
    try {
        spinner.classList.remove('d-none');
        button.disabled = true;
        
        const response = await fetch('/api/db-connections/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert('连接测试成功！', 'success');
        } else {
            showAlert('连接测试失败: ' + (result.message || '未知错误'), 'danger');
        }
    } catch (error) {
        showAlert('连接测试失败: ' + error.message, 'danger');
    } finally {
        spinner.classList.add('d-none');
        button.disabled = false;
    }
}

// 保存数据库连接
async function saveConnection() {
    const formData = {
        name: document.getElementById('conn-name').value,
        db_type: document.getElementById('conn-type').value,
        host: document.getElementById('conn-host').value,
        port: parseInt(document.getElementById('conn-port').value) || null,
        database_name: document.getElementById('conn-database').value,
        username: document.getElementById('conn-username').value,
        password: document.getElementById('conn-password').value
    };

    try {
        const url = currentConnectionId ? `/api/db-connections/${currentConnectionId}` : '/api/db-connections';
        const method = currentConnectionId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addConnectionModal'));
            modal.hide();
            document.getElementById('connection-form').reset();
            currentConnectionId = null;
            loadDatabaseConnections();
            showAlert('数据库连接保存成功', 'success');
        } else {
            const error = await response.json();
            showAlert('保存失败: ' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('保存失败: ' + error.message, 'danger');
    }
}

// 保存LLM配置
async function saveLLMConfig() {
    const formData = {
        name: document.getElementById('llm-name').value,
        provider: document.getElementById('llm-provider').value,
        model_name: document.getElementById('llm-model').value,
        api_key: document.getElementById('llm-api-key').value,
        base_url: document.getElementById('llm-base-url').value
    };

    try {
        const url = currentLLMConfigId ? `/api/llm-configs/${currentLLMConfigId}` : '/api/llm-configs';
        const method = currentLLMConfigId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('llmConfigModal'));
            modal.hide();
            document.getElementById('llm-config-form').reset();
            currentLLMConfigId = null;
            loadLLMConfigs();
            showAlert('LLM配置保存成功', 'success');
        } else {
            const error = await response.json();
            showAlert('保存失败: ' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('保存失败: ' + error.message, 'danger');
    }
}

// 加载数据库连接列表
async function loadDatabaseConnections() {
    try {
        const response = await fetch('/api/db-connections/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const connections = await response.json();
        
        const container = document.getElementById('db-connections');
        const select = document.getElementById('db-connection-select');
        
        if (connections.length === 0) {
            container.innerHTML = '<div class="list-group-item text-muted">暂无连接</div>';
            select.innerHTML = '<option value="">选择数据库连接</option>';
        } else {
            container.innerHTML = connections.map(conn => `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div onclick="editConnection(${conn.id})" style="cursor: pointer; flex-grow: 1;">
                        <strong>${conn.name}</strong>
                        <br><small class="text-muted">${conn.db_type}</small>
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editConnection(${conn.id})" title="编辑">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteConnection(${conn.id})" title="删除">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
            
            const optionsHtml = '<option value="">选择数据库连接</option>' + 
                connections.map(conn => `<option value="${conn.id}">${conn.name}</option>`).join('');
            
            select.innerHTML = optionsHtml;
        }
    } catch (error) {
        console.error('加载数据库连接失败:', error);
    }
}

// 加载SQL语句列表（带分页）
async function loadSQLStatements(page = 1) {
    try {
        const response = await fetch(`/api/sql-statements/?page=${page}&page_size=${sqlPageSize}&order_by=created_at&order_dir=desc`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('SQL语句数据:', data); // 添加调试日志
        
        const container = document.getElementById('sql-statements');
        const paginationContainer = document.getElementById('sql-pagination');
        
        if (!data.items || data.items.length === 0) {
            container.innerHTML = '<div class="list-group-item text-muted">暂无SQL语句</div>';
            paginationContainer.innerHTML = '';
        } else {
            container.innerHTML = data.items.map(stmt => `
                <div class="list-group-item list-group-item-action">
                    <div class="d-flex w-100 justify-content-between align-items-start">
                        <div onclick="loadSQL(${stmt.id})" style="cursor: pointer; flex-grow: 1;">
                            <h6 class="mb-1">${stmt.title || 'SQL-' + stmt.id}</h6>
                            <p class="mb-1">${stmt.description || '无描述'}</p>
                            <small class="text-muted">创建时间: ${new Date(stmt.created_at).toLocaleString()}</small>
                        </div>
                        <div class="d-flex flex-column align-items-end">
                            <div class="mb-1">${getStatusBadge(stmt.status)}</div>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteSQLStatement(${stmt.id})" title="删除">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
            
            // 生成分页控件
            generateSQLPagination(data.page, data.pages, data.total);
        }
        
        currentSQLPage = page;
    } catch (error) {
        console.error('加载SQL语句失败:', error);
    }
}

// 生成SQL分页控件
function generateSQLPagination(currentPage, totalPages, totalItems) {
    const container = document.getElementById('sql-pagination');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = `
        <div class="d-flex justify-content-between align-items-center">
            <small class="text-muted">共 ${totalItems} 条</small>
            <div class="btn-group btn-group-sm">
    `;
    
    // 上一页
    html += `
        <button class="btn btn-outline-secondary" onclick="loadSQLStatements(${currentPage - 1})" 
                ${currentPage <= 1 ? 'disabled' : ''}>
            <i class="bi bi-chevron-left"></i>
        </button>
    `;
    
    // 页码
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button class="btn ${i === currentPage ? 'btn-primary' : 'btn-outline-secondary'}" 
                    onclick="loadSQLStatements(${i})">
                ${i}
            </button>
        `;
    }
    
    // 下一页
    html += `
        <button class="btn btn-outline-secondary" onclick="loadSQLStatements(${currentPage + 1})" 
                ${currentPage >= totalPages ? 'disabled' : ''}>
            <i class="bi bi-chevron-right"></i>
        </button>
    `;
    
    html += '</div></div>';
    container.innerHTML = html;
}

// 加载LLM配置列表
async function loadLLMConfigs() {
    try {
        const response = await fetch('/api/llm-configs/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const configs = await response.json();
        
        const select = document.getElementById('llm-config-select');
        const container = document.getElementById('llm-configs');
        
        if (configs.length === 0) {
            select.innerHTML = '<option value="">选择AI模型</option>';
            container.innerHTML = '<div class="list-group-item text-muted">暂无配置</div>';
        } else {
            const optionsHtml = '<option value="">选择AI模型</option>' + 
                configs.map(config => `
                    <option value="${config.id}" ${config.is_default ? 'selected' : ''}>
                        ${config.name} (${config.provider}/${config.model_name})
                    </option>
                `).join('');
            
            select.innerHTML = optionsHtml;
            
            // 显示LLM配置列表
            container.innerHTML = configs.map(config => `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div onclick="editLLMConfig(${config.id})" style="cursor: pointer; flex-grow: 1;">
                        <strong>${config.name}</strong>
                        <br><small class="text-muted">${config.provider}/${config.model_name}</small>
                        ${config.is_default ? '<br><span class="badge bg-primary">默认</span>' : ''}
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editLLMConfig(${config.id})" title="编辑">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteLLMConfig(${config.id})" title="删除">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载LLM配置失败:', error);
    }
}

// 新建SQL
function addNewSQL() {
    currentSQLId = null;
    document.getElementById('sql-title').value = '';
    document.getElementById('sql-description').value = '';
    document.getElementById('sql-content').value = '';
    
    // 清空数据库连接选择器
    const dbSelect = document.getElementById('db-connection-select');
    
    if (dbSelect) dbSelect.value = '';
    
    document.getElementById('review-report').style.display = 'none';
}

// 加载SQL语句
async function loadSQL(sqlId) {
    try {
        const response = await fetch(`/api/sql-statements/${sqlId}`);
        const sql = await response.json();
        
        currentSQLId = sqlId;
        document.getElementById('sql-title').value = sql.title || '';
        document.getElementById('sql-description').value = sql.description || '';
        document.getElementById('sql-content').value = sql.sql_content || '';
        
        // 设置数据库连接选择器
        const dbConnectionId = sql.db_connection_id || '';
        const dbSelect = document.getElementById('db-connection-select');
        
        if (dbSelect) dbSelect.value = dbConnectionId;
        
        // 加载最新的审查报告
        loadLatestReviewReport(sqlId);
        
    } catch (error) {
        console.error('加载SQL语句失败:', error);
        showAlert('加载SQL语句失败', 'danger');
    }
}

// 保存SQL
async function saveSQL() {
    // 表单验证
    const title = document.getElementById('sql-title').value.trim();
    const sqlContent = document.getElementById('sql-content').value.trim();
    
    if (!title) {
        showAlert('请输入SQL标题', 'warning');
        document.getElementById('sql-title').focus();
        return;
    }
    
    if (!sqlContent) {
        showAlert('请输入SQL语句', 'warning');
        document.getElementById('sql-content').focus();
        return;
    }
    
    // 获取数据库连接ID
    const dbConnectionId = document.getElementById('db-connection-select') ? document.getElementById('db-connection-select').value : '';
    
    const formData = {
        title: title,
        sql_content: sqlContent,
        description: document.getElementById('sql-description').value,
        db_connection_id: parseInt(dbConnectionId) || null
    };

    try {
        let response;
        if (currentSQLId) {
            response = await fetch(`/api/sql-statements/${currentSQLId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
        } else {
            response = await fetch('/api/sql-statements', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
        }

        if (response.ok) {
            const result = await response.json();
            if (!currentSQLId) {
                currentSQLId = result.id;
            }
            loadSQLStatements();
            showAlert('SQL语句保存成功', 'success');
        } else {
            const error = await response.json();
            showAlert('保存失败: ' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('保存失败: ' + error.message, 'danger');
    }
}

// 审查SQL
async function reviewSQL() {
    if (!currentSQLId) {
        showAlert('请先保存SQL语句', 'warning');
        return;
    }

    const llmConfigId = document.getElementById('llm-config-select').value;
    
    // 显示加载状态
    const reviewBtn = document.getElementById('review-btn');
    const spinner = document.getElementById('review-spinner');
    reviewBtn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        const url = `/api/reviews/sql/${currentSQLId}/review` + 
                   (llmConfigId ? `?llm_config_id=${llmConfigId}` : '');
        
        const response = await fetch(url, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            currentReportId = result.report_id;
            displayReviewReport(result.review_result);
            showAlert('AI审查完成', 'success');
        } else {
            const error = await response.json();
            showAlert('审查失败: ' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('审查失败: ' + error.message, 'danger');
    } finally {
        // 隐藏加载状态
        reviewBtn.disabled = false;
        spinner.classList.add('d-none');
    }
}

// 加载最新的审查报告
async function loadLatestReviewReport(sqlId) {
    try {
        const response = await fetch(`/api/reviews/sql/${sqlId}/history`);
        const reports = await response.json();
        
        if (reports.length > 0) {
            const latestReport = reports[0];
            const reportResponse = await fetch(`/api/reviews/reports/${latestReport.id}`);
            const reportData = await reportResponse.json();
            displayReviewReport(reportData);
        } else {
            document.getElementById('review-report').style.display = 'none';
        }
    } catch (error) {
        console.error('加载审查报告失败:', error);
    }
}

// 显示审查报告
function displayReviewReport(report) {
    const reportContainer = document.getElementById('review-report');
    const contentContainer = document.getElementById('review-content');
    
    const sections = [
        { key: 'overall_assessment', title: '总体评估', icon: '📊' },
        { key: 'consistency', title: '一致性分析', icon: '🎯' },
        { key: 'conventions', title: 'SQL规范性', icon: '📋' },
        { key: 'performance', title: '性能分析', icon: '⚡' },
        { key: 'security', title: '安全性检查', icon: '🔒' },
        { key: 'readability', title: '可读性评估', icon: '👁️' },
        { key: 'maintainability', title: '可维护性', icon: '🔧' }
    ];

    let html = '';
    
    sections.forEach(section => {
        const data = report[section.key];
        if (data) {
            const statusClass = getStatusClass(data.status);
            const scoreColor = getScoreColor(data.score);
            
            html += `
                <div class="review-section">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="mb-0">${section.icon} ${section.title}</h6>
                        <div class="d-flex align-items-center">
                            <span class="badge ${statusClass} me-2">${getStatusText(data.status)}</span>
                            <div class="score-circle" style="background-color: ${scoreColor}">
                                ${data.score || 0}
                            </div>
                        </div>
                    </div>
                    ${data.details ? `<p><strong>详细分析:</strong> ${data.details}</p>` : ''}
                    ${data.suggestions ? `<p><strong>改进建议:</strong> ${data.suggestions}</p>` : ''}
                    ${data.summary ? `<p><strong>摘要:</strong> ${data.summary}</p>` : ''}
                </div>
            `;
        }
    });

    // 添加优化建议
    if (report.optimized_sql) {
        html += `
            <div class="review-section">
                <h6>🚀 优化建议SQL</h6>
                <pre><code class="language-sql">${report.optimized_sql}</code></pre>
            </div>
        `;
    }

    contentContainer.innerHTML = html;
    reportContainer.style.display = 'block';
    
    // 高亮SQL代码
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
}

// 获取状态对应的CSS类
function getStatusClass(status) {
    const statusMap = {
        'excellent': 'bg-success',
        'good': 'bg-primary',
        'needs_improvement': 'bg-warning',
        'has_issues': 'bg-danger'
    };
    return statusMap[status] || 'bg-secondary';
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'excellent': '优秀',
        'good': '良好',
        'needs_improvement': '需要改进',
        'has_issues': '存在问题'
    };
    return statusMap[status] || '未知';
}

// 获取分数对应的颜色
function getScoreColor(score) {
    if (score >= 90) return '#198754';
    if (score >= 80) return '#0d6efd';
    if (score >= 60) return '#fd7e14';
    return '#dc3545';
}

// 获取状态徽章
function getStatusBadge(status) {
    const statusMap = {
        'draft': '<span class="badge bg-secondary">草稿</span>',
        'reviewed': '<span class="badge bg-primary">已审查</span>',
        'approved': '<span class="badge bg-success">已批准</span>',
        'rejected': '<span class="badge bg-danger">已拒绝</span>'
    };
    return statusMap[status] || '<span class="badge bg-light">未知</span>';
}

// 删除数据库连接
async function deleteConnection(connectionId) {
    if (!confirm('确定要删除这个数据库连接吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/db-connections/${connectionId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadDatabaseConnections();
            showAlert('数据库连接删除成功', 'success');
        } else {
            const error = await response.json();
            showAlert('删除失败: ' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('删除失败: ' + error.message, 'danger');
    }
}

// 显示提示消息
function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertContainer.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertContainer);
    
    // 3秒后自动消失
    setTimeout(() => {
        if (alertContainer.parentNode) {
            alertContainer.parentNode.removeChild(alertContainer);
        }
    }, 3000);
}

// ==================== 新增功能 ====================

// 显示导入CSV模态框
function showImportModal() {
    // 加载数据库连接到导入模态框
    loadDatabaseConnections().then(() => {
        const connections = document.getElementById('db-connection-select').innerHTML;
        document.getElementById('import-connection').innerHTML = connections;
    });
    
    const modal = new bootstrap.Modal(document.getElementById('importModal'));
    modal.show();
}

// 预览CSV文件
function previewCSV() {
    const fileInput = document.getElementById('csv-file');
    const file = fileInput.files[0];
    
    if (!file) {
        document.getElementById('csv-preview').style.display = 'none';
        document.getElementById('import-btn').disabled = true;
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const csv = e.target.result;
        const lines = csv.split('\n').filter(line => line.trim());
        
        if (lines.length < 2) {
            showAlert('CSV文件格式不正确，至少需要标题行和一行数据', 'warning');
            return;
        }
        
        const headers = lines[0].split(',').map(h => h.trim());
        const previewData = lines.slice(1, 6); // 预览前5行
        
        // 构建预览表格
        const table = document.getElementById('csv-preview-table');
        table.querySelector('thead').innerHTML = `
            <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
        `;
        
        table.querySelector('tbody').innerHTML = previewData.map(line => {
            const cells = line.split(',').map(c => c.trim());
            return `<tr>${cells.map(c => `<td>${c}</td>`).join('')}</tr>`;
        }).join('');
        
        document.getElementById('csv-preview').style.display = 'block';
        document.getElementById('import-btn').disabled = false;
    };
    
    reader.readAsText(file);
}

// 导入CSV
async function importCSV() {
    const fileInput = document.getElementById('csv-file');
    const connectionId = document.getElementById('import-connection').value;
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('请选择CSV文件', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    if (connectionId) {
        formData.append('db_connection_id', connectionId);
    }
    
    try {
        const response = await fetch('/api/sql-statements/import-csv', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            const modal = bootstrap.Modal.getInstance(document.getElementById('importModal'));
            modal.hide();
            loadSQLStatements();
            showAlert(`成功导入 ${result.imported_count} 条SQL语句`, 'success');
        } else {
            const error = await response.json();
            showAlert('导入失败: ' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('导入失败: ' + error.message, 'danger');
    }
}

// 导出SQL为CSV
async function exportSQL() {
    try {
        const response = await fetch('/api/sql-statements/export-csv');
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sql_statements_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showAlert('导出成功', 'success');
        } else {
            showAlert('导出失败', 'danger');
        }
    } catch (error) {
        showAlert('导出失败: ' + error.message, 'danger');
    }
}

// 显示数据库浏览器
function showDatabaseExplorer() {
    // 加载数据库连接到浏览器模态框
    loadDatabaseConnections().then(() => {
        const connections = document.getElementById('db-connection-select').innerHTML;
        document.getElementById('explorer-connection').innerHTML = connections;
    });
    
    const modal = new bootstrap.Modal(document.getElementById('databaseExplorerModal'));
    modal.show();
}

// 加载数据库模式
async function loadDatabaseSchema() {
    const connectionId = document.getElementById('explorer-connection').value;
    const schemaTree = document.getElementById('schema-tree');
    const objectDetails = document.getElementById('object-details');
    
    if (!connectionId) {
        schemaTree.innerHTML = '<div class="text-muted">请先选择数据库连接</div>';
        objectDetails.innerHTML = '<div class="text-muted">选择左侧对象查看详细信息</div>';
        return;
    }
    
    try {
        const response = await fetch(`/api/db-connections/${connectionId}/schema`);
        
        if (response.ok) {
            const schema = await response.json();
            displaySchemaTree(schema);
        } else {
            schemaTree.innerHTML = '<div class="text-danger">加载数据库模式失败</div>';
        }
    } catch (error) {
        schemaTree.innerHTML = '<div class="text-danger">连接数据库失败</div>';
    }
}

// 显示数据库模式树
function displaySchemaTree(schema) {
    const schemaTree = document.getElementById('schema-tree');
    
    let html = '';
    
    // 显示表
    if (schema.tables && schema.tables.length > 0) {
        html += `
            <div class="mb-2">
                <strong><i class="bi bi-table"></i> 表 (${schema.tables.length})</strong>
                <div class="ms-3">
        `;
        
        schema.tables.forEach(table => {
            html += `
                <div class="py-1">
                    <a href="#" class="text-decoration-none" onclick="showTableDetails('${table.name}', 'table')">
                        <i class="bi bi-table"></i> ${table.name}
                    </a>
                </div>
            `;
        });
        
        html += '</div></div>';
    }
    
    // 显示视图
    if (schema.views && schema.views.length > 0) {
        html += `
            <div class="mb-2">
                <strong><i class="bi bi-eye"></i> 视图 (${schema.views.length})</strong>
                <div class="ms-3">
        `;
        
        schema.views.forEach(view => {
            html += `
                <div class="py-1">
                    <a href="#" class="text-decoration-none" onclick="showTableDetails('${view.name}', 'view')">
                        <i class="bi bi-eye"></i> ${view.name}
                    </a>
                </div>
            `;
        });
        
        html += '</div></div>';
    }
    
    schemaTree.innerHTML = html || '<div class="text-muted">未找到数据库对象</div>';
}

// 显示表/视图详细信息
async function showTableDetails(tableName, objectType) {
    const connectionId = document.getElementById('explorer-connection').value;
    const objectDetails = document.getElementById('object-details');
    
    try {
        const response = await fetch(`/api/db-connections/${connectionId}/schema/${objectType}/${tableName}`);
        
        if (response.ok) {
            const details = await response.json();
            displayObjectDetails(details, objectType);
        } else {
            objectDetails.innerHTML = '<div class="text-danger">加载对象详细信息失败</div>';
        }
    } catch (error) {
        objectDetails.innerHTML = '<div class="text-danger">获取对象信息失败</div>';
    }
}

// 显示对象详细信息
function displayObjectDetails(details, objectType) {
    const objectDetails = document.getElementById('object-details');
    
    let html = `<h6><i class="bi bi-${objectType === 'table' ? 'table' : 'eye'}"></i> ${details.name}</h6>`;
    
    // 显示列信息
    if (details.columns && details.columns.length > 0) {
        html += `
            <h6 class="mt-3">列信息</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>列名</th>
                            <th>数据类型</th>
                            <th>可空</th>
                            <th>默认值</th>
                            <th>注释</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        details.columns.forEach(col => {
            html += `
                <tr>
                    <td><strong>${col.name}</strong></td>
                    <td>${col.type}</td>
                    <td>${col.nullable ? '是' : '否'}</td>
                    <td>${col.default || '-'}</td>
                    <td>${col.comment || '-'}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
    }
    
    // 显示索引信息
    if (details.indexes && details.indexes.length > 0) {
        html += `
            <h6 class="mt-3">索引信息</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>索引名</th>
                            <th>列</th>
                            <th>唯一</th>
                            <th>类型</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        details.indexes.forEach(idx => {
            html += `
                <tr>
                    <td><strong>${idx.name}</strong></td>
                    <td>${idx.columns.join(', ')}</td>
                    <td>${idx.unique ? '是' : '否'}</td>
                    <td>${idx.type || '-'}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
    }
    
    objectDetails.innerHTML = html;
}

// 格式化SQL
function formatSQL() {
    const sqlContent = document.getElementById('sql-content');
    const sql = sqlContent.value.trim();
    
    if (!sql) {
        showAlert('请先输入SQL语句', 'warning');
        return;
    }
    
    // 简单的SQL格式化（可以集成更专业的SQL格式化库）
    const formatted = sql
        .replace(/\s+/g, ' ')
        .replace(/\s*,\s*/g, ',\n    ')
        .replace(/\s*(SELECT|FROM|WHERE|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|GROUP BY|ORDER BY|HAVING)\s+/gi, '\n$1 ')
        .replace(/\s*\(\s*/g, ' (')
        .replace(/\s*\)\s*/g, ') ')
        .trim();
    
    sqlContent.value = formatted;
    showAlert('SQL格式化完成', 'success');
}

// 显示版本历史
async function showVersionHistory() {
    if (!currentSQLId) {
        showAlert('请先选择一个SQL语句', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/sql-statements/${currentSQLId}/versions`);
        
        if (response.ok) {
            const versions = await response.json();
            displayVersionHistory(versions);
            const modal = new bootstrap.Modal(document.getElementById('versionHistoryModal'));
            modal.show();
        } else {
            showAlert('加载版本历史失败', 'danger');
        }
    } catch (error) {
        showAlert('加载版本历史失败: ' + error.message, 'danger');
    }
}

// 显示版本历史列表
function displayVersionHistory(versions) {
    const versionList = document.getElementById('version-list');
    
    if (versions.length === 0) {
        versionList.innerHTML = '<div class="text-muted">暂无版本历史</div>';
        return;
    }
    
    let html = '<div class="list-group">';
    
    versions.forEach((version, index) => {
        html += `
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">版本 ${version.version} ${index === 0 ? '<span class="badge bg-primary">当前</span>' : ''}</h6>
                    <small class="text-muted">${new Date(version.created_at).toLocaleString()}</small>
                </div>
                <p class="mb-1">${version.description || '无描述'}</p>
                <div class="mt-2">
                    <button class="btn btn-sm btn-outline-primary" onclick="viewVersion(${version.id})">查看</button>
                    ${index > 0 ? `<button class="btn btn-sm btn-outline-info" onclick="compareVersions(${versions[index-1].id}, ${version.id})">对比</button>` : ''}
                    ${index > 0 ? `<button class="btn btn-sm btn-outline-warning" onclick="selectVersionForRestore(${version.id})">恢复</button>` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    versionList.innerHTML = html;
}

let selectedVersionForRestore = null;

// 选择要恢复的版本
function selectVersionForRestore(versionId) {
    selectedVersionForRestore = versionId;
    document.getElementById('restore-btn').style.display = 'inline-block';
}

// 恢复版本
async function restoreVersion() {
    if (!selectedVersionForRestore) {
        showAlert('请先选择要恢复的版本', 'warning');
        return;
    }
    
    if (!confirm('确定要恢复到选中的版本吗？当前内容将被覆盖。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sql-statements/${currentSQLId}/restore/${selectedVersionForRestore}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('versionHistoryModal'));
            modal.hide();
            loadSQL(currentSQLId); // 重新加载SQL内容
            showAlert('版本恢复成功', 'success');
        } else {
            showAlert('版本恢复失败', 'danger');
        }
    } catch (error) {
        showAlert('版本恢复失败: ' + error.message, 'danger');
    }
}