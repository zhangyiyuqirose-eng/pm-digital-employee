"""
PM Digital Employee - Database Migration v1.3.0
新增文档解析记录表

Revision ID: 002_document_parse
Revises: 001_initial
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_document_parse'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库：创建document_parse_records表."""
    # 创建document_parse_records表
    op.create_table(
        'document_parse_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, comment='解析记录ID'),

        # 文件信息
        sa.Column('file_key', sa.String(128), nullable=False, comment='飞书文件Key'),
        sa.Column('file_name', sa.String(512), nullable=False, comment='文件名'),
        sa.Column('file_type', sa.String(32), nullable=False, comment='文件类型'),
        sa.Column('file_size', sa.Integer, nullable=False, default=0, comment='文件大小'),
        sa.Column('file_extension', sa.String(16), nullable=False, comment='文件扩展名'),
        sa.Column('storage_path', sa.String(512), nullable=True, comment='本地存储路径'),

        # 分类结果
        sa.Column('document_category', sa.String(32), nullable=True, comment='文档大类'),
        sa.Column('document_subtype', sa.String(64), nullable=True, comment='文档子类型'),
        sa.Column('project_phase', sa.String(32), nullable=True, comment='项目阶段'),
        sa.Column('classification_confidence', sa.Float, nullable=True, comment='分类置信度'),

        # 项目关联
        sa.Column('inferred_project_id', postgresql.UUID(as_uuid=True), nullable=True, comment='推断的项目ID'),
        sa.Column('inferred_project_name', sa.String(256), nullable=True, comment='推断的项目名称'),
        sa.Column('project_match_type', sa.String(32), nullable=True, comment='项目匹配类型'),
        sa.Column('confirmed_project_id', postgresql.UUID(as_uuid=True), nullable=True, comment='确认的项目ID'),

        # 提取结果
        sa.Column('entity_types', sa.Text, nullable=True, comment='可提取实体类型JSON'),
        sa.Column('extracted_data', sa.Text, nullable=True, comment='提取数据JSON'),
        sa.Column('extraction_confidence', sa.Float, nullable=True, comment='提取置信度'),
        sa.Column('field_confidences', sa.Text, nullable=True, comment='字段置信度JSON'),
        sa.Column('missing_fields', sa.Text, nullable=True, comment='缺失字段JSON'),

        # 处理状态
        sa.Column('parse_status', sa.String(32), nullable=False, default='pending', comment='解析状态'),
        sa.Column('import_status', sa.String(32), nullable=False, default='pending', comment='入库状态'),
        sa.Column('imported_entity_ids', sa.Text, nullable=True, comment='已入库实体IDJSON'),
        sa.Column('conflict_ids', sa.Text, nullable=True, comment='冲突记录IDJSON'),

        # 用户确认
        sa.Column('requires_confirmation', sa.Boolean, nullable=False, default=False, comment='是否需要确认'),
        sa.Column('confirmed_by_id', sa.String(64), nullable=True, comment='确认人飞书ID'),
        sa.Column('confirmed_by_name', sa.String(128), nullable=True, comment='确认人姓名'),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True, comment='确认时间'),
        sa.Column('confirmation_action', sa.String(32), nullable=True, comment='确认动作'),

        # 处理元数据
        sa.Column('parser_version', sa.String(16), nullable=False, default='v1.0.0', comment='解析器版本'),
        sa.Column('llm_model', sa.String(64), nullable=True, comment='LLM模型'),
        sa.Column('llm_tokens_input', sa.Integer, nullable=True, comment='LLM输入Token'),
        sa.Column('llm_tokens_output', sa.Integer, nullable=True, comment='LLM输出Token'),
        sa.Column('processing_time_ms', sa.Integer, nullable=True, comment='处理耗时'),

        # 异常信息
        sa.Column('error_type', sa.String(32), nullable=True, comment='错误类型'),
        sa.Column('error_message', sa.Text, nullable=True, comment='错误信息'),
        sa.Column('retry_count', sa.Integer, nullable=False, default=0, comment='重试次数'),

        # 来源信息
        sa.Column('sender_id', sa.String(64), nullable=False, comment='发送者飞书ID'),
        sa.Column('sender_name', sa.String(128), nullable=True, comment='发送者姓名'),
        sa.Column('chat_id', sa.String(64), nullable=False, comment='会话ID'),
        sa.Column('chat_type', sa.String(16), nullable=False, comment='会话类型'),
        sa.Column('message_id', sa.String(64), nullable=False, comment='飞书消息ID'),

        # 时间戳
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),

        # 外键
        sa.ForeignKeyConstraint(['inferred_project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['confirmed_project_id'], ['projects.id'], ondelete='SET NULL'),

        comment='文档解析记录表',
    )

    # 创建索引
    op.create_index('ix_document_parse_records_file_key', 'document_parse_records', ['file_key'])
    op.create_index('ix_document_parse_records_inferred_project_id', 'document_parse_records', ['inferred_project_id'])
    op.create_index('ix_document_parse_records_parse_status', 'document_parse_records', ['parse_status'])
    op.create_index('ix_document_parse_records_sender_id', 'document_parse_records', ['sender_id'])
    op.create_index('ix_document_parse_records_created_at', 'document_parse_records', ['created_at'])
    op.create_index('ix_document_parse_records_requires_confirmation', 'document_parse_records', ['requires_confirmation'])


def downgrade() -> None:
    """降级数据库：删除document_parse_records表."""
    # 删除索引
    op.drop_index('ix_document_parse_records_file_key', 'document_parse_records')
    op.drop_index('ix_document_parse_records_inferred_project_id', 'document_parse_records')
    op.drop_index('ix_document_parse_records_parse_status', 'document_parse_records')
    op.drop_index('ix_document_parse_records_sender_id', 'document_parse_records')
    op.drop_index('ix_document_parse_records_created_at', 'document_parse_records')
    op.drop_index('ix_document_parse_records_requires_confirmation', 'document_parse_records')

    # 删除表
    op.drop_table('document_parse_records')