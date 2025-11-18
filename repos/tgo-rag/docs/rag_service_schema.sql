-- =====================================================
-- TGO-TECH RAG SERVICE DATABASE SCHEMA
-- =====================================================
-- Service: RAG Service (Retrieval-Augmented Generation - Document & File Management)
-- Responsibilities: File upload, document processing, content management, vector storage for RAG operations
-- Tables: rag_projects, rag_collections, rag_files, rag_file_documents
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- PROJECT MANAGEMENT TABLES
-- =====================================================

-- Projects table: Local project management
CREATE TABLE rag_projects (
    id UUID PRIMARY KEY COMMENT 'Project UUID',
    name VARCHAR(255) NOT NULL COMMENT 'Project name',
    api_key VARCHAR(255) UNIQUE NOT NULL COMMENT 'API key for authentication',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for rag_projects
CREATE INDEX idx_rag_projects_api_key ON rag_projects(api_key);
CREATE INDEX idx_rag_projects_deleted_at ON rag_projects(deleted_at);

-- Collections table: Document collections for RAG
CREATE TABLE rag_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL COMMENT 'Associated project ID',
    display_name VARCHAR(255) NOT NULL COMMENT 'Human-readable collection name',
    description TEXT COMMENT 'Collection description',
    collection_metadata JSONB COMMENT 'Collection metadata (embedding model, chunk size, etc.)',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT fk_rag_collections_project FOREIGN KEY (project_id) REFERENCES rag_projects(id) ON DELETE CASCADE
);

-- Create indexes for rag_collections
CREATE INDEX idx_rag_collections_project_id ON rag_collections(project_id);
CREATE INDEX idx_rag_collections_display_name ON rag_collections(display_name);
CREATE INDEX idx_rag_collections_created_at ON rag_collections(created_at);
CREATE INDEX idx_rag_collections_deleted_at ON rag_collections(deleted_at);
CREATE INDEX idx_rag_collections_project_display_name ON rag_collections(project_id, display_name);

-- =====================================================
-- FILE AND DOCUMENT MANAGEMENT FOR RAG OPERATIONS
-- =====================================================

-- Files table: Uploaded files for RAG processing
CREATE TABLE rag_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL COMMENT 'Associated project ID',
    collection_id UUID COMMENT 'Associated collection ID',
    original_filename VARCHAR(255) NOT NULL COMMENT 'Original filename when uploaded',
    file_size BIGINT NOT NULL COMMENT 'File size in bytes',
    content_type VARCHAR(100) NOT NULL COMMENT 'MIME content type',
    storage_provider VARCHAR(50) NOT NULL DEFAULT 'local' COMMENT 'Storage provider: local, s3, gcs, azure',
    storage_path VARCHAR(500) NOT NULL COMMENT 'Path to file in storage system',
    storage_metadata JSONB COMMENT 'Storage-specific metadata (bucket, region, etc.)',
    
    -- RAG Processing status and metadata
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'Processing status: pending, processing, completed, failed, archived',
    document_count INTEGER DEFAULT 0 COMMENT 'Number of document chunks created for RAG',
    total_tokens INTEGER DEFAULT 0 COMMENT 'Total tokens extracted for RAG processing',
    language VARCHAR(10) COMMENT 'Detected language code (ISO 639-1)',
    
    -- File metadata
    description TEXT COMMENT 'File description',
    tags JSONB COMMENT 'File tags and metadata for RAG categorization',
    uploaded_by VARCHAR(255) COMMENT 'User who uploaded the file',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT fk_rag_files_project FOREIGN KEY (project_id) REFERENCES rag_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_rag_files_collection FOREIGN KEY (collection_id) REFERENCES rag_collections(id) ON DELETE SET NULL,
    CONSTRAINT chk_rag_files_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'archived')),
    CONSTRAINT chk_rag_files_storage_provider CHECK (storage_provider IN ('local', 's3', 'gcs', 'azure')),
    CONSTRAINT chk_rag_files_file_size CHECK (file_size > 0),
    CONSTRAINT chk_rag_files_document_count CHECK (document_count >= 0),
    CONSTRAINT chk_rag_files_total_tokens CHECK (total_tokens >= 0)
);

-- Create indexes for rag_files
CREATE INDEX idx_rag_files_project_id ON rag_files(project_id);
CREATE INDEX idx_rag_files_collection_id ON rag_files(collection_id);
CREATE INDEX idx_rag_files_status ON rag_files(status);
CREATE INDEX idx_rag_files_content_type ON rag_files(content_type);
CREATE INDEX idx_rag_files_storage_provider ON rag_files(storage_provider);
CREATE INDEX idx_rag_files_uploaded_by ON rag_files(uploaded_by);
CREATE INDEX idx_rag_files_language ON rag_files(language);
CREATE INDEX idx_rag_files_created_at ON rag_files(created_at);
CREATE INDEX idx_rag_files_project_status ON rag_files(project_id, status);
CREATE INDEX idx_rag_files_project_content_type ON rag_files(project_id, content_type);
CREATE INDEX idx_rag_files_project_uploaded_by ON rag_files(project_id, uploaded_by);
CREATE INDEX idx_rag_files_deleted_at ON rag_files(deleted_at);

