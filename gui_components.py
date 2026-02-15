"""
GUI Components - Reusable widgets for GeminiFileStoreManager.
Contains custom Tkinter widgets with ttkbootstrap styling.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Dict, List, Optional, Any, Tuple
from pathlib import Path
import threading
from datetime import datetime

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from config import (
    SUPPORTED_EXTENSIONS, METADATA_SCHEMA, CHUNK_DEFAULTS, 
    CHUNK_LIMITS, COLORS
)
from filestore_manager import FileInfo, UploadProgress


class SmartFilePicker(ttkb.Frame):
    """File picker with directory scanning and checkbox tree."""
    
    def __init__(self, parent, on_selection_change: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_selection_change = on_selection_change
        self.selected_files: List[str] = []
        self.file_metadata: Dict[str, Dict] = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the file picker UI."""
        # Toolbar
        toolbar = ttkb.Frame(self)
        toolbar.pack(fill=X, pady=5)
        
        ttkb.Button(
            toolbar, text="Select Folder", 
            command=self._select_folder,
            bootstyle=PRIMARY
        ).pack(side=LEFT, padx=2)
        
        ttkb.Button(
            toolbar, text="Select Files", 
            command=self._select_files,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=2)
        
        ttkb.Button(
            toolbar, text="Clear All", 
            command=self._clear_all,
            bootstyle=DANGER
        ).pack(side=LEFT, padx=2)
        
        # Stats label
        self.stats_label = ttkb.Label(toolbar, text="0 files selected")
        self.stats_label.pack(side=RIGHT, padx=5)
        
        # File tree with scrollbar
        tree_frame = ttkb.Frame(self)
        tree_frame.pack(fill=BOTH, expand=True, pady=5)
        
        # Scrollbars
        vsb = ttkb.Scrollbar(tree_frame, orient=VERTICAL)
        vsb.pack(side=RIGHT, fill=Y)
        
        hsb = ttkb.Scrollbar(tree_frame, orient=HORIZONTAL)
        hsb.pack(side=BOTTOM, fill=X)
        
        # Treeview
        columns = ("name", "size", "type", "path")
        self.tree = ttkb.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="extended"
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Column headings
        self.tree.heading("name", text="File Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("type", text="Type")
        self.tree.heading("path", text="Path")
        
        self.tree.column("name", width=200)
        self.tree.column("size", width=80)
        self.tree.column("type", width=80)
        self.tree.column("path", width=300)
        
        self.tree.pack(fill=BOTH, expand=True)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
    
    def _select_folder(self):
        """Open folder dialog and scan for files."""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self._scan_folder(folder)
    
    def _scan_folder(self, folder: str, recursive: bool = True):
        """Scan folder for supported files."""
        folder_path = Path(folder)
        pattern = "**/*" if recursive else "*"
        
        new_files = []
        for file_path in folder_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                if str(file_path) not in self.selected_files:
                    new_files.append(str(file_path))
        
        self._add_files_to_tree(new_files)
    
    def _select_files(self):
        """Open file dialog for multiple files."""
        files = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[
                ("All Supported", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)),
                ("Text Files", "*.txt *.md"),
                ("Documents", "*.pdf *.doc *.docx"),
                ("Code Files", "*.py *.js *.ts *.java *.cpp *.c *.h"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self._add_files_to_tree(list(files))
    
    def _add_files_to_tree(self, files: List[str]):
        """Add files to the treeview."""
        for file_path in files:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                path_obj = Path(file_path)
                
                size = path_obj.stat().st_size
                size_str = self._format_size(size)
                
                self.tree.insert(
                    "", END,
                    values=(
                        path_obj.name,
                        size_str,
                        path_obj.suffix[1:].upper() if path_obj.suffix else "Unknown",
                        str(path_obj.parent)
                    ),
                    tags=(file_path,)
                )
                
                # Initialize metadata
                self.file_metadata[file_path] = {
                    "file_size_kb": size // 1024,
                    "path_hash": self._compute_hash(file_path),
                }
        
        self._update_stats()
        if self.on_selection_change:
            self.on_selection_change(self.selected_files)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes // 1024} KB"
        else:
            return f"{size_bytes // (1024 * 1024)} MB"
    
    def _compute_hash(self, file_path: str) -> str:
        """Compute simple hash for file path."""
        import hashlib
        return hashlib.sha256(file_path.encode()).hexdigest()[:16]
    
    def _clear_all(self):
        """Clear all selected files."""
        self.selected_files.clear()
        self.file_metadata.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._update_stats()
        if self.on_selection_change:
            self.on_selection_change(self.selected_files)
    
    def _on_select(self, event):
        """Handle tree selection change."""
        pass  # Could add preview functionality here
    
    def _update_stats(self):
        """Update the statistics label."""
        total_size = sum(
            Path(f).stat().st_size for f in self.selected_files if Path(f).exists()
        )
        self.stats_label.config(
            text=f"{len(self.selected_files)} files | {self._format_size(total_size)}"
        )
    
    def get_selected_files(self) -> List[FileInfo]:
        """Get list of FileInfo objects for selected files."""
        return [
            FileInfo(path=f, metadata=self.file_metadata.get(f, {}))
            for f in self.selected_files
        ]
    
    def update_file_metadata(self, file_path: str, metadata: Dict[str, Any]):
        """Update metadata for a specific file."""
        if file_path in self.file_metadata:
            self.file_metadata[file_path].update(metadata)


class MetadataForm(ttkb.Frame):
    """Dynamic metadata form based on schema."""
    
    def __init__(self, parent, schema: Optional[Dict] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.schema = schema or METADATA_SCHEMA
        self.fields: Dict[str, Any] = {}
        self._create_ui()
    
    def _create_ui(self):
        """Create form fields based on schema."""
        row = 0
        for field_name, field_config in self.schema.items():
            self._create_field(row, field_name, field_config)
            row += 1
        
        # Custom JSON editor
        ttkb.Label(self, text="Custom Metadata (JSON):").grid(
            row=row, column=0, sticky=W, pady=5
        )
        row += 1
        
        self.custom_text = ttkb.Text(self, height=4, width=40)
        self.custom_text.grid(row=row, column=0, columnspan=2, sticky=EW, pady=2)
        self.custom_text.insert("1.0", "{}")
    
    def _create_field(self, row: int, name: str, config: Dict):
        """Create a single form field."""
        field_type = config.get("type", "text")
        label = config.get("label", name)
        
        ttkb.Label(self, text=f"{label}:").grid(
            row=row, column=0, sticky=W, padx=5, pady=3
        )
        
        if field_type == "text":
            var = tk.StringVar(value=config.get("default", ""))
            entry = ttkb.Entry(self, textvariable=var, width=30)
            entry.grid(row=row, column=1, sticky=EW, padx=5, pady=3)
            self.fields[name] = var
            
        elif field_type == "dropdown":
            var = tk.StringVar(value=config.get("default", ""))
            combo = ttkb.Combobox(
                self, 
                textvariable=var,
                values=config.get("options", []),
                state="readonly",
                width=28
            )
            combo.grid(row=row, column=1, sticky=EW, padx=5, pady=3)
            self.fields[name] = var
            
        elif field_type == "date":
            var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            entry = ttkb.Entry(self, textvariable=var, width=30)
            entry.grid(row=row, column=1, sticky=EW, padx=5, pady=3)
            self.fields[name] = var
            
        elif field_type == "chips":
            frame = ttkb.Frame(self)
            frame.grid(row=row, column=1, sticky=EW, padx=5, pady=3)
            
            var = tk.StringVar()
            entry = ttkb.Entry(frame, textvariable=var, width=20)
            entry.pack(side=LEFT, padx=2)
            
            chips_frame = ttkb.Frame(frame)
            chips_frame.pack(side=LEFT, padx=5)
            
            tags: List[str] = []
            
            def add_tag():
                tag = var.get().strip()
                if tag and tag not in tags:
                    tags.append(tag)
                    self._refresh_chips(chips_frame, tags)
                    var.set("")
            
            ttkb.Button(
                frame, text="+", command=add_tag,
                bootstyle=SUCCESS, width=3
            ).pack(side=LEFT, padx=2)
            
            self.fields[name] = tags
    
    def _refresh_chips(self, parent, tags: List[str]):
        """Refresh the chips display."""
        for widget in parent.winfo_children():
            widget.destroy()
        
        for tag in tags:
            chip = ttkb.Label(
                parent, text=f"{tag} x",
                bootstyle=INFO,
                padding=(5, 2)
            )
            chip.pack(side=LEFT, padx=2)
            chip.bind("<Button-1>", lambda e, t=tag: self._remove_tag(tags, t, parent))
    
    def _remove_tag(self, tags: List[str], tag: str, parent):
        """Remove a tag."""
        if tag in tags:
            tags.remove(tag)
            self._refresh_chips(parent, tags)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get all metadata values."""
        metadata = {}
        
        for name, field in self.fields.items():
            if isinstance(field, list):
                metadata[name] = field.copy()
            else:
                metadata[name] = field.get()
        
        # Parse custom JSON
        try:
            import json
            custom = json.loads(self.custom_text.get("1.0", END).strip())
            metadata.update(custom)
        except json.JSONDecodeError:
            pass
        
        return metadata
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """Set form values from metadata dict."""
        for name, field in self.fields.items():
            if name in metadata:
                if isinstance(field, list):
                    field.clear()
                    if isinstance(metadata[name], list):
                        field.extend(metadata[name])
                else:
                    field.set(str(metadata[name]))


class ChunkConfigForm(ttkb.Frame):
    """Chunking configuration form with sliders."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_ui()
    
    def _create_ui(self):
        """Create the chunk configuration UI."""
        # Max tokens slider
        frame1 = ttkb.Frame(self)
        frame1.pack(fill=X, pady=5)
        
        ttkb.Label(frame1, text="Max Tokens per Chunk:").pack(side=LEFT)
        self.max_tokens_var = tk.IntVar(value=CHUNK_DEFAULTS["max_tokens"])
        self.max_tokens_label = ttkb.Label(
            frame1, text=str(CHUNK_DEFAULTS["max_tokens"])
        )
        self.max_tokens_label.pack(side=RIGHT)
        
        self.max_tokens_slider = ttkb.Scale(
            self,
            from_=CHUNK_LIMITS["max_tokens"]["min"],
            to=CHUNK_LIMITS["max_tokens"]["max"],
            variable=self.max_tokens_var,
            command=self._update_max_tokens_label,
            bootstyle=PRIMARY
        )
        self.max_tokens_slider.pack(fill=X, pady=2)
        
        # Overlap slider
        frame2 = ttkb.Frame(self)
        frame2.pack(fill=X, pady=5)
        
        ttkb.Label(frame2, text="Overlap Tokens:").pack(side=LEFT)
        self.overlap_var = tk.IntVar(value=CHUNK_DEFAULTS["overlap_tokens"])
        self.overlap_label = ttkb.Label(
            frame2, text=str(CHUNK_DEFAULTS["overlap_tokens"])
        )
        self.overlap_label.pack(side=RIGHT)
        
        self.overlap_slider = ttkb.Scale(
            self,
            from_=CHUNK_LIMITS["overlap_tokens"]["min"],
            to=CHUNK_LIMITS["overlap_tokens"]["max"],
            variable=self.overlap_var,
            command=self._update_overlap_label,
            bootstyle=INFO
        )
        self.overlap_slider.pack(fill=X, pady=2)
        
        # Preview
        preview_frame = ttkb.Labelframe(self, text="Configuration Preview", padding=10)
        preview_frame.pack(fill=X, pady=10)
        
        self.preview_text = ttkb.Label(
            preview_frame, 
            text=self._get_preview_text(),
            justify=LEFT
        )
        self.preview_text.pack(fill=X)
    
    def _update_max_tokens_label(self, value):
        """Update max tokens label."""
        val = int(float(value))
        self.max_tokens_label.config(text=str(val))
        self._update_preview()
    
    def _update_overlap_label(self, value):
        """Update overlap label."""
        val = int(float(value))
        self.overlap_label.config(text=str(val))
        self._update_preview()
    
    def _update_preview(self):
        """Update the preview text."""
        self.preview_text.config(text=self._get_preview_text())
    
    def _get_preview_text(self) -> str:
        """Get preview text for current configuration."""
        max_t = self.max_tokens_var.get()
        overlap = self.overlap_var.get()
        effective = max_t - overlap
        return f"Chunk size: {max_t} tokens | Overlap: {overlap} | Effective: {effective} tokens/chunk"
    
    def get_config(self) -> Dict[str, int]:
        """Get the chunk configuration."""
        return {
            "max_tokens": self.max_tokens_var.get(),
            "overlap_tokens": self.overlap_var.get(),
        }


class ProgressDialog(ttkb.Toplevel):
    """Modal progress dialog for upload operations."""
    
    def __init__(self, parent, title: str = "Progress", on_cancel: Optional[Callable] = None):
        super().__init__(parent)
        self.title(title)
        self.on_cancel = on_cancel
        self.cancelled = False
        
        self.geometry("400x200")
        self.transient(parent)
        self.grab_set()
        
        self._create_ui()
        self.center_on_parent()
    
    def _create_ui(self):
        """Create the progress dialog UI."""
        # Status label
        self.status_label = ttkb.Label(
            self, text="Initializing...", font=("Helvetica", 11)
        )
        self.status_label.pack(pady=10)
        
        # Current file
        self.file_label = ttkb.Label(self, text="", wraplength=350)
        self.file_label.pack(pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttkb.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            bootstyle=SUCCESS,
            length=350
        )
        self.progress_bar.pack(pady=10, padx=20, fill=X)
        
        # Stats
        self.stats_label = ttkb.Label(self, text="0/0 files")
        self.stats_label.pack(pady=5)
        
        # Cancel button
        ttkb.Button(
            self, text="Cancel", 
            command=self._cancel,
            bootstyle=DANGER
        ).pack(pady=10)
    
    def center_on_parent(self):
        """Center the dialog on the parent window."""
        self.update_idletasks()
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def update_progress(self, progress: UploadProgress):
        """Update the progress display."""
        self.progress_var.set(progress.percent)
        self.status_label.config(
            text=f"Uploading... {progress.percent:.1f}%"
        )
        self.file_label.config(text=progress.current_file or "")
        self.stats_label.config(
            text=f"{progress.completed_files}/{progress.total_files} files | "
                 f"Failed: {progress.failed_files}"
        )
        self.update_idletasks()
    
    def _cancel(self):
        """Handle cancel button."""
        self.cancelled = True
        if self.on_cancel:
            self.on_cancel()
        self.destroy()
    
    def complete(self, message: str = "Completed!"):
        """Mark the operation as complete."""
        self.status_label.config(text=message)
        self.progress_var.set(100)
        self.file_label.config(text="")
        self.update_idletasks()
        self.after(1500, self.destroy)


class QueryResultsPanel(ttkb.Frame):
    """Panel for displaying query results with citations."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_ui()
    
    def _create_ui(self):
        """Create the results panel UI."""
        # Response text with scrollbar
        response_frame = ttkb.Labelframe(self, text="Response", padding=5)
        response_frame.pack(fill=BOTH, expand=True, pady=5)
        
        self.response_text = tk.Text(
            response_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=COLORS["dark"],
            fg=COLORS["light"],
            padx=10,
            pady=10
        )
        self.response_text.pack(side=LEFT, fill=BOTH, expand=True)
        
        response_scroll = ttkb.Scrollbar(
            response_frame, orient=VERTICAL, command=self.response_text.yview
        )
        response_scroll.pack(side=RIGHT, fill=Y)
        self.response_text.config(yscrollcommand=response_scroll.set)
        
        # Citations panel
        citations_frame = ttkb.Labelframe(self, text="Citations", padding=5)
        citations_frame.pack(fill=BOTH, expand=True, pady=5)
        
        self.citations_tree = ttkb.Treeview(
            citations_frame,
            columns=("source", "snippet"),
            show="headings"
        )
        self.citations_tree.heading("source", text="Source")
        self.citations_tree.heading("snippet", text="Snippet")
        self.citations_tree.column("source", width=150)
        self.citations_tree.column("snippet", width=400)
        
        citations_scroll = ttkb.Scrollbar(
            citations_frame, orient=VERTICAL, command=self.citations_tree.yview
        )
        self.citations_tree.config(yscrollcommand=citations_scroll.set)
        
        self.citations_tree.pack(side=LEFT, fill=BOTH, expand=True)
        citations_scroll.pack(side=RIGHT, fill=Y)
    
    def set_response(self, text: str, citations: List[Dict] = None):
        """Display the query response."""
        self.response_text.delete("1.0", END)
        self.response_text.insert("1.0", text)
        
        # Clear and populate citations
        for item in self.citations_tree.get_children():
            self.citations_tree.delete(item)
        
        if citations:
            for citation in citations:
                source = citation.get("source", "Unknown")
                snippet = citation.get("text", "")[:100]
                self.citations_tree.insert("", END, values=(source, snippet))
    
    def clear(self):
        """Clear the results panel."""
        self.response_text.delete("1.0", END)
        for item in self.citations_tree.get_children():
            self.citations_tree.delete(item)


class LogPanel(ttkb.Frame):
    """Panel for displaying application logs."""
    
    def __init__(self, parent, max_lines: int = 1000, **kwargs):
        super().__init__(parent, **kwargs)
        self.max_lines = max_lines
        self._create_ui()
    
    def _create_ui(self):
        """Create the log panel UI."""
        # Toolbar
        toolbar = ttkb.Frame(self)
        toolbar.pack(fill=X, pady=2)
        
        ttkb.Button(
            toolbar, text="Clear", 
            command=self.clear,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=2)
        
        ttkb.Button(
            toolbar, text="Copy", 
            command=self._copy_to_clipboard,
            bootstyle=INFO
        ).pack(side=LEFT, padx=2)
        
        # Log text
        self.log_text = tk.Text(
            self,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1a1a1a",
            fg="#00ff00",
            padx=5,
            pady=5,
            height=15
        )
        self.log_text.pack(fill=BOTH, expand=True)
        
        scrollbar = ttkb.Scrollbar(
            self, orient=VERTICAL, command=self.log_text.yview
        )
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Tag configurations for log levels
        self.log_text.tag_config("INFO", foreground="#00ff00")
        self.log_text.tag_config("WARNING", foreground="#ffff00")
        self.log_text.tag_config("ERROR", foreground="#ff0000")
        self.log_text.tag_config("DEBUG", foreground="#00ffff")
    
    def log(self, message: str, level: str = "INFO"):
        """Add a log message."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(END, log_line, level)
        self.log_text.see(END)
        
        # Trim if too long
        lines = int(self.log_text.index(END).split(".")[0])
        if lines > self.max_lines:
            self.log_text.delete("1.0", f"{lines - self.max_lines}.0")
    
    def clear(self):
        """Clear all logs."""
        self.log_text.delete("1.0", END)
    
    def _copy_to_clipboard(self):
        """Copy logs to clipboard."""
        content = self.log_text.get("1.0", END)
        self.clipboard_clear()
        self.clipboard_append(content)
