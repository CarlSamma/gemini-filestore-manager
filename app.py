#!/usr/bin/env python3
"""
GeminiFileStoreManager - Main Application
A desktop GUI for managing Gemini File Search stores.
"""

import json
import logging
import logging.config
import sys
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledText

# Import local modules
from config import (
    APP_NAME, APP_VERSION, APP_MIN_WIDTH, APP_MIN_HEIGHT,
    THEME, THEMES, SHORTCUTS, MAX_CHAT_HISTORY,
    get_env_api_key, save_api_key, load_stores_data, save_stores_data,
    LOGGING_CONFIG, COLORS, FONTS
)
from PIL import Image, ImageDraw
from PIL import ImageTk
import os
from filestore_manager import FileStoreManager, FileInfo, UploadProgress, QueryResult
from gui_components import (
    SmartFilePicker, MetadataForm, ChunkConfigForm,
    ProgressDialog, QueryResultsPanel, LogPanel
)

# Setup logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class GeminiFileStoreApp:
    """Main application class for GeminiFileStoreManager."""
    
    def __init__(self):
        """Initialize the application."""
        self.root = ttkb.Window(themename=THEME)
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(f"{APP_MIN_WIDTH}x{APP_MIN_HEIGHT}")
        self.root.minsize(APP_MIN_WIDTH, APP_MIN_HEIGHT)
        # Apply global background and basic styles to match example.html
        try:
            self.root.configure(bg=COLORS.get("bg", "#0d0d0d"))
            # Configure common ttk styles
            self.root.style.configure('TLabel', background=COLORS.get('bg'), foreground=COLORS.get('fg'), font=FONTS.get('mono'))
            self.root.style.configure('TButton', font=FONTS.get('mono'))
            self.root.style.configure('TLabelframe.Label', font=FONTS.get('heading'), foreground=COLORS.get('accent'))
        except Exception:
            pass

        # Add subtle background text and grain overlay similar to example.html
        try:
            self._ensure_grain_image()
            grain_path = Path(DATA_DIR) / "grain_overlay.png"
            if grain_path.exists():
                img = Image.open(grain_path)
                self._grain_tk = ImageTk.PhotoImage(img)
                grain_label = ttkb.Label(self.root, image=self._grain_tk)
                grain_label.place(relx=0, rely=0, relwidth=1, relheight=1)

            # Background large text
            bg_text = ttkb.Label(self.root, text="RAG NATIVO", font=(FONTS.get('heading', ("Helvetica", 20))[0], 72))
            bg_text.configure(foreground="#ffffff", background=COLORS.get('bg'))
            bg_text.place(relx=0.6, rely=0.55, anchor='center')
            bg_text.lower()
        except Exception:
            pass
        
        # Application state
        self.manager: Optional[FileStoreManager] = None
        self.stores: List[Dict[str, Any]] = []
        self.current_store: Optional[str] = None
        self.chat_history: List[Dict[str, Any]] = []
        self.upload_thread: Optional[threading.Thread] = None
        self.cancel_upload = False
        
        # Load saved data
        self.stores_data = load_stores_data()
        
        # Initialize UI
        self._create_menu()
        self._create_ui()
        self._setup_shortcuts()
        
        # Try to initialize with saved API key
        self._auto_init_api()
    
    def _create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Store", command=self._show_new_store_tab, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Export Stores...", command=self._export_stores)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close, accelerator="Alt+F4")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self._refresh_all, accelerator="F5")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _ensure_grain_image(self):
        """Generate a subtle grain overlay image in the data folder if missing."""
        try:
            out_path = Path(DATA_DIR) / "grain_overlay.png"
            if out_path.exists():
                return

            width, height = 1600, 1200
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            import random
            for _ in range(30000):
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)
                alpha = random.randint(8, 30)
                draw.point((x, y), fill=(196, 164, 124, alpha))

            img = img.resize((int(width * 0.8), int(height * 0.8)))
            out_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(out_path, format="PNG")
        except Exception:
            pass
    
    def _create_ui(self):
        """Create the main UI with notebook tabs."""
        # Main notebook with 5 tabs
        self.notebook = ttkb.Notebook(self.root, bootstyle=PRIMARY)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Dashboard
        self.dashboard_tab = self._create_dashboard_tab()
        self.notebook.add(self.dashboard_tab, text=" Dashboard ")
        
        # Tab 2: New Store
        self.new_store_tab = self._create_new_store_tab()
        self.notebook.add(self.new_store_tab, text=" New Store ")
        
        # Tab 3: Query
        self.query_tab = self._create_query_tab()
        self.notebook.add(self.query_tab, text=" Query ")
        
        # Tab 4: Settings
        self.settings_tab = self._create_settings_tab()
        self.notebook.add(self.settings_tab, text=" Settings ")
        
        # Tab 5: Logs
        self.logs_tab = self._create_logs_tab()
        self.notebook.add(self.logs_tab, text=" Logs ")
        
        # Status bar
        self.status_bar = ttkb.Label(
            self.root, text="Ready", relief=SUNKEN, anchor=W
        )
        self.status_bar.pack(side=BOTTOM, fill=X)
    
    def _create_dashboard_tab(self) -> ttkb.Frame:
        """Create the Dashboard tab."""
        tab = ttkb.Frame(self.notebook)
        
        # Header
        header = ttkb.Frame(tab)
        header.pack(fill=X, pady=10)
        
        ttkb.Label(
            header, text="File Search Stores",
            font=(FONTS.get("heading", ("Helvetica", 12))[0], 16, "bold")
        ).pack(side=LEFT)
        
        ttkb.Button(
            header, text="+ New Store",
            command=self._show_new_store_tab,
            bootstyle=SUCCESS
        ).pack(side=RIGHT, padx=5)
        
        ttkb.Button(
            header, text="Refresh",
            command=self._refresh_stores,
            bootstyle=INFO
        ).pack(side=RIGHT, padx=5)
        
        # Stores treeview
        tree_frame = ttkb.Frame(tab)
        tree_frame.pack(fill=BOTH, expand=True, pady=10)
        
        columns = ("name", "display_name", "file_count", "created", "actions")
        self.stores_tree = ttkb.Treeview(
            tree_frame, columns=columns, show="headings"
        )
        
        self.stores_tree.heading("name", text="Store ID")
        self.stores_tree.heading("display_name", text="Name")
        self.stores_tree.heading("file_count", text="Files")
        self.stores_tree.heading("created", text="Created")
        self.stores_tree.heading("actions", text="Actions")
        
        self.stores_tree.column("name", width=200)
        self.stores_tree.column("display_name", width=150)
        self.stores_tree.column("file_count", width=60)
        self.stores_tree.column("created", width=150)
        self.stores_tree.column("actions", width=100)
        
        # Scrollbar
        scrollbar = ttkb.Scrollbar(
            tree_frame, orient=VERTICAL, command=self.stores_tree.yview
        )
        self.stores_tree.config(yscrollcommand=scrollbar.set)
        
        self.stores_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind double-click
        self.stores_tree.bind("<Double-1>", self._on_store_double_click)
        
        # Context menu
        self._create_stores_context_menu()
        
        return tab
    
    def _create_stores_context_menu(self):
        """Create context menu for stores tree."""
        self.store_menu = tk.Menu(self.root, tearoff=0)
        self.store_menu.add_command(label="Query", command=self._query_selected_store)
        self.store_menu.add_command(label="Delete", command=self._delete_selected_store)
        
        self.stores_tree.bind("<Button-3>", self._show_store_context_menu)
    
    def _show_store_context_menu(self, event):
        """Show context menu on right-click."""
        item = self.stores_tree.identify_row(event.y)
        if item:
            self.stores_tree.selection_set(item)
            self.store_menu.post(event.x_root, event.y_root)
    
    def _create_new_store_tab(self) -> ttkb.Frame:
        """Create the New Store tab."""
        tab = ttkb.Frame(self.notebook)
        
        # Scrollable canvas
        canvas = tk.Canvas(tab, bg=COLORS.get("bg", "#222222"), highlightthickness=0)
        scrollbar = ttkb.Scrollbar(tab, orient=VERTICAL, command=canvas.yview)
        scroll_frame = ttkb.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Store info section
        info_frame = ttkb.Labelframe(
            scroll_frame, text="Store Information", padding=15
        )
        info_frame.pack(fill=X, pady=10, padx=10)
        
        ttkb.Label(info_frame, text="Display Name:").grid(row=0, column=0, sticky=W)
        self.store_name_var = tk.StringVar()
        ttkb.Entry(info_frame, textvariable=self.store_name_var, width=40).grid(
            row=0, column=1, sticky=EW, padx=5
        )
        
        ttkb.Label(info_frame, text="Description:").grid(row=1, column=0, sticky=W, pady=5)
        self.store_desc_var = tk.StringVar()
        ttkb.Entry(info_frame, textvariable=self.store_desc_var, width=40).grid(
            row=1, column=1, sticky=EW, padx=5
        )
        
        # File picker section
        files_frame = ttkb.Labelframe(
            scroll_frame, text="Select Files", padding=15
        )
        files_frame.pack(fill=BOTH, expand=True, pady=10, padx=10)
        
        self.file_picker = SmartFilePicker(files_frame)
        self.file_picker.pack(fill=BOTH, expand=True)
        
        # Metadata section
        meta_frame = ttkb.Labelframe(
            scroll_frame, text="Default Metadata", padding=15
        )
        meta_frame.pack(fill=X, pady=10, padx=10)
        
        self.metadata_form = MetadataForm(meta_frame)
        self.metadata_form.pack(fill=X)
        
        # Chunk config section
        chunk_frame = ttkb.Labelframe(
            scroll_frame, text="Chunking Configuration", padding=15
        )
        chunk_frame.pack(fill=X, pady=10, padx=10)
        
        self.chunk_config = ChunkConfigForm(chunk_frame)
        self.chunk_config.pack(fill=X)
        
        # Create button
        ttkb.Button(
            scroll_frame, text="Create Store & Upload Files",
            command=self._create_store,
            bootstyle=SUCCESS,
            padding=10
        ).pack(pady=20)
        
        return tab
    
    def _create_query_tab(self) -> ttkb.Frame:
        """Create the Query tab."""
        tab = ttkb.Frame(self.notebook)
        
        # Left panel - controls
        left_panel = ttkb.Frame(tab, width=300)
        left_panel.pack(side=LEFT, fill=Y, padx=10, pady=10)
        left_panel.pack_propagate(False)
        
        # Store selector
        store_frame = ttkb.Labelframe(left_panel, text="Select Store", padding=10)
        store_frame.pack(fill=X, pady=5)
        
        self.query_store_var = tk.StringVar()
        self.store_combo = ttkb.Combobox(
            store_frame, textvariable=self.query_store_var,
            state="readonly", width=30
        )
        self.store_combo.pack(fill=X, pady=5)
        
        # Query input
        query_frame = ttkb.Labelframe(left_panel, text="Query", padding=10)
        query_frame.pack(fill=BOTH, expand=True, pady=5)
        
        self.query_text = ScrolledText(query_frame, height=8, width=30)
        self.query_text.pack(fill=BOTH, expand=True, pady=5)
        
        # Metadata filters
        filter_frame = ttkb.Labelframe(left_panel, text="Metadata Filters", padding=10)
        filter_frame.pack(fill=X, pady=5)
        
        self.filter_text = ttkb.Text(filter_frame, height=4, width=30)
        self.filter_text.pack(fill=X)
        self.filter_text.insert("1.0", "{}")
        
        # Submit button
        ttkb.Button(
            left_panel, text="Submit Query",
            command=self._submit_query,
            bootstyle=PRIMARY,
            padding=10
        ).pack(fill=X, pady=10)
        
        # Clear history button
        ttkb.Button(
            left_panel, text="Clear History",
            command=self._clear_chat_history,
            bootstyle=SECONDARY
        ).pack(fill=X)
        
        # Right panel - results
        right_panel = ttkb.Frame(tab)
        right_panel.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        
        self.results_panel = QueryResultsPanel(right_panel)
        self.results_panel.pack(fill=BOTH, expand=True)
        
        return tab
    
    def _create_settings_tab(self) -> ttkb.Frame:
        """Create the Settings tab."""
        tab = ttkb.Frame(self.notebook)
        
        # API Key section
        api_frame = ttkb.Labelframe(tab, text="API Configuration", padding=15)
        api_frame.pack(fill=X, pady=10, padx=20)
        
        ttkb.Label(api_frame, text="Gemini API Key:").grid(row=0, column=0, sticky=W)
        self.api_key_var = tk.StringVar(value=get_env_api_key())
        api_entry = ttkb.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*")
        api_entry.grid(row=0, column=1, sticky=EW, padx=5)
        
        ttkb.Button(
            api_frame, text="Save & Validate",
            command=self._save_api_key,
            bootstyle=SUCCESS
        ).grid(row=0, column=2, padx=5)
        
        # Theme section
        theme_frame = ttkb.Labelframe(tab, text="Appearance", padding=15)
        theme_frame.pack(fill=X, pady=10, padx=20)
        
        ttkb.Label(theme_frame, text="Theme:").grid(row=0, column=0, sticky=W)
        self.theme_var = tk.StringVar(value=THEME)
        theme_combo = ttkb.Combobox(
            theme_frame, textvariable=self.theme_var,
            values=THEMES, state="readonly", width=20
        )
        theme_combo.grid(row=0, column=1, sticky=W, padx=5)
        
        ttkb.Button(
            theme_frame, text="Apply",
            command=self._apply_theme,
            bootstyle=INFO
        ).grid(row=0, column=2, padx=5)
        
        # Default settings
        defaults_frame = ttkb.Labelframe(tab, text="Default Settings", padding=15)
        defaults_frame.pack(fill=X, pady=10, padx=20)
        
        ttkb.Label(defaults_frame, text="Default Chunk Size:").grid(row=0, column=0, sticky=W)
        self.default_chunk_var = tk.IntVar(value=1024)
        ttkb.Spinbox(
            defaults_frame, from_=200, to=2048,
            textvariable=self.default_chunk_var, width=10
        ).grid(row=0, column=1, sticky=W, padx=5)
        
        # Export/Import
        data_frame = ttkb.Labelframe(tab, text="Data Management", padding=15)
        data_frame.pack(fill=X, pady=10, padx=20)
        
        ttkb.Button(
            data_frame, text="Export All Data",
            command=self._export_all_data,
            bootstyle=INFO
        ).pack(side=LEFT, padx=5)
        
        ttkb.Button(
            data_frame, text="Clear Local Cache",
            command=self._clear_cache,
            bootstyle=DANGER
        ).pack(side=LEFT, padx=5)
        
        # Info section
        info_frame = ttkb.Labelframe(tab, text="Application Info", padding=15)
        info_frame.pack(fill=X, pady=10, padx=20)
        
        ttkb.Label(info_frame, text=f"{APP_NAME} v{APP_VERSION}").pack(anchor=W)
        ttkb.Label(info_frame, text="Built with Python, Tkinter, and Gemini API").pack(anchor=W)
        
        return tab
    
    def _create_logs_tab(self) -> ttkb.Frame:
        """Create the Logs tab."""
        tab = ttkb.Frame(self.notebook)
        
        self.log_panel = LogPanel(tab)
        self.log_panel.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        return tab
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.root.bind(SHORTCUTS["new_store"], lambda e: self._show_new_store_tab())
        self.root.bind(SHORTCUTS["refresh"], lambda e: self._refresh_all())
        self.root.bind("<Control-q>", lambda e: self._on_close())
    
    def _auto_init_api(self):
        """Try to initialize API with saved key."""
        api_key = get_env_api_key()
        if api_key:
            self._init_manager(api_key)
    
    def _init_manager(self, api_key: str) -> bool:
        """Initialize the FileStoreManager."""
        try:
            self.manager = FileStoreManager(api_key)
            if self.manager.validate_api_key():
                self._log("API key validated successfully", "INFO")
                self._refresh_stores()
                return True
            else:
                self._log("API key validation failed", "ERROR")
                return False
        except Exception as e:
            self._log(f"Failed to initialize manager: {e}", "ERROR")
            return False
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message to the log panel and logger."""
        logger.log(getattr(logging, level), message)
        if hasattr(self, 'log_panel'):
            self.log_panel.log(message, level)
    
    # === Dashboard Actions ===
    
    def _refresh_stores(self):
        """Refresh the stores list."""
        if not self.manager:
            self._log("API not initialized", "WARNING")
            return
        
        try:
            self.stores = self.manager.list_stores()
            self._update_stores_tree()
            self._update_store_combo()
            self._log(f"Loaded {len(self.stores)} stores", "INFO")
            
            # Save to local cache
            self.stores_data["stores"] = self.stores
            save_stores_data(self.stores_data)
            
        except Exception as e:
            self._log(f"Failed to load stores: {e}", "ERROR")
            # Load from cache
            self.stores = self.stores_data.get("stores", [])
            self._update_stores_tree()
    
    def _update_stores_tree(self):
        """Update the stores treeview."""
        # Clear existing
        for item in self.stores_tree.get_children():
            self.stores_tree.delete(item)
        
        # Add stores
        for store in self.stores:
            self.stores_tree.insert(
                "", END,
                values=(
                    store.get("name", ""),
                    store.get("display_name", ""),
                    store.get("file_count", 0),
                    store.get("create_time", "")[:19]  # Truncate timestamp
                )
            )
    
    def _update_store_combo(self):
        """Update the store selector combobox."""
        store_names = [s.get("display_name", s.get("name", "")) for s in self.stores]
        self.store_combo.config(values=store_names)
    
    def _on_store_double_click(self, event):
        """Handle double-click on a store."""
        self._query_selected_store()
    
    def _query_selected_store(self):
        """Query the selected store."""
        selection = self.stores_tree.selection()
        if not selection:
            return
        
        item = self.stores_tree.item(selection[0])
        store_name = item["values"][0]
        store_display = item["values"][1]
        
        self.query_store_var.set(store_display)
        self.notebook.select(self.query_tab)
    
    def _delete_selected_store(self):
        """Delete the selected store."""
        selection = self.stores_tree.selection()
        if not selection:
            return
        
        item = self.stores_tree.item(selection[0])
        store_name = item["values"][0]
        store_display = item["values"][1]
        
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{store_display}'?\n\nThis action cannot be undone."
        ):
            try:
                if self.manager and self.manager.delete_store(store_name):
                    self._log(f"Deleted store: {store_display}", "INFO")
                    self._refresh_stores()
                else:
                    self._log("Failed to delete store", "ERROR")
            except Exception as e:
                self._log(f"Error deleting store: {e}", "ERROR")
    
    # === New Store Actions ===
    
    def _show_new_store_tab(self):
        """Switch to the New Store tab."""
        self.notebook.select(self.new_store_tab)
    
    def _create_store(self):
        """Create a new store and upload files."""
        if not self.manager:
            messagebox.showerror("Error", "API key not configured. Please set it in Settings.")
            return
        
        store_name = self.store_name_var.get().strip()
        if not store_name:
            messagebox.showerror("Error", "Please enter a store name.")
            return
        
        files = self.file_picker.get_selected_files()
        if not files:
            messagebox.showerror("Error", "Please select at least one file.")
            return
        
        # Get metadata and apply to all files
        default_metadata = self.metadata_form.get_metadata()
        for file_info in files:
            file_info.metadata.update(default_metadata)
        
        # Get chunk config
        chunk_config = self.chunk_config.get_config()
        
        # Create store in background
        def create_and_upload():
            try:
                # Create store
                store_id = self.manager.create_store(
                    store_name, self.store_desc_var.get()
                )
                self._log(f"Created store: {store_id}", "INFO")
                
                # Show progress dialog
                self.root.after(0, lambda: self._show_upload_progress(store_id, files, chunk_config))
                
            except Exception as e:
                self._log(f"Failed to create store: {e}", "ERROR")
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        threading.Thread(target=create_and_upload, daemon=True).start()
    
    def _show_upload_progress(self, store_id: str, files: List[FileInfo], chunk_config: Dict):
        """Show upload progress dialog."""
        dialog = ProgressDialog(self.root, "Uploading Files")
        
        def progress_callback(progress: UploadProgress):
            self.root.after(0, lambda: dialog.update_progress(progress))
        
        def upload():
            try:
                result = self.manager.upload_files(
                    store_id, files, chunk_config, progress_callback
                )
                self.root.after(0, lambda: dialog.complete(
                    f"Upload complete! {result.completed_files}/{result.total_files} files"
                ))
                self.root.after(0, self._refresh_stores)
            except Exception as e:
                self._log(f"Upload failed: {e}", "ERROR")
                self.root.after(0, lambda: messagebox.showerror("Upload Error", str(e)))
        
        threading.Thread(target=upload, daemon=True).start()
    
    # === Query Actions ===
    
    def _submit_query(self):
        """Submit a query to the selected store."""
        if not self.manager:
            messagebox.showerror("Error", "API key not configured.")
            return
        
        store_display = self.query_store_var.get()
        if not store_display:
            messagebox.showerror("Error", "Please select a store.")
            return
        
        query = self.query_text.get("1.0", END).strip()
        if not query:
            messagebox.showerror("Error", "Please enter a query.")
            return
        
        # Find store name from display name
        store_name = None
        for store in self.stores:
            if store.get("display_name") == store_display:
                store_name = store.get("name")
                break
        
        if not store_name:
            messagebox.showerror("Error", "Store not found.")
            return
        
        # Parse filters
        try:
            filters = json.loads(self.filter_text.get("1.0", END).strip())
        except json.JSONDecodeError:
            filters = {}
        
        # Submit query in background
        def do_query():
            try:
                result = self.manager.query_store(store_name, query, filters)
                self.root.after(0, lambda: self._display_query_result(result))
                
                # Add to history
                self.chat_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "response": result.text[:500]  # Truncate for storage
                })
                
                # Trim history
                if len(self.chat_history) > MAX_CHAT_HISTORY:
                    self.chat_history = self.chat_history[-MAX_CHAT_HISTORY:]
                    
            except Exception as e:
                self._log(f"Query failed: {e}", "ERROR")
                self.root.after(0, lambda: messagebox.showerror("Query Error", str(e)))
        
        self.status_bar.config(text="Querying...")
        threading.Thread(target=do_query, daemon=True).start()
    
    def _display_query_result(self, result: QueryResult):
        """Display the query result."""
        self.results_panel.set_response(result.text, result.citations)
        self.status_bar.config(text=f"Query complete. Tokens used: {result.tokens_used}")
    
    def _clear_chat_history(self):
        """Clear the chat history."""
        self.chat_history.clear()
        self.results_panel.clear()
        self.query_text.delete("1.0", END)
    
    # === Settings Actions ===
    
    def _save_api_key(self):
        """Save and validate the API key."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key.")
            return
        
        save_api_key(api_key)
        
        if self._init_manager(api_key):
            messagebox.showinfo("Success", "API key saved and validated!")
        else:
            messagebox.showerror("Error", "Failed to validate API key.")
    
    def _apply_theme(self):
        """Apply the selected theme."""
        new_theme = self.theme_var.get()
        self.root.style.theme_use(new_theme)
        self._log(f"Theme changed to: {new_theme}", "INFO")
    
    def _export_stores(self):
        """Export stores list to file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")]
        )
        if file_path:
            try:
                if file_path.endswith(".json"):
                    with open(file_path, "w") as f:
                        json.dump(self.stores, f, indent=2)
                else:
                    import csv
                    with open(file_path, "w", newline="") as f:
                        if self.stores:
                            writer = csv.DictWriter(f, fieldnames=self.stores[0].keys())
                            writer.writeheader()
                            writer.writerows(self.stores)
                self._log(f"Exported stores to: {file_path}", "INFO")
            except Exception as e:
                self._log(f"Export failed: {e}", "ERROR")
    
    def _export_all_data(self):
        """Export all application data."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                data = {
                    "stores": self.stores,
                    "chat_history": self.chat_history,
                    "export_time": datetime.now().isoformat()
                }
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
                self._log(f"Exported all data to: {file_path}", "INFO")
            except Exception as e:
                self._log(f"Export failed: {e}", "ERROR")
    
    def _clear_cache(self):
        """Clear local cache files."""
        if messagebox.askyesno("Confirm", "Clear all local cache data?"):
            try:
                from config import STORES_FILE
                if STORES_FILE.exists():
                    STORES_FILE.unlink()
                self.stores_data = {"stores": [], "last_updated": ""}
                self._log("Local cache cleared", "INFO")
            except Exception as e:
                self._log(f"Failed to clear cache: {e}", "ERROR")
    
    # === General Actions ===
    
    def _refresh_all(self):
        """Refresh all data."""
        self._refresh_stores()
        self._log("Refreshed all data", "INFO")
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "A desktop application for managing Gemini File Search stores.\n\n"
            "Built with Python, Tkinter, and Google's Gemini API."
        )
    
    def _on_close(self):
        """Handle application close."""
        if self.upload_thread and self.upload_thread.is_alive():
            if not messagebox.askyesno(
                "Confirm Exit",
                "Upload in progress. Are you sure you want to exit?"
            ):
                return
        
        self.root.destroy()
    
    def run(self):
        """Start the application main loop."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()


def main():
    """Main entry point."""
    app = GeminiFileStoreApp()
    app.run()


if __name__ == "__main__":
    main()
