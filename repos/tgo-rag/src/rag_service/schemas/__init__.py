"""
Pydantic schemas for request/response validation.
"""

from .collections import (
    CollectionCreateRequest,
    CollectionDetailResponse,
    CollectionResponse,
    CollectionSearchRequest,
)
from .common import ErrorResponse, PaginationMetadata, PaginationParams
from .documents import DocumentCreateRequest, DocumentResponse
from .files import FileResponse, FileUploadResponse
from .projects import ProjectResponse
from .search import SearchResponse, SearchResult, SearchMetadata

__all__ = [
    # Common schemas
    "ErrorResponse",
    "PaginationMetadata",
    "PaginationParams",
    # Project schemas
    "ProjectResponse",
    # Collection schemas
    "CollectionCreateRequest",
    "CollectionResponse",
    "CollectionDetailResponse",
    "CollectionSearchRequest",
    # File schemas
    "FileResponse",
    "FileUploadResponse",
    # Document schemas
    "DocumentCreateRequest",
    "DocumentResponse",
    # Search schemas
    "SearchResponse",
    "SearchResult",
    "SearchMetadata",
]
