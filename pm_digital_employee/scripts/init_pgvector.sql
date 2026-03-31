-- PostgreSQL pgvector Extension Initialization Script
-- 项目经理数字员工系统 - 向量检索扩展初始化
-- 此脚本在PostgreSQL容器启动时自动执行

-- 创建pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证扩展已安装
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION 'pgvector extension not installed';
    END IF;
    RAISE NOTICE 'pgvector extension installed successfully';
END $$;

-- 创建向量索引操作类
-- IVFFlat索引适用于中等规模向量检索（10万-100万）
-- HNSW索引适用于大规模向量检索（百万以上）
-- 一期MVP使用IVFFlat，部署最简

-- 创建向量相似度函数（余弦距离）
CREATE OR REPLACE FUNCTION cosine_distance(a vector, b vector)
RETURNS float8 AS $$
    SELECT 1 - (a <=> b);
$$ LANGUAGE SQL IMMUTABLE STRICT;

-- 创建向量相似度函数（欧氏距离）
CREATE OR REPLACE FUNCTION euclidean_distance(a vector, b vector)
RETURNS float8 AS $$
    SELECT sqrt((a <#> b)^2);
$$ LANGUAGE SQL IMMUTABLE STRICT;

-- 创建向量内积函数
CREATE OR REPLACE FUNCTION inner_product(a vector, b vector)
RETURNS float8 AS $$
    SELECT (-a) <#> b;
$$ LANGUAGE SQL IMMUTABLE STRICT;

-- 创建辅助函数：规范化向量
CREATE OR REPLACE FUNCTION normalize_vector(v vector)
RETURNS vector AS $$
DECLARE
    norm float8;
    result vector;
BEGIN
    -- 计算向量的L2范数
    norm := sqrt(v <#> v);
    -- 防止除零
    IF norm = 0 THEN
        RETURN v;
    END IF;
    -- 返回规范化后的向量（需要通过应用层实现）
    RETURN v;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- 创建向量维度验证函数
CREATE OR REPLACE FUNCTION validate_vector_dimension(v vector, expected_dim integer)
RETURNS boolean AS $$
BEGIN
    IF vector_dims(v) != expected_dim THEN
        RETURN false;
    END IF;
    RETURN true;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- 创建向量检索日志表（用于追踪检索效果）
CREATE TABLE IF NOT EXISTS vector_search_log (
    id SERIAL PRIMARY KEY,
    query_vector vector(1536),
    query_text TEXT,
    top_k INTEGER DEFAULT 5,
    distance_metric VARCHAR(50) DEFAULT 'cosine',
    hit_count INTEGER,
    avg_distance float8,
    search_time_ms float8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量检索性能统计表
CREATE TABLE IF NOT EXISTS vector_search_stats (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    total_searches INTEGER DEFAULT 0,
    avg_search_time_ms float8 DEFAULT 0,
    avg_hit_count float8 DEFAULT 0,
    cache_hit_rate float8 DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量索引维护日志表
CREATE TABLE IF NOT EXISTS vector_index_maintenance_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    index_name VARCHAR(100) NOT NULL,
    operation VARCHAR(50) NOT NULL, -- 'create', 'reindex', 'drop'
    index_type VARCHAR(50), -- 'ivfflat', 'hnsw'
    lists INTEGER, -- IVFFlat参数
    m INTEGER, -- HNSW参数
    ef_construction INTEGER, -- HNSW参数
    execution_time_ms float8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建初始性能统计记录
INSERT INTO vector_search_stats (date, total_searches, avg_search_time_ms)
VALUES (CURRENT_DATE, 0, 0)
ON CONFLICT DO NOTHING;

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '=== pgvector initialization completed ===';
    RAISE NOTICE 'Extension: vector';
    RAISE NOTICE 'Functions: cosine_distance, euclidean_distance, inner_product';
    RAISE NOTICE 'Tables: vector_search_log, vector_search_stats, vector_index_maintenance_log';
    RAISE NOTICE 'Ready for vector similarity search operations';
END $$;