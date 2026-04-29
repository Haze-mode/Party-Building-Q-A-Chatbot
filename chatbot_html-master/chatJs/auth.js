const API_BASE_URL = 'http://localhost:6006';

// login.html 页面的登录表单处理
$(function() {
    if ($('#loginForm').length && $('#username').length) {
        $('#loginForm').on('submit', function(e) {
            e.preventDefault();
            
            const username = $('#username').val().trim();
            const password = $('#password').val().trim();
            const loginBtn = $('#loginBtn');
            const errorMessage = $('#errorMessage');
            
            if (!username || !password) {
                showError('请输入用户名和密码');
                return;
            }
            
            loginBtn.prop('disabled', true).text('登录中...');
            errorMessage.hide();
            
            $.ajax({
                url: API_BASE_URL + '/api/login',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    username: username,
                    password: password
                }),
                success: function(response) {
                    if (response.success) {
                        localStorage.setItem('token', response.token);
                        localStorage.setItem('username', response.user.username);
                        localStorage.setItem('role', response.user.role);
                        window.location.href = 'index.html';
                    } else {
                        showError('登录失败，请检查用户名和密码');
                    }
                },
                error: function(xhr) {
                    console.error('登录请求失败:', xhr);
                    console.error('状态码:', xhr.status);
                    console.error('响应文本:', xhr.responseText);
                    if (xhr.status === 0) {
                        showError('无法连接到后端服务（http://localhost:6006），请确认后端是否已启动');
                    } else {
                        showError('请求失败：' + xhr.status + ' - ' + xhr.statusText);
                    }
                },
                complete: function() {
                    loginBtn.prop('disabled', false).text('登录');
                }
            });
        });
        
        function showError(message) {
            $('#errorMessage').text(message).show();
        }
    }
});

function getToken() {
    return localStorage.getItem('token');
}

function getUsername() {
    return localStorage.getItem('username');
}

function getRole() {
    return localStorage.getItem('role');
}

function isLoggedIn() {
    return !!getToken();
}

function isAdmin() {
    return getRole() === 'admin';
}

function logout() {
    const token = getToken();
    if (token) {
        $.ajax({
            url: API_BASE_URL + '/api/logout',
            type: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token
            },
            complete: function() {
                clearAuth();
                window.location.href = 'login.html';
            }
        });
    } else {
        clearAuth();
        window.location.href = 'login.html';
    }
}

function clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
}

function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function reloadKnowledgeBase() {
    var kbDir = prompt('请输入知识库目录路径：', '/root/GLM-4/finetune_demo/demo/knowledge_base');
    if (!kbDir) return;
    
    var token = getToken();
    var headers = {};
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }
    
    console.log('开始重载知识库，目录:', kbDir);
    
    $.ajax({
        url: API_BASE_URL + '/api/kb/reload',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ kb_dir: kbDir }),
        headers: headers,
        success: function(response) {
            console.log('知识库重载响应:', response);
            if (response && response.success) {
                alert('知识库重载成功！' + (response.file_count ? '\n文件数量：' + response.file_count : ''));
            } else {
                alert('知识库重载失败：' + (response.message || '未知错误'));
            }
        },
        error: function(xhr) {
            console.error('知识库重载失败:', xhr);
            var errorMsg = '知识库重载失败！\n\n';
            
            if (xhr.status === 500) {
                errorMsg += '服务器内部错误 (500)\n\n';
                errorMsg += '可能原因：\n';
                errorMsg += '1. 后端未实现该接口\n';
                errorMsg += '2. 后端代码有 bug\n';
                errorMsg += '3. 目录路径不存在或没有权限\n';
                errorMsg += '4. 文件处理过程中出现异常\n\n';
                if (xhr.responseText) {
                    errorMsg += '错误详情：\n' + xhr.responseText;
                }
            } else if (xhr.status === 0) {
                errorMsg += '无法连接到后端服务（http://localhost:6006）\n';
                errorMsg += '请确认后端服务是否已启动';
            } else {
                errorMsg += 'HTTP ' + xhr.status + ' - ' + xhr.statusText;
                if (xhr.responseText) {
                    errorMsg += '\n\n' + xhr.responseText;
                }
            }
            
            alert(errorMsg);
        }
    });
}