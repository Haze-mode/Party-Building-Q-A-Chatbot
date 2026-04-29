/*聊天信息*/
function show(avatarSrc, str, isUser) {
    var messageClass = isUser ? 'user-message' : 'ai-message';
    var bubbleClass = isUser ? 'user-bubble' : 'ai-bubble';
    var html = '<div class="message ' + messageClass + '">' +
        '<img class="avatar" src="' + avatarSrc + '" alt="Avatar" />' +
        '<div class="bubble ' + bubbleClass + '">' + str + '</div>' +
        '</div>';
    upView(html);
}

/*更新视图*/
function upView(html) {
    $('.chat-messages').append(html);
    $('.chat-messages').animate({scrollTop: $('.chat-messages')[0].scrollHeight}, 200);
}

var flag = true;
var message = '';
var sessionId = '';

$(function () {
    initSession();
    setupUI();
    setupEventHandlers();
    
    function initSession() {
        const guestMode = getUrlParameter('guest');
        if (guestMode === 'true' || !isLoggedIn()) {
            // 游客模式或未登录，显示菜单但隐藏知识库管理和退出登录
            sessionId = 'guest_' + Date.now();
            $('#userInfo').show();
            $('#usernameDisplay').text('游客');
            $('#loginBtn').hide();
            $('.admin-only').hide();
            $('#logoutBtn').hide();
        } else if (isLoggedIn()) {
            sessionId = getUsername();
            $('#userInfo').show();
            $('#usernameDisplay').text(getUsername());
            $('#loginBtn').hide();
            if (isAdmin()) {
                $('.admin-only').show();
            }
        }
    }
    
    function setupUI() {
        $('#inputVal').focus();
        $('.send-button').prop('disabled', true);
    }
    
    function setupEventHandlers() {
        $('#inputVal').on('input', function () {
            var sendBtn = $('.send-button');
            if ($(this).val().length > 0) {
                sendBtn.prop('disabled', false);
            } else {
                sendBtn.prop('disabled', true);
            }
        });

        $('.send-button').click(getMessage);
        $('.input-wrapper').on('submit', function () {
            getMessage();
            return false;
        });
        $(document).keyup(function (ev) {
            if (ev.keyCode == 13 && $('#inputVal').is(':focus')) {
                getMessage();
            }
        });
        
        $('#menuBtn').click(function(e) {
            e.stopPropagation();
            $('#menuContent').toggleClass('show');
        });
        
        $(document).click(function() {
            $('#menuContent').removeClass('show');
        });
        
        $('#viewHistory').click(viewHistory);
        $('#exportChat').click(exportChat);
        $('#clearSession').click(clearSession);
        $('#logoutBtn').click(logout);
        $('#kbManage').click(function() {
            window.location.href = 'kb_manager.html';
        });
        $('#kbReload').click(reloadKnowledgeBase);
        $('#loginBtn').click(openLoginModal);
        setupUploadHandlers();
        setupLoginHandlers();
    }
    
    function getMessage() {
        var val = $('#inputVal').val();
        if (val == '')
            return;
        if (flag) {
            flag = false;

            show("./chatImages/woman.png", $('#inputVal').val(), true);
            
            $('#inputVal').val('');
            $('.send-button').prop('disabled', true);
            
            const token = getToken();
            const headers = {};
            if (token) {
                headers['Authorization'] = 'Bearer ' + token;
            }
            
            $.ajax({
                type: "POST",
                dataType: "json",
                contentType: "application/json",
                async: true,
                url: API_BASE_URL + "/api/chatbot",
                headers: headers,
                data: JSON.stringify({
                    infos: val,
                    session_id: sessionId
                }),
                success: function (data) {
                    flag = true;
                    if (data.answer) {
                        setTimeout(function () {
                            show("chatImages/man.png", data.answer, false);
                        }, 500);
                    } else {
                        show("chatImages/man.png", "抱歉，我没有找到相关答案。", false);
                    }
                },
                error: function (xhr) {
                    flag = true;
                    show("chatImages/man.png", "请求失败，请稍后重试。", false);
                }
            });
        }
    }
    
    function viewHistory() {
        // 优先从当前页面读取对话历史
        var messages = [];
        $('.message').each(function() {
            var isUser = $(this).hasClass('user-message');
            var text = $(this).find('.bubble').text().trim();
            if (text) {
                messages.push({
                    type: isUser ? 'question' : 'answer',
                    content: text
                });
            }
        });
        
        if (messages.length === 0) {
            alert('当前没有对话历史');
            return;
        }
        
        displayHistory(messages);
        openModal('historyModal');
    }
    
    function displayHistory(history) {
        let html = '';
        if (!history || history.length === 0) {
            html = '<p style="text-align: center; color: #999;">暂无历史记录</p>';
        } else {
            // 将消息配对显示（一问一答）
            for (let i = 0; i < history.length; i += 2) {
                var question = history[i];
                var answer = history[i + 1];
                
                html += '<div class="history-item">';
                if (question && question.content) {
                    html += '<div class="history-question">问：' + escapeHtml(question.content) + '</div>';
                }
                if (answer && answer.content) {
                    html += '<div class="history-answer">答：' + escapeHtml(answer.content) + '</div>';
                }
                html += '</div>';
            }
        }
        $('#historyContent').html(html);
    }
    
    function exportChat() {
        var messages = [];
        $('.message').each(function() {
            var isUser = $(this).hasClass('user-message');
            var text = $(this).find('.bubble').html();
            if (text && text.trim()) {
                messages.push({
                    type: isUser ? 'user' : 'assistant',
                    content: text.trim()
                });
            }
        });
        
        if (messages.length === 0) {
            alert('当前没有对话可以导出');
            return;
        }
        
        // 生成 HTML 格式的文档
        var now = new Date();
        var timeStr = now.getFullYear() + '-' + 
                      String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                      String(now.getDate()).padStart(2, '0') + ' ' +
                      String(now.getHours()).padStart(2, '0') + ':' +
                      String(now.getMinutes()).padStart(2, '0');
        
        var htmlContent = '<html xmlns:o="urn:schemas-microsoft-com:office:office" ' +
                         'xmlns:w="urn:schemas-microsoft-com:office:word" ' +
                         'xmlns="http://www.w3.org/TR/REC-html40">';
        htmlContent += '<head><meta charset="utf-8"><title>对话记录</title>';
        htmlContent += '<style>';
        htmlContent += 'body { font-family: 宋体, SimSun, serif; font-size: 12pt; line-height: 1.6; padding: 40px; }';
        htmlContent += 'h1 { text-align: center; font-size: 18pt; margin-bottom: 20px; color: #C91F37; }';
        htmlContent += '.info { text-align: center; color: #666; margin-bottom: 30px; font-size: 10pt; }';
        htmlContent += '.message { margin-bottom: 20px; }';
        htmlContent += '.user { background: #f0f8ff; padding: 15px; border-left: 4px solid #2196F3; margin-bottom: 15px; }';
        htmlContent += '.assistant { background: #fff5f5; padding: 15px; border-left: 4px solid #C91F37; margin-bottom: 15px; }';
        htmlContent += '.label { font-weight: bold; margin-bottom: 5px; }';
        htmlContent += '.user .label { color: #2196F3; }';
        htmlContent += '.assistant .label { color: #C91F37; }';
        htmlContent += '.content { margin-top: 8px; }';
        htmlContent += '</style></head><body>';
        htmlContent += '<h1>党建知识问答 - 对话记录</h1>';
        htmlContent += '<div class="info">导出时间：' + timeStr + ' | 对话轮数：' + Math.ceil(messages.length / 2) + '</div>';
        
        messages.forEach(function(msg) {
            var label = msg.type === 'user' ? '👤 用户提问' : '🤖 AI 回答';
            var className = msg.type === 'user' ? 'user' : 'assistant';
            htmlContent += '<div class="message ' + className + '">';
            htmlContent += '<div class="label">' + label + '</div>';
            htmlContent += '<div class="content">' + msg.content + '</div>';
            htmlContent += '</div>';
        });
        
        htmlContent += '</body></html>';
        
        // 创建下载链接
        var blob = new Blob([htmlContent], { type: 'application/msword;charset=utf-8' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = '对话记录_' + now.getTime() + '.doc';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        alert('对话已导出为 DOC 文件！');
    }
    
    function clearSession() {
        if (confirm('确定要清空当前会话吗？')) {
            $.ajax({
                url: API_BASE_URL + '/api/session/clear',
                type: 'GET',
                data: { session_id: sessionId },
                headers: getAuthHeaders(),
                success: function() {
                    alert('会话已清空');
                    $('.chat-messages').empty();
                    show("chatImages/man.png", "<p>你好，我是党建小助手！可以问我关于党建文件、政策解读等问题。</p>", false);
                },
                error: function() {
                    alert('清空会话失败');
                }
            });
        }
    }
    
    function openKbModal() {
        openModal('kbModal');
    }
    
    function setupUploadHandlers() {
        const uploadArea = $('#uploadArea');
        const fileInput = $('#fileInput');
        
        uploadArea.click(function() {
            fileInput.click();
        });
        
        uploadArea.on('dragover', function(e) {
            e.preventDefault();
            $(this).addClass('dragover');
        });
        
        uploadArea.on('dragleave', function() {
            $(this).removeClass('dragover');
        });
        
        uploadArea.on('drop', function(e) {
            e.preventDefault();
            $(this).removeClass('dragover');
            const files = e.originalEvent.dataTransfer.files;
            handleFiles(files);
        });
        
        fileInput.change(function() {
            handleFiles(this.files);
        });
    }
    
    function handleFiles(files) {
        if (files.length === 0) return;
        
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('file', files[i]);
        }
        
        $('#uploadStatus').html('<p>正在上传...</p>');
        
        $.ajax({
            url: API_BASE_URL + '/api/kb/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: getAuthHeaders(),
            success: function(response) {
                $('#uploadStatus').html('<p style="color: green;">上传成功！</p>');
                setTimeout(function() {
                    closeModal('kbModal');
                    $('#uploadStatus').html('');
                }, 1500);
            },
            error: function() {
                $('#uploadStatus').html('<p style="color: red;">上传失败，请重试</p>');
            }
        });
    }
    
    function getAuthHeaders() {
        const token = getToken();
        const headers = {};
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }
        return headers;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function openLoginModal() {
        openModal('loginModal');
    }
    
    function setupLoginHandlers() {
        $('#loginForm').on('submit', function(e) {
            e.preventDefault();
            
            const username = $('#loginUsername').val().trim();
            const password = $('#loginPassword').val().trim();
            const loginBtn = $('#loginSubmitBtn');
            const errorMessage = $('#loginError');
            
            console.log('登录按钮被点击', { username: username, hasPassword: !!password });
            
            if (!username || !password) {
                showError('请输入用户名和密码');
                return;
            }
            
            loginBtn.prop('disabled', true).text('登录中...');
            errorMessage.hide();
            
            console.log('准备发送请求到:', API_BASE_URL + '/api/login');
            
            $.ajax({
                url: API_BASE_URL + '/api/login',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    username: username,
                    password: password
                }),
                success: function(response) {
                    console.log('登录成功，响应:', response);
                    if (response.success) {
                        localStorage.setItem('token', response.token);
                        localStorage.setItem('username', response.user.username);
                        localStorage.setItem('role', response.user.role);
                        alert('登录成功！');
                        closeModal('loginModal');
                        location.reload();
                    } else {
                        showError('登录失败，请检查用户名和密码');
                    }
                },
                error: function(xhr) {
                    console.error('登录请求失败:', xhr);
                    if (xhr.status === 0) {
                        showError('无法连接到后端服务，请确认 http://localhost:6006 是否已启动');
                    } else {
                        showError('请求失败：' + xhr.status + ' ' + xhr.statusText);
                    }
                },
                complete: function() {
                    loginBtn.prop('disabled', false).text('登录');
                }
            });
        });
        
        function showError(message) {
            $('#loginError').text(message).show();
        }
    }
});

function openModal(modalId) {
    $('#' + modalId).css('display', 'block');
}

function closeModal(modalId) {
    $('#' + modalId).css('display', 'none');
}

function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}