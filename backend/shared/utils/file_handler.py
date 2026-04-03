"""
文件处理工具
提供文件上传、存储和读取功能
"""
import os
import base64
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from shared.utils.logger import chat_logger


class FileHandler:
    """文件处理器"""
    
    # 支持的图片类型
    IMAGE_TYPES = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'image/bmp': '.bmp'
    }
    
    # 支持的文档类型
    DOCUMENT_TYPES = {
        'text/plain': '.txt',
        'text/markdown': '.md',
        'application/pdf': '.pdf',
        'application/json': '.json',
        'text/csv': '.csv',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx'
    }
    
    def __init__(self, upload_dir: str = "uploads"):
        """初始化文件处理器"""
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        self.image_dir = self.upload_dir / "images"
        self.document_dir = self.upload_dir / "documents"
        self.image_dir.mkdir(exist_ok=True)
        self.document_dir.mkdir(exist_ok=True)
    
    def save_file(self, content: bytes, content_type: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        保存上传的文件
        
        Args:
            content: 文件内容（bytes）
            content_type: MIME类型
            filename: 原始文件名（可选）
            
        Returns:
            文件信息字典
        """
        # 生成唯一文件名
        file_hash = hashlib.md5(content).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确定文件类型和扩展名
        if content_type in self.IMAGE_TYPES:
            ext = self.IMAGE_TYPES[content_type]
            sub_dir = self.image_dir
            file_type = "image"
        elif content_type in self.DOCUMENT_TYPES:
            ext = self.DOCUMENT_TYPES[content_type]
            sub_dir = self.document_dir
            file_type = "document"
        else:
            # 未知类型，尝试从文件名获取扩展名
            if filename and '.' in filename:
                ext = '.' + filename.split('.')[-1].lower()
            else:
                ext = '.bin'
            sub_dir = self.document_dir
            file_type = "unknown"
        
        # 生成存储文件名
        storage_filename = f"{timestamp}_{file_hash}{ext}"
        file_path = sub_dir / storage_filename
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(content)
        
        chat_logger.info(f"文件已保存: {file_path}, 类型: {file_type}, 大小: {len(content)} bytes")
        
        return {
            "file_id": file_hash,
            "filename": filename or storage_filename,
            "storage_path": str(file_path),
            "file_type": file_type,
            "content_type": content_type,
            "size": len(content),
            "url": f"/uploads/{file_type}s/{storage_filename}"
        }
    
    def save_base64_image(self, base64_data: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        保存Base64编码的图片
        
        Args:
            base64_data: Base64编码的图片数据（可包含 data:image/xxx;base64, 前缀）
            filename: 原始文件名（可选）
            
        Returns:
            文件信息字典
        """
        # 解析Base64数据
        if ',' in base64_data:
            header, encoded = base64_data.split(',', 1)
            # 从header中提取MIME类型
            if 'data:' in header:
                content_type = header.split(';')[0].replace('data:', '')
            else:
                content_type = 'image/png'  # 默认
        else:
            encoded = base64_data
            content_type = 'image/png'  # 默认
        
        # 解码
        content = base64.b64decode(encoded)
        
        return self.save_file(content, content_type, filename)
    
    def read_file(self, file_path: str) -> Optional[bytes]:
        """读取文件内容"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            chat_logger.error(f"读取文件失败: {file_path}, 错误: {e}")
            return None
    
    def read_text_file(self, file_path: str) -> Optional[str]:
        """读取文本文件内容"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            chat_logger.error(f"读取文本文件失败: {file_path}, 错误: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                "filename": path.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            chat_logger.error(f"获取文件信息失败: {file_path}, 错误: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                chat_logger.info(f"文件已删除: {file_path}")
                return True
            return False
        except Exception as e:
            chat_logger.error(f"删除文件失败: {file_path}, 错误: {e}")
            return False


# 创建全局文件处理器实例
file_handler = FileHandler()
