"""RAG service schemas for proxy endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, PaginationMetadata


# Collection Schemas
class CollectionCreateRequest(BaseSchema):
    """Schema for creating a new collection."""
    
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable collection name",
        examples=["Product Documentation v2.1"]
    )
    description: Optional[str] = Field(
        None,
        description="Optional collection description",
        examples=["Updated product documentation for RAG knowledge base"]
    )
    collection_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Collection metadata (embedding model, chunk size, etc.)",
        examples=[{
            "embedding_model": "text-embedding-ada-002",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "language": "en"
        }]
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Collection tags for categorization and filtering",
        examples=[["documentation", "product", "v2.1"]]
    )


class CollectionUpdateRequest(BaseSchema):
    """Schema for updating an existing collection."""

    display_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Human-readable collection name",
        examples=["Product Documentation v2.2"]
    )
    description: Optional[str] = Field(
        None,
        description="Collection description",
        examples=["Updated product documentation for RAG knowledge base with new features"]
    )
    collection_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Collection metadata (embedding model, chunk size, etc.)",
        examples=[{
            "embedding_model": "text-embedding-ada-002",
            "chunk_size": 1200,
            "chunk_overlap": 250,
            "language": "en"
        }]
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Collection tags for categorization and filtering",
        examples=[["documentation", "product", "v2.2", "updated"]]
    )


class CollectionResponse(BaseSchema):
    """Schema for collection API responses."""
    
    id: str = Field(
        ...,
        description="Collection unique identifier",
        examples=["coll_123e4567-e89b-12d3-a456-426614174000"]
    )
    display_name: str = Field(
        ...,
        description="Human-readable collection name",
        examples=["Product Documentation v2.1"]
    )
    description: Optional[str] = Field(
        None,
        description="Collection description",
        examples=["Updated product documentation for RAG knowledge base"]
    )
    collection_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Collection metadata",
        examples=[{
            "embedding_model": "text-embedding-ada-002",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "language": "en"
        }]
    )
    file_count: Optional[int] = Field(default=0, description="Number of files in collection")
    tags: Optional[List[str]] = Field(
        None,
        description="Collection tags for categorization and filtering",
        examples=[["documentation", "product", "v2.1"]]
    )
    created_at: datetime = Field(
        ...,
        description="Collection creation timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: datetime = Field(
        ...,
        description="Collection last update timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )
    deleted_at: Optional[datetime] = Field(
        None,
        description="Collection deletion timestamp (if soft deleted)"
    )


class CollectionStats(BaseSchema):
    """Schema for collection statistics."""
    
    document_count: int = Field(
        ...,
        ge=0,
        description="Total number of documents in collection",
        examples=[150]
    )
    file_count: int = Field(
        ...,
        ge=0,
        description="Total number of files in collection",
        examples=[25]
    )
    total_tokens: int = Field(
        ...,
        ge=0,
        description="Total tokens across all documents",
        examples=[45000]
    )
    last_updated: Optional[datetime] = Field(
        None,
        description="Last time a document was added/updated",
        examples=["2024-01-15T14:30:00Z"]
    )


class CollectionDetailResponse(CollectionResponse):
    """Schema for detailed collection response with optional statistics."""
    
    stats: Optional[CollectionStats] = Field(
        None,
        description="Collection statistics (when include_stats=true)"
    )


class CollectionListResponse(BaseSchema):
    """Schema for paginated collection list responses."""
    
    data: List[CollectionResponse] = Field(
        ...,
        description="List of collections"
    )
    pagination: PaginationMetadata = Field(
        ...,
        description="Pagination metadata"
    )


# Search Schemas
class CollectionSearchRequest(BaseSchema):
    """Schema for collection-scoped search requests."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query text",
        examples=["How to configure database settings"]
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip for pagination"
    )
    min_score: float = Field(
        default=0,
        ge=0,
        le=1,
        description="Minimum relevance score threshold (0-1)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional filters to apply to search results",
        examples=[{
            "content_type": ["paragraph", "heading"],
            "language": "en",
            "min_confidence": 0.8,
            "tags": {"section": "installation"}
        }]
    )


class SearchResult(BaseSchema):
    """Schema for individual search result."""
    
    id: str = Field(..., description="Document unique identifier")
    content: str = Field(..., description="Document content")
    score: float = Field(..., description="Relevance score (0-1)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")


class SearchResponse(BaseSchema):
    """Schema for search response."""
    
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of matching documents")
    query: str = Field(..., description="Original search query")
    took: float = Field(..., description="Search execution time in seconds")


# File Schemas  
class FileResponse(BaseSchema):
    """Schema for file API responses."""
    
    id: str = Field(..., description="File unique identifier")
    collection_id: Optional[str] = Field(
        None,
        description="Associated collection ID",
        examples=["coll_123e4567-e89b-12d3-a456-426614174000"]
    )
    original_filename: str = Field(
        ...,
        description="Original filename when uploaded",
        examples=["product_manual.pdf"]
    )
    file_size: int = Field(
        ...,
        description="File size in bytes",
        examples=[2048576]
    )
    content_type: str = Field(
        ...,
        description="MIME type of the file",
        examples=["application/pdf"]
    )
    status: str = Field(
        ...,
        description="Processing status",
        examples=["pending", "processing", "completed", "failed", "archived"]
    )
    document_count: int = Field(
        ...,
        description="Number of document chunks generated",
        examples=[25]
    )
    total_tokens: int = Field(
        ...,
        description="Total tokens across all document chunks",
        examples=[5000]
    )
    language: Optional[str] = Field(
        None,
        description="Detected or specified language",
        examples=["en", "es", "fr"]
    )
    description: Optional[str] = Field(
        None,
        description="Optional file description"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="File tags for categorization and filtering",
        examples=[["document", "manual", "pdf"]]
    )
    uploaded_by: Optional[str] = Field(
        None,
        description="User who uploaded the file"
    )
    created_at: datetime = Field(..., description="File upload timestamp")
    updated_at: datetime = Field(..., description="File last update timestamp")


class FileListResponse(BaseSchema):
    """Schema for paginated file list responses."""
    
    data: List[FileResponse] = Field(..., description="List of files")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")


class FileUploadResponse(BaseSchema):
    """Schema for file upload responses."""
    
    id: str = Field(..., description="File unique identifier")
    original_filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Upload status message")


# Batch Upload Schemas
class FileUploadError(BaseSchema):
    """Schema for individual file upload errors."""
    
    filename: str = Field(..., description="Name of the file that failed")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


class BatchUploadSummary(BaseSchema):
    """Schema for batch upload summary statistics."""
    
    total_files: int = Field(..., description="Total number of files in the batch")
    successful_uploads: int = Field(..., description="Number of successfully uploaded files")
    failed_uploads: int = Field(..., description="Number of failed uploads")
    total_size: int = Field(..., description="Total size of all files in bytes")


class BatchFileUploadResponse(BaseSchema):
    """Schema for batch file upload responses."""
    
    summary: BatchUploadSummary = Field(..., description="Batch upload summary statistics")
    successful_uploads: List[FileUploadResponse] = Field(
        ...,
        description="List of successfully uploaded files"
    )
    failed_uploads: List[FileUploadError] = Field(
        ...,
        description="List of failed uploads with error details"
    )
    message: str = Field(
        ...,
        description="Overall batch status message",
        examples=["Batch upload completed: 4 successful, 1 failed"]
    )
