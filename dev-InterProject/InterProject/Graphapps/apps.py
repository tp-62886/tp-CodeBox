# Graphapps/apps.py
"""
知识图谱应用配置
"""
from django.apps import AppConfig


class GraphappsConfig(AppConfig):
    """知识图谱应用配置类"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Graphapps'
    verbose_name = '专业知识图谱自动生成系统'

    def ready(self):
        """应用准备就绪时的初始化操作"""
        import os
        import logging

        logger = logging.getLogger(__name__)

        try:
            # 确保数据目录存在
            base_dir = os.path.dirname(__file__)
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)

            # 确保模板目录存在
            template_dir = os.path.join(base_dir, 'templates')
            os.makedirs(template_dir, exist_ok=True)

            logger.info("知识图谱应用初始化完成")

        except Exception as e:
            logger.error(f"知识图谱应用初始化失败: {str(e)}")