-- File documents table: Processed document chunks for RAG operations
CREATE TABLE rag_file_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL COMMENT 'Associated file ID',
    collection_id UUID COMMENT 'Associated collection ID',
    document_id VARCHAR(100) NOT NULL COMMENT 'Unique document identifier within the file',
    collection_name VARCHAR(255) NOT NULL COMMENT 'Collection name for grouping related documents',
    
    -- Document content and metadata for RAG
    document_title VARCHAR(500) COMMENT 'Document title or heading',
    content TEXT NOT NULL COMMENT 'Document content text for RAG processing',
    content_length INTEGER NOT NULL COMMENT 'Length of content in characters',
    token_count INTEGER COMMENT 'Number of tokens in the content',
    chunk_index INTEGER COMMENT 'Index of this chunk within the document',
    
    -- Document structure and context
    section_title VARCHAR(255) COMMENT 'Section or chapter title',
    page_number INTEGER COMMENT 'Page number in original document',
    content_type VARCHAR(50) DEFAULT 'paragraph' COMMENT 'Type of content: paragraph, heading, table, list, code, image, metadata',
    
    -- RAG processing metadata
    language VARCHAR(10) COMMENT 'Document language (ISO 639-1)',
    confidence_score DECIMAL(5,4) COMMENT 'Confidence score for content extraction (0.0-1.0)',
    tags JSONB COMMENT 'Document tags and metadata for RAG categorization',
    
    -- Vector embeddings (stored separately in vector database)
    embedding_model VARCHAR(100) COMMENT 'Model used for generating embeddings',
    embedding_dimensions INTEGER COMMENT 'Dimensions of the embedding vector',
    vector_id VARCHAR(255) COMMENT 'Reference to vector in vector database',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rag_file_documents_file FOREIGN KEY (file_id) REFERENCES rag_files(id) ON DELETE CASCADE,
    CONSTRAINT fk_rag_file_documents_collection FOREIGN KEY (collection_id) REFERENCES rag_collections(id) ON DELETE SET NULL,
    CONSTRAINT uk_rag_file_documents_file_document UNIQUE (file_id, document_id),
    CONSTRAINT chk_rag_file_documents_content_type CHECK (content_type IN ('paragraph', 'heading', 'table', 'list', 'code', 'image', 'metadata')),
    CONSTRAINT chk_rag_file_documents_content_length CHECK (content_length > 0),
    CONSTRAINT chk_rag_file_documents_token_count CHECK (token_count IS NULL OR token_count > 0),
    CONSTRAINT chk_rag_file_documents_chunk_index CHECK (chunk_index IS NULL OR chunk_index >= 0),
    CONSTRAINT chk_rag_file_documents_page_number CHECK (page_number IS NULL OR page_number > 0),
    CONSTRAINT chk_rag_file_documents_confidence_score CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    CONSTRAINT chk_rag_file_documents_embedding_dimensions CHECK (embedding_dimensions IS NULL OR embedding_dimensions > 0)
);

-- Create indexes for rag_file_documents
CREATE INDEX idx_rag_file_documents_file_id ON rag_file_documents(file_id);
CREATE INDEX idx_rag_file_documents_collection_id ON rag_file_documents(collection_id);
CREATE INDEX idx_rag_file_documents_document_id ON rag_file_documents(document_id);
CREATE INDEX idx_rag_file_documents_collection_name ON rag_file_documents(collection_name);
CREATE INDEX idx_rag_file_documents_content_type ON rag_file_documents(content_type);
CREATE INDEX idx_rag_file_documents_language ON rag_file_documents(language);
CREATE INDEX idx_rag_file_documents_chunk_index ON rag_file_documents(chunk_index);
CREATE INDEX idx_rag_file_documents_page_number ON rag_file_documents(page_number);
CREATE INDEX idx_rag_file_documents_token_count ON rag_file_documents(token_count);
CREATE INDEX idx_rag_file_documents_confidence_score ON rag_file_documents(confidence_score);
CREATE INDEX idx_rag_file_documents_embedding_model ON rag_file_documents(embedding_model);
CREATE INDEX idx_rag_file_documents_vector_id ON rag_file_documents(vector_id);
CREATE INDEX idx_rag_file_documents_created_at ON rag_file_documents(created_at);
CREATE INDEX idx_rag_file_documents_file_collection ON rag_file_documents(file_id, collection_name);
CREATE INDEX idx_rag_file_documents_collection_content_type ON rag_file_documents(collection_name, content_type);
CREATE INDEX idx_rag_file_documents_collection_language ON rag_file_documents(collection_name, language);
CREATE INDEX idx_rag_file_documents_file_chunk ON rag_file_documents(file_id, chunk_index);
CREATE INDEX idx_rag_file_documents_search_optimization ON rag_file_documents(collection_name, content_type, language, confidence_score);

-- =====================================================
-- END OF RAG SERVICE SCHEMA
-- =====================================================
