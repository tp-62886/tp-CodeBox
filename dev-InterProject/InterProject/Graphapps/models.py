# knowledgeGraph/models.py
"""
知识图谱数据模型
注意：因为知识图谱主要使用Neo4j图数据库存储，这里的Django模型主要用于存储配置和进度信息
"""
from django.db import models
from django.utils import timezone


class KnowledgeGraphConfig(models.Model):
    """知识图谱配置模型"""
    
    name = models.CharField(max_length=100, unique=True, verbose_name='配置名称')
    neo4j_uri = models.CharField(max_length=200, verbose_name='Neo4j URI')
    neo4j_user = models.CharField(max_length=50, verbose_name='Neo4j 用户名')
    neo4j_password = models.CharField(max_length=100, verbose_name='Neo4j 密码')
    deepseek_api_key = models.CharField(max_length=200, blank=True, null=True, verbose_name='DeepSeek API密钥')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '知识图谱配置'
        verbose_name_plural = '知识图谱配置'
        db_table = 'knowledge_graph_config'
    
    def __str__(self):
        return self.name


class CollectionTask(models.Model):
    """数据采集任务模型"""
    
    TASK_STATUS_CHOICES = [
        ('idle', '空闲'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('error', '错误'),
        ('cancelled', '已取消'),
    ]
    
    COLLECTION_TYPE_CHOICES = [
        ('reset', '重置采集'),
        ('continue', '继续采集'),
        ('incremental', '增量采集'),
    ]
    
    task_id = models.CharField(max_length=50, unique=True, verbose_name='任务ID')
    collection_type = models.CharField(max_length=20, choices=COLLECTION_TYPE_CHOICES, verbose_name='采集类型')
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='idle', verbose_name='任务状态')
    progress = models.FloatField(default=0.0, verbose_name='进度百分比')
    total_batches = models.IntegerField(default=0, verbose_name='总批次数')
    completed_batches = models.IntegerField(default=0, verbose_name='已完成批次数')
    processed_topics = models.TextField(default='[]', verbose_name='已处理主题')  # JSON字符串格式
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '数据采集任务'
        verbose_name_plural = '数据采集任务'
        db_table = 'knowledge_graph_collection_task'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.task_id} - {self.get_status_display()}'
    
    def start_task(self):
        """开始任务"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save()
    
    def complete_task(self):
        """完成任务"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress = 100.0
        self.save()
    
    def fail_task(self, error_message):
        """任务失败"""
        self.status = 'error'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    def update_progress(self, completed_batches, total_batches=None, processed_topics=None):
        """更新进度"""
        self.completed_batches = completed_batches
        if total_batches is not None:
            self.total_batches = total_batches
        if processed_topics is not None:
            self.processed_topics = processed_topics
        
        if self.total_batches > 0:
            self.progress = (self.completed_batches / self.total_batches) * 100
        
        self.save()


class GraphStatistics(models.Model):
    """图谱统计信息模型"""
    
    date = models.DateField(verbose_name='统计日期')
    total_entities = models.IntegerField(default=0, verbose_name='实体总数')
    total_relations = models.IntegerField(default=0, verbose_name='关系总数')
    knowledge_points = models.IntegerField(default=0, verbose_name='知识点数量')
    courses = models.IntegerField(default=0, verbose_name='课程数量')
    entity_types = models.TextField(default='{}', verbose_name='实体类型分布')  # JSON字符串格式
    relation_types = models.TextField(default='{}', verbose_name='关系类型分布')  # JSON字符串格式
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '图谱统计信息'
        verbose_name_plural = '图谱统计信息'
        db_table = 'knowledge_graph_statistics'
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f'{self.date} - 实体:{self.total_entities}, 关系:{self.total_relations}'


class QueryLog(models.Model):
    """查询日志模型"""
    
    QUERY_TYPE_CHOICES = [
        ('search', '搜索查询'),
        ('path', '路径查询'),
        ('related', '相关查询'),
        ('knowledge_points', '知识点查询'),
        ('courses', '课程查询'),
        ('full_graph', '完整图谱查询'),
        ('statistics', '统计查询'),
    ]
    
    query_type = models.CharField(max_length=20, choices=QUERY_TYPE_CHOICES, verbose_name='查询类型')
    query_text = models.TextField(verbose_name='查询内容')
    query_params = models.TextField(default='{}', verbose_name='查询参数')  # JSON字符串格式
    result_count = models.IntegerField(default=0, verbose_name='结果数量')
    execution_time = models.FloatField(default=0.0, verbose_name='执行时间(秒)')
    success = models.BooleanField(default=True, verbose_name='是否成功')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    user_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='用户IP')
    user_agent = models.TextField(blank=True, null=True, verbose_name='用户代理')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='查询时间')
    
    class Meta:
        verbose_name = '查询日志'
        verbose_name_plural = '查询日志'
        db_table = 'knowledge_graph_query_log'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.get_query_type_display()} - {self.created_at.strftime("%Y-%m-%d %H:%M:%S")}'
