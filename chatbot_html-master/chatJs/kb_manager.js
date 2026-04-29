// 知识库管理逻辑（API_BASE_URL 已在 auth.js 中声明）

$(function() {
    // 检查管理员权限
    if (!isAdmin()) {
        alert('您没有权限访问此页面');
        window.location.href = 'index.html';
        return;
    }
    
    loadFileList();
    setupUploadHandlers();
});

function loadFileList() {
    var token = getToken();
    var headers = {};
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }
    
    // 尝试从后端获取文件列表
    $.ajax({
        url: API_BASE_URL + '/api/kb/files',
        type: 'GET',
        headers: headers,
        success: function(response) {
            if (response && response.files) {
                displayFileList(response.files);
                updateStats(response.files);
            } else {
                // 如果后端没有实现，使用本地存储
                var files = getKBFiles();
                displayFileList(files);
                updateStats(files);
            }
        },
        error: function(xhr) {
            console.log('后端未实现文件列表接口，使用本地存储');
            // 后端未实现，使用本地存储
            var files = getKBFiles();
            displayFileList(files);
            updateStats(files);
        }
    });
}

function displayFileList(files) {
    var fileList = $('#fileList');
    
    if (!files || files.length === 0) {
        fileList.html('<div class="kb-empty">暂无文件，请上传知识库文件</div>');
        return;
    }
    
    var html = '';
    files.forEach(function(file, index) {
        html += '<div class="kb-file-item" data-index="' + index + '">';
        html += '  <div class="kb-file-info">';
        html += '    <div class="kb-file-name">' + escapeHtml(file.name) + '</div>';
        html += '    <div class="kb-file-meta">大小：' + formatFileSize(file.size) + ' | 上传时间：' + file.uploadTime + '</div>';
        html += '  </div>';
        html += '  <div class="kb-file-actions">';
        html += '    <button class="kb-action-btn delete" onclick="deleteFile(\'' + file.name.replace(/'/g, "\\'") + '\')">删除</button>';
        html += '  </div>';
        html += '</div>';
    });
    
    fileList.html(html);
}

function updateStats(files) {
    $('#fileCount').text(files ? files.length : 0);
    
    var totalSize = 0;
    if (files) {
        files.forEach(function(file) {
            totalSize += file.size || 0;
        });
    }
    $('#kbSize').text(formatFileSize(totalSize));
    
    var lastUpdate = '-';
    if (files && files.length > 0) {
        lastUpdate = files[files.length - 1].uploadTime || '-';
    }
    $('#lastUpdate').text(lastUpdate);
}

function setupUploadHandlers() {
    var uploadArea = $('#uploadArea');
    var fileInput = $('#fileInput');
    
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
        var files = e.originalEvent.dataTransfer.files;
        handleFiles(files);
    });
    
    fileInput.change(function() {
        handleFiles(this.files);
    });
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    $('#uploadProgress').show();
    $('#uploadSuccess').hide();
    $('#uploadError').hide();
    
    var formData = new FormData();
    for (var i = 0; i < files.length; i++) {
        formData.append('file', files[i]);
    }
    
    var token = getToken();
    var headers = {};
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }
    
    $.ajax({
        url: API_BASE_URL + '/api/kb/upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: headers,
        success: function(response) {
            $('#uploadProgress').hide();
            $('#uploadSuccess').show();
            
            // 保存到本地存储
            saveUploadedFiles(files);
            
            setTimeout(function() {
                $('#uploadSuccess').hide();
                loadFileList();
            }, 2000);
        },
        error: function(xhr) {
            $('#uploadProgress').hide();
            $('#uploadError').show();
            console.error('上传失败:', xhr);
            
            setTimeout(function() {
                $('#uploadError').hide();
            }, 3000);
        }
    });
}

function deleteFile(fileName) {
    if (!fileName) {
        alert('文件名不能为空');
        return;
    }
    
    if (!confirm('确定要删除文件「' + fileName + '」吗？\n删除后将无法恢复！')) {
        return;
    }
    
    var token = getToken();
    var headers = {};
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }
    
    // 尝试调用后端删除接口
    $.ajax({
        url: API_BASE_URL + '/api/kb/files/' + encodeURIComponent(fileName),
        type: 'DELETE',
        headers: headers,
        success: function(response) {
            if (response.success) {
                alert('文件删除成功！');
                loadFileList();
            } else {
                alert('删除失败：' + (response.message || '未知错误'));
            }
        },
        error: function(xhr) {
            console.log('后端删除接口未实现，使用本地删除');
            // 后端未实现，使用本地删除
            var files = getKBFiles();
            var newFiles = files.filter(function(f) {
                return f.name !== fileName;
            });
            localStorage.setItem('kbFiles', JSON.stringify(newFiles));
            loadFileList();
            alert('文件已从本地列表删除');
        }
    });
}

function getKBFiles() {
    var files = localStorage.getItem('kbFiles');
    return files ? JSON.parse(files) : [];
}

function saveUploadedFiles(files) {
    var existingFiles = getKBFiles();
    var now = new Date().toLocaleString('zh-CN');
    
    for (var i = 0; i < files.length; i++) {
        existingFiles.push({
            name: files[i].name,
            size: files[i].size,
            uploadTime: now
        });
    }
    
    localStorage.setItem('kbFiles', JSON.stringify(existingFiles));
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    var k = 1024;
    var sizes = ['B', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function reloadKnowledgeBase() {
    var kbDir = prompt('请输入知识库目录路径：', '/root/GLM-4/finetune_demo/demo/knowledge_base');
    if (!kbDir) return;
    
    var token = getToken();
    var headers = {};
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }
    
    $.ajax({
        url: API_BASE_URL + '/api/kb/reload',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ kb_dir: kbDir }),
        headers: headers,
        success: function(response) {
            alert('知识库重载成功！');
            loadFileList();
        },
        error: function(xhr) {
            alert('知识库重载失败：' + (xhr.responseText || '未知错误'));
        }
    });
}
