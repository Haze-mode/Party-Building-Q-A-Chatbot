"""
API请求处理器模块
包含所有HTTP请求处理逻辑
"""
import json
import logging
import os
import tornado.web
from typing import Optional, Dict, Any

from auth import auth_service, require_auth
from config import settings
from cache import answer_cache, retrieval_cache

logger = logging.getLogger(__name__)


class BaseHandler(tornado.web.RequestHandler):
    """基础请求处理器，处理CORS和通用逻辑"""
    
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Content-Type', 'application/json; charset=utf-8')
    
    def options(self, *args, **kwargs):
        """处理OPTIONS预检请求"""
        self.set_status(204)
        self.finish()
    
    def write_success(self, data: dict = None):
        """写入成功响应"""
        response = {'success': True}
        if data:
            response.update(data)
        self.write(response)
    
    def write_error_response(self, status_code: int, error: str):
        """写入错误响应"""
        self.set_status(status_code)
        self.write({'success': False, 'error': error})


class LoginHandler(BaseHandler):
    """用户登录处理器"""
    
    def post(self):
        try:
            body = self._parse_json_body()
        except ValueError as e:
            self.write_error_response(400, str(e))
            return
        
        username = body.get('username')
        password = body.get('password')
        
        if not username or not password:
            self.write_error_response(400, '用户名和密码不能为空')
            return
        
        success, token, user, error = auth_service.login(username, password)
        
        if not success:
            self.write_error_response(401, error)
            return
        
        self.write_success({
            'token': token,
            'user': user.to_dict()
        })
    
    def _parse_json_body(self) -> dict:
        """解析JSON请求体"""
        try:
            return json.loads(self.request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            raise ValueError('请求体不是合法的JSON格式')


class LogoutHandler(BaseHandler):
    """用户登出处理器"""
    
    def post(self):
        auth_header = self.request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_service.logout(token)
        
        self.write_success()


class ChatbotHandler(BaseHandler):
    """聊天机器人处理器"""
    
    def __init__(self, application, request, chat_engine=None, **kwargs):
        super().__init__(application, request, **kwargs)
        self.chat_engine = chat_engine
    
    def _parse_request(self) -> dict:
        """解析请求参数（支持GET和POST）"""
        if self.request.method == 'GET':
            return self._parse_get_params()
        else:
            return self._parse_post_body()
    
    def _parse_get_params(self) -> dict:
        """解析GET请求参数"""
        data = {
            'infos': self.get_query_argument('infos', default=None),
            'session_id': self.get_query_argument('session_id', default='default'),
            'system_prompt': self.get_query_argument('system_prompt', default=None),
            'format': self.get_query_argument('format', default='json'),
        }
        
        # 解析可选数值参数
        for param, cast_type in [('top_p', float), ('temperature', float), ('max_new_tokens', int)]:
            value = self.get_query_argument(param, default=None)
            if value is not None:
                try:
                    data[param] = cast_type(value)
                except (ValueError, TypeError):
                    pass
        
        return data
    
    def _parse_post_body(self) -> dict:
        """解析POST请求体"""
        try:
            body = json.loads(self.request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            raise ValueError('请求体不是合法的JSON格式')
        
        return {
            'infos': body.get('infos') or body.get('query') or body.get('prompt'),
            'session_id': body.get('session_id', 'default'),
            'system_prompt': body.get('system_prompt'),
            'format': body.get('format', 'json'),
            'top_p': body.get('top_p'),
            'temperature': body.get('temperature'),
            'max_new_tokens': body.get('max_new_tokens'),
        }
    
    def _write_result(self, result: dict, raw: bool = False):
        """写入响应结果"""
        if raw:
            self.set_header('Content-Type', 'text/plain; charset=utf-8')
            self.write(result['answer'])
        else:
            self.write(result)
    
    def _handle_chat_request(self):
        """处理聊天请求的核心逻辑"""
        data = self._parse_request()
        
        infos = data.get('infos')
        if not infos:
            raise ValueError("缺少必填参数 'infos'")
        
        session_id = data.get('session_id', 'default')
        response_format = data.get('format', 'json')
        raw = str(response_format).lower() in ['text', 'raw']
        
        # 调用聊天引擎生成回答
        result = self.chat_engine.generate_response(
            user_input=infos,
            session_id=session_id,
            system_prompt=data.get('system_prompt'),
            max_new_tokens=data.get('max_new_tokens'),
            top_p=data.get('top_p'),
            temperature=data.get('temperature'),
        )
        
        self._write_result(result, raw=raw)
        logger.info(f"会话 {session_id}: 问题已处理")
    
    def get(self):
        """处理GET请求"""
        try:
            self._handle_chat_request()
        except ValueError as e:
            self.write_error_response(400, str(e))
            logger.warning(f"客户端错误: {e}")
        except RuntimeError as e:
            self.write_error_response(500, str(e))
            logger.error(f"服务端错误: {e}")
        except Exception as e:
            self.write_error_response(500, "服务器内部错误")
            logger.critical(f"未预期异常: {e}", exc_info=True)
    
    def post(self):
        """处理POST请求"""
        try:
            self._handle_chat_request()
        except ValueError as e:
            self.write_error_response(400, str(e))
            logger.warning(f"客户端错误: {e}")
        except RuntimeError as e:
            self.write_error_response(500, str(e))
            logger.error(f"服务端错误: {e}")
        except Exception as e:
            self.write_error_response(500, "服务器内部错误")
            logger.critical(f"未预期异常: {e}", exc_info=True)


class SessionHistoryHandler(BaseHandler):
    """会话历史查询处理器"""
    
    def __init__(self, application, request, chat_engine=None, **kwargs):
        super().__init__(application, request, **kwargs)
        self.chat_engine = chat_engine
    
    def get(self):
        session_id = self.get_query_argument('session_id', default='default')
        history = self.chat_engine.get_session_history(session_id)
        
        self.write_success({
            'session_id': session_id,
            'history': history,
            'history_length': len(history),
        })


class SessionClearHandler(BaseHandler):
    """会话清空处理器"""
    
    def __init__(self, application, request, chat_engine=None, **kwargs):
        super().__init__(application, request, **kwargs)
        self.chat_engine = chat_engine
    
    def get(self):
        session_id = self.get_query_argument('session_id', default='default')
        self.chat_engine.clear_session(session_id)
        
        self.write_success({
            'session_id': session_id,
            'cleared': True,
        })


class SessionListHandler(BaseHandler):
    """会话列表处理器"""
    
    def __init__(self, application, request, chat_engine=None, **kwargs):
        super().__init__(application, request, **kwargs)
        self.chat_engine = chat_engine
    
    def get(self):
        self.write_success({
            'session_count': len(self.chat_engine.sessions),
            'sessions': list(self.chat_engine.sessions.keys()),
        })


class KnowledgeReloadHandler(BaseHandler):
    """知识库重载处理器（需要管理员权限）"""
    
    def __init__(self, application, request, knowledge_base=None, **kwargs):
        super().__init__(application, request, **kwargs)
        self.kb = knowledge_base
    
    @require_auth('admin')
    def get(self):
        kb_dir = self.get_query_argument('kb_dir', default=None)
        self._reload_kb(kb_dir)
    
    @require_auth('admin')
    def post(self):
        try:
            body = json.loads(self.request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            self.write_error_response(400, '请求体不是合法的JSON格式')
            return
        
        kb_dir = body.get('kb_dir')
        self._reload_kb(kb_dir)
    
    def _reload_kb(self, kb_dir: Optional[str] = None):
        """执行知识库重载"""
        # 验证参数
        if not kb_dir:
            self.write_error_response(400, '知识库目录路径不能为空')
            return
        
        # 检查目录是否存在
        if not os.path.exists(kb_dir):
            self.write_error_response(404, f'知识库目录不存在：{kb_dir}')
            return
        
        try:
            # 重载知识库
            self.kb.reload(kb_dir)
            
            # 统计文件数量
            file_count = 0
            if os.path.exists(self.kb.kb_dir):
                file_count = len([f for f in os.listdir(self.kb.kb_dir) 
                                 if os.path.isfile(os.path.join(self.kb.kb_dir, f))])
            
            self.write_success({
                'message': '知识库重载成功',
                'file_count': file_count,
                'kb_dir': self.kb.kb_dir,
                'paragraph_count': len(self.kb.paragraphs),
            })
            logger.info(f"知识库重载成功: {kb_dir}, 文件数: {file_count}")
            
            # 🗑️ 清除相关缓存（知识库已更新）
            retrieval_cache.clear()
            answer_cache.clear()
            logger.info("🗑️  知识库重载，已清除所有缓存")
        except Exception as e:
            self.write_error_response(500, f'重载知识库失败：{str(e)}')
            logger.error(f"知识库重载失败: {e}", exc_info=True)


class KnowledgeFilesHandler(BaseHandler):
    """知识库文件列表处理器（需要管理员权限）"""
    
    def __init__(self, application, request, knowledge_base=None, **kwargs):
        super().__init__(application, request, **kwargs)
        self.kb = knowledge_base
    
    @require_auth('admin')
    def get(self):
        """获取知识库文件列表"""
        try:
            files = self._get_kb_files()
            self.write_success({
                'files': files,
                'total_count': len(files),
            })
        except Exception as e:
            self.write_error_response(500, str(e))
            logger.error(f"获取文件列表失败: {e}", exc_info=True)
    
    def _get_kb_files(self) -> list:
        """获取知识库目录下的所有文件信息"""
        kb_dir = self.kb.kb_dir
        
        if not os.path.exists(kb_dir):
            return []
        
        files = []
        for filename in os.listdir(kb_dir):
            filepath = os.path.join(kb_dir, filename)
            
            # 只处理文件，跳过目录
            if not os.path.isfile(filepath):
                continue
            
            try:
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'uploadTime': self._format_time(stat.st_mtime),
                    'path': filepath,
                })
            except Exception as e:
                logger.warning(f"无法获取文件信息 {filename}: {e}")
                continue
        
        # 按修改时间降序排列（最新的在前）
        files.sort(key=lambda x: x['uploadTime'], reverse=True)
        return files
    
    def _format_time(self, timestamp: float) -> str:
        """格式化时间戳为字符串"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


class KnowledgeFileDeleteHandler(BaseHandler):
    """知识库文件删除处理器（需要管理员权限）"""
    
    def __init__(self, application, request, knowledge_base=None, **kwargs):
        super().__init__(application, request, **kwargs)
        self.kb = knowledge_base
    
    @require_auth('admin')
    def delete(self, filename: str = None):
        """通过URL参数删除文件 - DELETE /api/kb/files/<filename>"""
        if not filename:
            self.write_error_response(400, '请提供文件名')
            return
        
        # URL解码文件名
        from urllib.parse import unquote
        filename = unquote(filename)
        
        file_path = os.path.join(self.kb.kb_dir, filename)
        
        try:
            self._delete_file(file_path)
            self.write_success({
                'message': '文件删除成功',
                'file_name': filename,
            })
            logger.info(f"文件已删除: {file_path}")
        except FileNotFoundError:
            self.write_error_response(404, '文件不存在')
        except Exception as e:
            self.write_error_response(500, f'删除文件失败: {str(e)}')
            logger.error(f"删除文件失败: {e}", exc_info=True)
    
    @require_auth('admin')
    def post(self):
        """通过请求体删除文件 - POST /api/kb/files/delete"""
        try:
            body = json.loads(self.request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            self.write_error_response(400, '请求体不是合法的JSON格式')
            return
        
        file_name = body.get('file_name')
        file_path = body.get('file_path')
        
        if not file_name and not file_path:
            self.write_error_response(400, '请提供 file_name 或 file_path')
            return
        
        # 如果只提供文件名，构建完整路径
        if not file_path:
            file_path = os.path.join(self.kb.kb_dir, file_name)
        
        try:
            self._delete_file(file_path)
            self.write_success({
                'message': '文件删除成功',
                'file_name': os.path.basename(file_path),
            })
            logger.info(f"文件已删除: {file_path}")
        except FileNotFoundError:
            self.write_error_response(404, '文件不存在')
        except Exception as e:
            self.write_error_response(500, f'删除文件失败: {str(e)}')
            logger.error(f"删除文件失败: {e}", exc_info=True)
    
    def _delete_file(self, file_path: str):
        """删除文件并重新加载知识库"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 删除文件
        os.remove(file_path)
        logger.info(f"已删除文件: {file_path}")
        
        # 重新加载知识库
        try:
            self.kb.reload()
            logger.info("知识库已重新加载")
            
            # 🗑️ 清除相关缓存（知识库已更新）
            retrieval_cache.clear()
            answer_cache.clear()
            logger.info("🗑️  知识库更新，已清除所有缓存")
        except Exception as e:
            logger.warning(f"知识库重载失败: {e}")
            # 即使重载失败，文件已经删除，仍然返回成功


class KnowledgeUploadHandler(BaseHandler):
    """知识库文件上传处理器（需要管理员权限）"""
    
    def __init__(self, application, request, knowledge_base=None, **kwargs):
        super().__init__(application, request, **kwargs)
        self.kb = knowledge_base
    
    @require_auth('admin')
    def post(self):
        files = self.request.files.get('file') or self.request.files.get('files') or []
        
        if not files:
            self.write_error_response(400, '请上传文件，字段名为 file 或 files')
            return
        
        saved_files, errors = self._save_uploaded_files(files)
        
        if not saved_files:
            self.write_error_response(500, f'文件保存失败: {errors}')
            return
        
        # 上传成功后自动重载知识库
        try:
            self.kb.reload()
            
            # 🗑️ 清除相关缓存（知识库已更新）
            retrieval_cache.clear()
            answer_cache.clear()
            logger.info("🗑️  知识库更新，已清除所有缓存")
            
            # 构建响应数据（兼容单文件和多文件）
            if len(saved_files) == 1:
                # 单文件上传：返回file对象
                file_info = {
                    'name': saved_files[0],
                    'size': os.path.getsize(os.path.join(self.kb.kb_dir, saved_files[0])),
                    'path': os.path.join(self.kb.kb_dir, saved_files[0]),
                }
                self.write_success({
                    'message': '文件上传成功',
                    'file': file_info,
                    'kb_dir': self.kb.kb_dir,
                    'paragraph_count': len(self.kb.paragraphs),
                    'errors': errors,
                })
            else:
                # 多文件上传：返回saved_files数组
                self.write_success({
                    'message': f'{len(saved_files)} 个文件上传成功',
                    'saved_files': saved_files,
                    'kb_dir': self.kb.kb_dir,
                    'paragraph_count': len(self.kb.paragraphs),
                    'errors': errors,
                })
            
            logger.info(f"上传并加载了 {len(saved_files)} 个文件")
        except Exception as e:
            self.write_error_response(500, str(e))
            logger.error(f"知识库重载失败: {e}", exc_info=True)
    
    def _save_uploaded_files(self, files: list) -> tuple:
        """保存上传的文件"""
        saved_files = []
        errors = []
        
        os.makedirs(self.kb.kb_dir, exist_ok=True)
        
        for item in files:
            filename = item.get('filename')
            body = item.get('body')
            
            if not filename or body is None:
                continue
            
            dest_path = os.path.join(self.kb.kb_dir, filename)
            try:
                with open(dest_path, 'wb') as f:
                    f.write(body)
                saved_files.append(filename)
                logger.info(f"文件已保存: {filename}")
            except Exception as e:
                error_msg = f"{filename}: {e}"
                errors.append(error_msg)
                logger.error(f"文件保存失败: {error_msg}")
        
        return saved_files, errors


def create_handlers(chat_engine, knowledge_base) -> list:
    """
    创建所有路由处理器
    
    Args:
        chat_engine: 聊天引擎实例
        knowledge_base: 知识库实例
        
    Returns:
        路由配置列表
    """
    return [
        (r'/api/login', LoginHandler),
        (r'/api/logout', LogoutHandler),
        (r'/api/chatbot', ChatbotHandler, {'chat_engine': chat_engine}),
        (r'/api/session/history', SessionHistoryHandler, {'chat_engine': chat_engine}),
        (r'/api/session/clear', SessionClearHandler, {'chat_engine': chat_engine}),
        (r'/api/session/list', SessionListHandler, {'chat_engine': chat_engine}),
        (r'/api/kb/files/delete', KnowledgeFileDeleteHandler, {'knowledge_base': knowledge_base}),
        (r'/api/kb/files/(.+)', KnowledgeFileDeleteHandler, {'knowledge_base': knowledge_base}),
        (r'/api/kb/files', KnowledgeFilesHandler, {'knowledge_base': knowledge_base}),
        (r'/api/kb/reload', KnowledgeReloadHandler, {'knowledge_base': knowledge_base}),
        (r'/api/kb/upload', KnowledgeUploadHandler, {'knowledge_base': knowledge_base}),
    ]
