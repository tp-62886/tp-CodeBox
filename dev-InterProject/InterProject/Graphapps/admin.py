# knowledgeGraph/admin.py
"""
知识图谱Django管理界面
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import KnowledgeGraphConfig, CollectionTask, GraphStatistics, QueryLog


@admin.register(KnowledgeGraphConfig)
class KnowledgeGraphConfigAdmin(admin.ModelAdmin):
    """知识图谱配置管理"""
    
    list_display = ['name', 'neo4j_uri', 'neo4j_user', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'neo4j_uri', 'neo4j_user']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'is_active')
        }),
        ('Neo4j配置', {
            'fields': ('neo4j_uri', 'neo4j_user', 'neo4j_password')
        }),
        ('API配置', {
            'fields': ('deepseek_api_key',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """保存模型时的处理"""
        super().save_model(request, obj, form, change)
        
        # 如果设置为激活，将其他配置设为非激活
        if obj.is_active:
            KnowledgeGraphConfig.objects.exclude(pk=obj.pk).update(is_active=False)


@admin.register(CollectionTask)
class CollectionTaskAdmin(admin.ModelAdmin):
    """数据采集任务管理"""
    
    list_display = ['task_id', 'collection_type', 'status_colored', 'progress_bar', 'completed_batches', 'total_batches', 'started_at', 'completed_at']
    list_filter = ['status', 'collection_type', 'created_at']
    search_fields = ['task_id', 'error_message']
    readonly_fields = ['task_id', 'progress_bar', 'processed_topics_display', 'created_at', 'updated_at']
    
    fieldsets = (
        ('任务信息', {
            'fields': ('task_id', 'collection_type', 'status')
        }),
        ('进度信息', {
            'fields': ('progress_bar', 'total_batches', 'completed_batches', 'processed_topics_display')
        }),
        ('时间信息', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
        ('错误信息', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def status_colored(self, obj):
        """带颜色的状态显示"""
        colors = {
            'idle': 'gray',
            'running': 'blue',
            'completed': 'green',
            'error': 'red',
            'cancelled': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = '状态'
    
    def progress_bar(self, obj):
        """进度条显示"""
        if obj.progress > 0:
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
                '<div style="width: {}%; background-color: #007cba; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
                '{}%'
                '</div></div>',
                obj.progress,
                round(obj.progress, 1)
            )
        return '-'
    progress_bar.short_description = '进度'
    
    def processed_topics_display(self, obj):
        """已处理主题显示"""
        if obj.processed_topics:
            topics = obj.processed_topics[:10]  # 只显示前10个
            topics_str = ', '.join(topics)
            if len(obj.processed_topics) > 10:
                topics_str += f' ... (共{len(obj.processed_topics)}个)'
            return topics_str
        return '-'
    processed_topics_display.short_description = '已处理主题'
    
    def has_add_permission(self, request):
        """禁止手动添加任务"""
        return False


@admin.register(GraphStatistics)
class GraphStatisticsAdmin(admin.ModelAdmin):
    """图谱统计信息管理"""
    
    list_display = ['date', 'total_entities', 'total_relations', 'knowledge_points', 'courses', 'created_at']
    list_filter = ['date', 'created_at']
    readonly_fields = ['entity_types_display', 'relation_types_display', 'created_at']
    
    fieldsets = (
        ('统计日期', {
            'fields': ('date',)
        }),
        ('数量统计', {
            'fields': ('total_entities', 'total_relations', 'knowledge_points', 'courses')
        }),
        ('类型分布', {
            'fields': ('entity_types_display', 'relation_types_display'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def entity_types_display(self, obj):
        """实体类型分布显示"""
        if obj.entity_types:
            html = '<table style="width: 100%;">'
            for entity_type, count in obj.entity_types.items():
                html += f'<tr><td>{entity_type}</td><td>{count}</td></tr>'
            html += '</table>'
            return mark_safe(html)
        return '-'
    entity_types_display.short_description = '实体类型分布'
    
    def relation_types_display(self, obj):
        """关系类型分布显示"""
        if obj.relation_types:
            html = '<table style="width: 100%;">'
            for relation_type, count in obj.relation_types.items():
                html += f'<tr><td>{relation_type}</td><td>{count}</td></tr>'
            html += '</table>'
            return mark_safe(html)
        return '-'
    relation_types_display.short_description = '关系类型分布'


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    """查询日志管理"""
    
    list_display = ['query_type', 'query_text_short', 'result_count', 'execution_time', 'success_colored', 'user_ip', 'created_at']
    list_filter = ['query_type', 'success', 'created_at']
    search_fields = ['query_text', 'user_ip', 'error_message']
    readonly_fields = ['query_params_display', 'created_at']
    
    fieldsets = (
        ('查询信息', {
            'fields': ('query_type', 'query_text', 'query_params_display')
        }),
        ('执行结果', {
            'fields': ('result_count', 'execution_time', 'success', 'error_message')
        }),
        ('用户信息', {
            'fields': ('user_ip', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def query_text_short(self, obj):
        """查询内容简短显示"""
        if len(obj.query_text) > 50:
            return obj.query_text[:50] + '...'
        return obj.query_text
    query_text_short.short_description = '查询内容'
    
    def success_colored(self, obj):
        """带颜色的成功状态显示"""
        if obj.success:
            return format_html('<span style="color: green;">成功</span>')
        else:
            return format_html('<span style="color: red;">失败</span>')
    success_colored.short_description = '执行状态'
    
    def query_params_display(self, obj):
        """查询参数显示"""
        if obj.query_params:
            return mark_safe(f'<pre>{json.dumps(obj.query_params, indent=2, ensure_ascii=False)}</pre>')
        return '-'
    query_params_display.short_description = '查询参数'
    
    def has_add_permission(self, request):
        """禁止手动添加日志"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """禁止修改日志"""
        return False
