# GeminiFileStoreManager

A modern desktop application for managing Gemini File Search stores with a native Tkinter GUI.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Gemini](https://img.shields.io/badge/Gemini-API-orange.svg)

## Features

- **Store Management**: Create, list, and delete Gemini File Search stores
- **File Upload**: Bulk upload files with progress tracking and metadata
- **Query Interface**: Search stores with metadata filters and view citations
- **Dark Theme**: Optimized for legal document reading with ttkbootstrap darkly theme
- **Offline Cache**: Local storage of store metadata for offline viewing
- **Keyboard Shortcuts**: Ctrl+N (New Store), F5 (Refresh), Ctrl+Q (Query)

## Screenshots

*Dashboard showing store list with statistics*

*File picker with folder scanning and metadata editor*

*Query interface with response and citations panel*

## Installation

### Prerequisites

- Python 3.11 or higher
- Gemini API key (get one at [Google AI Studio](https://makersuite.google.com/app/apikey))

### Quick Start

```bash
# Clone or download the repository
cd gemini_filestore_app

# Install dependencies
pip install -r requirements.txt

# Set your API key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Run the application
python app.py
```

### Requirements

```
google-generativeai>=0.8.0
ttkbootstrap>=1.10.0
python-dotenv>=1.0.0
watchdog>=3.0.0
Pillow>=10.0.0
```

## Usage

### 1. Configure API Key

On first launch, go to **Settings** tab and enter your Gemini API key. The key is saved to `.env` file for future sessions.

### 2. Create a Store

1. Click **New Store** tab
2. Enter store name and optional description
3. Select files or folders to upload
4. Configure default metadata (practice, doc_type, tags, date, client)
5. Adjust chunking settings if needed
6. Click **Create Store & Upload Files**

### 3. Query a Store

1. Go to **Query** tab
2. Select a store from the dropdown
3. Enter your query
4. Optionally add metadata filters (JSON format)
5. Click **Submit Query**
6. View response and citations in the results panel

### 4. Manage Stores

- **Dashboard**: View all stores with file counts
- Right-click a store for context menu (Query, Delete)
- Double-click to quickly query a store

## File Structure

```
gemini_filestore_app/
├── app.py                 # Main GUI application
├── filestore_manager.py   # Gemini API wrapper
├── gui_components.py      # Reusable UI widgets
├── config.py              # App settings and defaults
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── stores.json           # Local store metadata cache
└── .env                  # API key storage
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Store |
| `F5` | Refresh Stores |
| `Ctrl+Q` | Query (when in query tab) |
| `Ctrl+,` | Settings |
| `Alt+F4` | Exit |

## Metadata Schema

Default metadata fields for uploaded files:

```json
{
  "practice": "Condominio Milano",
  "doc_type": "Contratto",
  "tags": ["MiCA", "GDPR", "Locazione"],
  "date": "2026-02-15",
  "client": "Studio Legale X",
  "file_size_kb": 245,
  "path_hash": "sha256_of_path"
}
```

## Chunking Configuration

- **Max Tokens**: 200-2048 (default: 1024)
- **Overlap Tokens**: 0-512 (default: 100)

Adjust based on your document types and query needs.

## Building Executable

To create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name GeminiFileStoreManager app.py

# Or use the provided spec file
pyinstaller GeminiFileStoreManager.spec
```

## Troubleshooting

### API Key Issues

- Verify your API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Check that `.env` file exists with correct format: `GEMINI_API_KEY=your_key`

### Upload Failures

- Maximum file size: 100MB per file
- Maximum total size: 1GB per store
- Supported formats: TXT, MD, PDF, DOC, DOCX, CSV, JSON, XML, HTML, and code files

### Rate Limiting

The app includes exponential backoff retry logic. If you hit rate limits:
- Wait a few minutes between large uploads
- Reduce chunk size for faster processing
- Check [Gemini API quotas](https://ai.google.dev/docs/quota)

## Development

### Running Tests

```bash
# Unit tests for FileStoreManager
python -m pytest tests/
```

### Code Style

```bash
# Format with black
black *.py

# Lint with pylint
pylint *.py
```

## License

MIT License - See LICENSE file for details.

## Changelog

### v1.0.0
- Initial release
- Store CRUD operations
- File upload with progress
- Query interface with citations
- Dark theme UI
- Local cache support

## Support

For issues and feature requests, please open an issue on GitHub.

---

Built with Python, Tkinter, and Google's Gemini API.
