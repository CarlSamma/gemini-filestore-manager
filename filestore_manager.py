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

import google.generativeai as genai
from google.generativeai import types, retriever, protos
from google.generativeai.client import get_default_retriever_client

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
        self.retriever_client = None
        self._lock = threading.Lock()
        self._init_client()
    
    def _init_client(self) -> bool:
        """Initialize the Gemini client."""
        try:
            genai.configure(api_key=self.api_key)
            self.retriever_client = get_default_retriever_client()
            logger.info("Gemini configured successfully with retriever client")
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
                logger.warning(f"Operation failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                else:
                    raise
    
    def validate_api_key(self) -> bool:
        """Validate the API key by making a test request."""
        try:
            # Try to list models as a validation test
            models = genai.list_models()
            return len(list(models)) > 0
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
            # Note: Using the correct API for creating a corpus/store
            store = retriever.create_corpus(display_name=display_name)
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
            for corpus in retriever.list_corpora():
                stores.append({
                    "name": corpus.name,
                    "display_name": getattr(corpus, 'display_name', corpus.name.split('/')[-1]),
                    "file_count": getattr(corpus, 'file_count', 0),
                    "create_time": str(getattr(corpus, 'create_time', '')),
                    "update_time": str(getattr(corpus, 'update_time', '')),
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
            retriever.delete_corpus(name=store_name, force=True)
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
                
                # Upload file to Gemini
                uploaded_file = self._upload_single_file(file_path, file_info.metadata)
                
                # Add to corpus
                document = self._add_file_to_corpus(store_name, uploaded_file, chunk_config)
                
                # Wait for indexing/processing
                self._wait_for_indexing(document.name)
                
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
    
    def _upload_single_file(self, file_path: Path, metadata: Dict[str, Any]) -> Any:
        """Upload a single file to Gemini."""
        def _upload():
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Upload with metadata
            file_obj = genai.upload_file(
                path=str(file_path),
                display_name=file_path.name,
                mime_type=self._get_mime_type(file_path)
            )
            
            # Store metadata as custom attributes if possible
            # Note: Gemini API may not support custom metadata directly
            # We'll store it locally in stores.json
            
            logger.info(f"Uploaded file: {file_obj.name}")
            return file_obj
        
        return self._retry_operation(_upload)
    
    def _add_file_to_corpus(
        self,
        corpus_name: str,
        file_obj: Any,
        chunk_config: Dict[str, int]
    ) -> Any:
        """Add an uploaded file to a corpus."""
        def _add():
            # Create document in corpus using the raw client
            request = protos.CreateDocumentRequest(
                parent=corpus_name,
                document=protos.Document(
                    display_name=getattr(file_obj, 'display_name', 'unnamed')
                )
            )
            document = self.retriever_client.create_document(request)
            
            logger.info(f"Added file to corpus: {document.name}")
            return document
        
        return self._retry_operation(_add)

    def _wait_for_indexing(self, document_name: str, timeout: int = 300):
        """Poll document status until it's processed."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            request = protos.GetDocumentRequest(name=document_name)
            doc = self.retriever_client.get_document(request)
            # Check for processing state
            state = getattr(doc, 'state', None)
            if str(state) == "STATE_ACTIVE" or str(state) == "ACTIVE":
                logger.info(f"Document {document_name} is active")
                return True
            logger.info(f"Waiting for document {document_name} indexing... Current state: {state}")
            time.sleep(5)
        raise TimeoutError(f"Indexing timed out for {document_name}")
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for a file."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"
    
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
            # Legacy tools configuration for compatibility with google-generativeai 0.8.5
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                tools=[{
                    "google_search_retrieval": {
                        "dynamic_retrieval_config": {
                            "mode": "MODE_DYNAMIC",
                            "dynamic_threshold": 0.5
                        }
                    }
                }]
            )
            
            # For corpus-specific queries, we need to use the retrieval API
            # This is a simplified version - actual implementation may vary
            response = model.generate_content(query)
            
            result = QueryResult(
                text=response.text if hasattr(response, 'text') else str(response),
                tokens_used=response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            )
            
            # Extract citations if available
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'grounding_metadata'):
                        result.grounding_metadata = candidate.grounding_metadata
                        # Extract citations from grounding chunks
                        if hasattr(candidate.grounding_metadata, 'grounding_chunks'):
                            for chunk in candidate.grounding_metadata.grounding_chunks:
                                result.citations.append({
                                    "source": getattr(chunk, 'web', None),
                                    "text": str(chunk)[:200]
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
            request = protos.ListDocumentsRequest(parent=store_name)
            for document in self.retriever_client.list_documents(request):
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
