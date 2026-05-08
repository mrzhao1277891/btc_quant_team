"""
配置管理模块

加载和管理回测系统的配置
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径，默认为 config/backtest.yaml
        """
        # 加载环境变量
        load_dotenv()
        
        # 确定配置文件路径
        if config_file is None:
            # 从当前文件向上查找项目根目录
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            config_file = project_root / "config" / "backtest.yaml"
        else:
            config_file = Path(config_file)
        
        # 加载配置文件
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {}
        
        # 从环境变量覆盖敏感配置
        self._override_from_env()
    
    def _override_from_env(self):
        """从环境变量覆盖配置"""
        # 数据库密码
        if 'database' in self._config:
            db_password = os.getenv('DB_PASSWORD')
            if db_password:
                self._config['database']['password'] = db_password
            
            # 其他数据库配置
            if os.getenv('DB_HOST'):
                self._config['database']['host'] = os.getenv('DB_HOST')
            if os.getenv('DB_PORT'):
                self._config['database']['port'] = int(os.getenv('DB_PORT'))
            if os.getenv('DB_USER'):
                self._config['database']['user'] = os.getenv('DB_USER')
            if os.getenv('DB_NAME'):
                self._config['database']['database'] = os.getenv('DB_NAME')
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键（如 "database.host"）
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get('database', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})
    
    def get_backtest_config(self) -> Dict[str, Any]:
        """获取回测配置"""
        return self.get('backtest', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.get('api', {})
    
    def get_available_indicators(self) -> list:
        """获取可用指标列表"""
        return self.get('indicators.available', [])
    
    def get_available_timeframes(self) -> list:
        """获取可用时间周期列表"""
        return self.get('timeframes.available', [])


# 创建全局配置实例
config = Config()
