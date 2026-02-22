"""
FileStoreManager - Gemini API wrapper for file search stores.
Handles store creation, file upload, querying, and management.
"""

import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading

from google import genai
from google.genai import types

from config import GEMINI_MODEL, API_TIMEOUT, MAX_RETRIES, RETRY_DELAY, MAX_FILE_SIZE

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Represents a file to be uploaded with metadata."""
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_kb: int = 0
    status: str = "pending"  # pending, uploading, completed, error
    error_msg: str = ""
    
    def __post_init__(self):
        if not self.size_kb:
            try:
                self.size_kb = Path(self.path).stat().st_size // 1024
            except OSError:
                self.size_kb = 0


@dataclass
class UploadProgress:
    """Tracks upload progress for a batch of files."""
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    current_file: str = ""
    total_tokens: int = 0
    is_cancelled: bool = False
    
    @property
    def percent(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100


@dataclass
class QueryResult:
    """Represents a query response with citations."""
    text: str = ""
    citations: List[Dict[str, Any]] = field(default_factory=list)
    grounding_metadata: Optional[Any] = None
    tokens_used: int = 0


class FileStoreManager:
    """
    Manager for Gemini File Search stores.
    Wraps the Gemini API for store operations.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the FileStoreManager.
        
        Args:
            api_key: Gemini API key
        """
        self.api_key = api_key
        self.client = None
        self._lock = threading.Lock()
        self._init_client()
    
    def _init_client(self) -> bool:
        """Initialize the Gemini client."""
        try:
            self.client = genai.Client(
                api_key=self.api_key,
                http_options={'api_version': 'v1beta'}
            )
            logger.info("Gemini configured successfully with modern genai client (v1beta)")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}")
            return False
    
    def _retry_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute an operation with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                # Catch genai specific errors if necessary, but broad check for now
                logger.warning(f"Operation failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                else:
                    raise
    
    def validate_api_key(self) -> bool:
        """Validate the API key by making a test request."""
        try:
            # Try to list models as a validation test
            models = self.client.models.list()
            return next(models, None) is not None
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    def create_store(self, display_name: str, description: str = "") -> str:
        """
        Create a new file search store.
        
        Args:
            display_name: Human-readable name for the store
            description: Optional description
            
        Returns:
            Store name (ID)
        """
        def _create():
            store = self.client.file_search_stores.create(
                config={'display_name': display_name}
            )
            logger.info(f"Created store: {store.name}")
            return store.name
        
        return self._retry_operation(_create)
    
    def list_stores(self) -> List[Dict[str, Any]]:
        """
        List all file search stores.
        
        Returns:
            List of store dictionaries with name, display_name, file_count, etc.
        """
        def _list():
            stores = []
            for store in self.client.file_search_stores.list():
                stores.append({
                    "name": store.name,
                    "display_name": getattr(store, 'display_name', store.name.split('/')[-1]),
                    "file_count": getattr(store, 'file_count', 0),
                    "create_time": str(getattr(store, 'create_time', '')),
                    "update_time": str(getattr(store, 'update_time', '')),
                })
            return stores
        
        return self._retry_operation(_list)
    
    def delete_store(self, store_name: str) -> bool:
        """
        Delete a file search store.
        
        Args:
            store_name: Full store name/ID
            
        Returns:
            True if successful
        """
        def _delete():
            self.client.file_search_stores.delete(name=store_name, config={'force': True})
            logger.info(f"Deleted store: {store_name}")
            return True
        
        try:
            return self._retry_operation(_delete)
        except Exception as e:
            logger.error(f"Failed to delete store {store_name}: {e}")
            return False
    
    def upload_files(
        self,
        store_name: str,
        files: List[FileInfo],
        chunk_config: Optional[Dict[str, int]] = None,
        progress_callback: Optional[Callable[[UploadProgress], None]] = None
    ) -> UploadProgress:
        """
        Upload files to a store.
        
        Args:
            store_name: Target store name
            files: List of FileInfo objects
            chunk_config: Optional chunking configuration
            progress_callback: Callback for progress updates
            
        Returns:
            Final UploadProgress object
        """
        progress = UploadProgress(total_files=len(files))
        chunk_config = chunk_config or {}
        
        for file_info in files:
            if progress_callback:
                progress_callback(progress)
            
            try:
                progress.current_file = Path(file_info.path).name
                file_info.status = "uploading"
                
                # Check file size
                file_path = Path(file_info.path)
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE // 1024 // 1024}MB")
                
                # Upload file to Gemini File Search Store directly
                # This handles both file upload and adding to store
                operation = self.client.file_search_stores.upload_to_file_search_store(
                    file=str(file_path),
                    file_search_store_name=store_name,
                    config={
                        'display_name': file_path.name,
                    }
                )
                
                # Wait for operation to complete
                while not operation.done:
                    time.sleep(2)
                    operation = self.client.operations.get(operation)
                
                if operation.error:
                    raise Exception(f"Operation failed: {operation.error}")
                
                # Retrieve document name from response or metadata
                document_name = None
                if hasattr(operation, 'response') and operation.response:
                    document_name = getattr(operation.response, 'name', None)
                
                if not document_name and hasattr(operation, 'metadata') and operation.metadata:
                    # Check both attribute and dictionary access for robustness
                    document_name = getattr(operation.metadata, 'document_name', None) or \
                                   (operation.metadata.get('document_name') if isinstance(operation.metadata, dict) else None) or \
                                   getattr(operation.metadata, 'name', None) or \
                                   (operation.metadata.get('name') if isinstance(operation.metadata, dict) else None)
                
                if not document_name:
                    logger.warning(f"Could not retrieve document name for {file_path.name}, skipping indexing wait")
                else:
                    logger.info(f"Uploaded and added file to store: {document_name}")
                    # Wait for indexing/processing
                    self._wait_for_indexing(document_name)
                
                file_info.status = "completed"
                progress.completed_files += 1
                progress.total_tokens += file_info.size_kb  # Approximation
                
            except Exception as e:
                logger.error(f"Failed to upload {file_info.path}: {e}")
                file_info.status = "error"
                file_info.error_msg = str(e)
                progress.failed_files += 1
        
        progress.current_file = ""
        if progress_callback:
            progress_callback(progress)
        
        return progress
    
    def _wait_for_indexing(self, document_name: str, timeout: int = 300):
        """Poll document status until it's processed."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            doc = self.client.file_search_stores.documents.get(name=document_name)
            # Check for processing state
            state = getattr(doc, 'state', None)
            if str(state) == "STATE_ACTIVE" or str(state) == "ACTIVE":
                logger.info(f"Document {document_name} is active")
                return True
            logger.info(f"Waiting for document {document_name} indexing... Current state: {state}")
            time.sleep(5)
        raise TimeoutError(f"Indexing timed out for {document_name}")
    
    def query_store(
        self,
        store_name: str,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        Query a store with optional metadata filters.
        
        Args:
            store_name: Store to query
            query: Query text
            metadata_filter: Optional metadata filters
            
        Returns:
            QueryResult with response and citations
        """
        def _query():
            # Use the modern generate_content with FileSearch tool
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[store_name]
                            )
                        )
                    ]
                )
            )
            
            result = QueryResult(
                text=response.text,
                tokens_used=getattr(response.usage_metadata, 'total_token_count', 0)
            )
            
            # Extract citations from grounding metadata
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    result.grounding_metadata = candidate.grounding_metadata
                    # Handle grounding chunks/citations
                    if hasattr(candidate.grounding_metadata, 'grounding_chunks'):
                        for chunk in candidate.grounding_metadata.grounding_chunks:
                            # In modern SDK, citations are often in grounding_chunks or search_entry_point
                            citation_text = ""
                            if hasattr(chunk, 'web'):
                                citation_text = f"Source: {chunk.web.title} ({chunk.web.uri})"
                            
                            result.citations.append({
                                "source": citation_text,
                                "text": ""
                            })
            
            return result
        
        return self._retry_operation(_query)
    
    def get_store_files(self, store_name: str) -> List[Dict[str, Any]]:
        """
        Get list of files in a store.
        
        Args:
            store_name: Store name
            
        Returns:
            List of file dictionaries
        """
        def _list_files():
            files = []
            for document in self.client.file_search_stores.documents.list(parent=store_name):
                files.append({
                    "name": document.name,
                    "display_name": getattr(document, 'display_name', 'unnamed'),
                    "create_time": str(getattr(document, 'create_time', '')),
                })
            return files
        
        return self._retry_operation(_list_files)
    
    @staticmethod
    def compute_path_hash(file_path: str) -> str:
        """Compute SHA256 hash of a file path for deduplication."""
        return hashlib.sha256(file_path.encode()).hexdigest()[:16]
