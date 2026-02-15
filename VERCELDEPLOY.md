# Vercel Deployment Guide - GeminiFileStoreManager

## ⚠️ Important Notice

**This application is currently a desktop GUI application built with Tkinter**, which **cannot be directly deployed to Vercel**. Vercel is a platform for deploying web applications (static sites, serverless functions, and web frameworks like Next.js, React, Vue, etc.).

To deploy this application to Vercel, you need to **completely rewrite it as a web application**. This document provides a comprehensive guide for converting the desktop app to a web-based version suitable for Vercel deployment.

---

## 🏗️ Architecture Conversion Required

### Current Stack (Desktop)
```
Python + Tkinter (Desktop GUI)
├── app.py (Tkinter UI)
├── gui_components.py (Tkinter widgets)
├── filestore_manager.py (Business logic)
└── config.py (Configuration)
```

### Target Stack for Vercel (Web)
```
Frontend: React/Next.js (Deployed to Vercel)
Backend: FastAPI/Flask (Deployed as Vercel Serverless Functions)
├── frontend/ (React/Next.js)
│   ├── pages/
│   ├── components/
│   └── api/ (calls to backend)
└── api/ (Python serverless functions)
    ├── stores.py
    ├── upload.py
    ├── query.py
    └── config.py
```

---

## 📋 Prerequisites

Before deploying to Vercel, you need:

1. **Vercel Account:** Sign up at [vercel.com](https://vercel.com)
2. **Git Repository:** Host your code on GitHub, GitLab, or Bitbucket
3. **Node.js:** v18.x or later (for frontend)
4. **Python:** 3.9-3.11 (for Vercel serverless functions)
5. **Gemini API Key:** From [Google AI Studio](https://makersuite.google.com/app/apikey)

---

## 🔄 Step-by-Step Conversion Guide

### Phase 1: Project Restructuring

#### 1.1 Create New Project Structure

```bash
gemini-filestore-web/
├── frontend/                    # Next.js application
│   ├── pages/
│   │   ├── index.js            # Dashboard
│   │   ├── stores/
│   │   │   ├── new.js          # Create store
│   │   │   └── [id].js         # Store details
│   │   ├── query.js            # Query interface
│   │   └── api/                # Frontend API routes (optional)
│   ├── components/
│   │   ├── FilePicker.jsx
│   │   ├── MetadataForm.jsx
│   │   ├── QueryPanel.jsx
│   │   └── StoreList.jsx
│   ├── styles/
│   │   └── globals.css
│   ├── public/
│   ├── package.json
│   └── next.config.js
├── api/                         # Python serverless functions
│   ├── stores/
│   │   ├── list.py             # GET /api/stores/list
│   │   ├── create.py           # POST /api/stores/create
│   │   └── delete.py           # DELETE /api/stores/delete
│   ├── files/
│   │   └── upload.py           # POST /api/files/upload
│   ├── query/
│   │   └── search.py           # POST /api/query/search
│   ├── filestore_manager.py    # Reused from original
│   └── requirements.txt
├── vercel.json                  # Vercel configuration
├── .env.example
└── README.md
```

#### 1.2 Initialize Frontend

```bash
# Create Next.js app with TypeScript
npx create-next-app@latest frontend --typescript --tailwind --app

# Navigate to frontend
cd frontend

# Install additional dependencies
npm install axios swr react-query
npm install @heroui/react framer-motion
npm install react-dropzone react-markdown
npm install date-fns lucide-react
```

#### 1.3 Setup Backend Structure

```bash
# Create API directory
mkdir -p api/stores api/files api/query

# Copy reusable modules
cp ../gemini_filestore_app/filestore_manager.py api/
cp ../gemini_filestore_app/config.py api/

# Create requirements.txt for serverless functions
cat > api/requirements.txt << EOF
google-generativeai>=0.8.0
python-dotenv>=1.0.0
EOF
```

---

### Phase 2: Backend Implementation (Serverless Functions)

Vercel supports Python serverless functions. Each API endpoint is a separate Python file.

#### 2.1 Create `api/stores/list.py`

```python
"""
Vercel Serverless Function: List all stores
Endpoint: GET /api/stores/list
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from filestore_manager import FileStoreManager


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get API key from environment
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                self._send_error(500, "API key not configured")
                return
            
            # Initialize manager
            manager = FileStoreManager(api_key)
            
            # List stores
            stores = manager.list_stores()
            
            # Send response
            self._send_json(200, {"success": True, "stores": stores})
            
        except Exception as e:
            self._send_error(500, str(e))
    
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error(self, status, message):
        self._send_json(status, {"success": False, "error": message})
```

#### 2.2 Create `api/stores/create.py`

```python
"""
Vercel Serverless Function: Create a new store
Endpoint: POST /api/stores/create
Body: {"display_name": "Store Name", "description": "Optional description"}
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from filestore_manager import FileStoreManager


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            
            # Validate input
            display_name = data.get('display_name', '').strip()
            if not display_name:
                self._send_error(400, "display_name is required")
                return
            
            description = data.get('description', '')
            
            # Get API key
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                self._send_error(500, "API key not configured")
                return
            
            # Create store
            manager = FileStoreManager(api_key)
            store_name = manager.create_store(display_name, description)
            
            self._send_json(200, {
                "success": True,
                "store_name": store_name,
                "message": "Store created successfully"
            })
            
        except Exception as e:
            self._send_error(500, str(e))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error(self, status, message):
        self._send_json(status, {"success": False, "error": message})
```

#### 2.3 Create `api/files/upload.py`

```python
"""
Vercel Serverless Function: Upload file to store
Endpoint: POST /api/files/upload
Body: multipart/form-data with file and metadata
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from filestore_manager import FileStoreManager, FileInfo


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Note: Vercel has a 4.5MB limit for serverless function payloads
            # For larger files, use a storage service like S3 or Vercel Blob
            
            content_type = self.headers.get('Content-Type', '')
            
            if not content_type.startswith('multipart/form-data'):
                self._send_error(400, "Expected multipart/form-data")
                return
            
            # Parse multipart form data (simplified - use python-multipart in production)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # For production, use python-multipart library to properly parse
            # This is a simplified example
            
            self._send_json(501, {
                "success": False,
                "error": "File upload requires Vercel Blob storage integration",
                "message": "Direct file upload to serverless functions is limited to 4.5MB. Use Vercel Blob or S3 for larger files."
            })
            
        except Exception as e:
            self._send_error(500, str(e))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error(self, status, message):
        self._send_json(status, {"success": False, "error": message})
```

#### 2.4 Create `api/query/search.py`

```python
"""
Vercel Serverless Function: Query a store
Endpoint: POST /api/query/search
Body: {"store_name": "...", "query": "...", "filters": {...}}
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from filestore_manager import FileStoreManager


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse request
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            
            # Validate input
            store_name = data.get('store_name', '').strip()
            query = data.get('query', '').strip()
            
            if not store_name or not query:
                self._send_error(400, "store_name and query are required")
                return
            
            filters = data.get('filters', {})
            
            # Get API key
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                self._send_error(500, "API key not configured")
                return
            
            # Execute query
            manager = FileStoreManager(api_key)
            result = manager.query_store(store_name, query, filters)
            
            # Return results
            self._send_json(200, {
                "success": True,
                "result": {
                    "text": result.text,
                    "citations": result.citations,
                    "tokens_used": result.tokens_used
                }
            })
            
        except Exception as e:
            self._send_error(500, str(e))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error(self, status, message):
        self._send_json(status, {"success": False, "error": message})
```

---

### Phase 3: Frontend Implementation (Next.js)

#### 3.1 Create Dashboard Page `frontend/pages/index.jsx`

```jsx
import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { PlusIcon, RefreshCwIcon, SearchIcon } from 'lucide-react';

export default function Dashboard() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStores = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/stores/list');
      const data = await response.json();
      
      if (data.success) {
        setStores(data.stores);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStores();
  }, []);

  return (
    <>
      <Head>
        <title>GeminiFileStoreManager - Dashboard</title>
      </Head>
      
      <div className="min-h-screen bg-gray-900 text-white">
        <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex justify-between items-center max-w-7xl mx-auto">
            <h1 className="text-2xl font-bold">GeminiFileStoreManager</h1>
            <div className="flex gap-4">
              <Link 
                href="/stores/new"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
              >
                <PlusIcon size={18} />
                New Store
              </Link>
              <button
                onClick={fetchStores}
                className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded"
              >
                <RefreshCwIcon size={18} />
                Refresh
              </button>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Your Stores</h2>
            <Link 
              href="/query"
              className="flex items-center gap-2 text-blue-400 hover:text-blue-300"
            >
              <SearchIcon size={18} />
              Query Interface
            </Link>
          </div>

          {loading && <p>Loading stores...</p>}
          {error && <p className="text-red-500">Error: {error}</p>}

          {!loading && !error && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {stores.length === 0 ? (
                <p className="text-gray-400 col-span-full">
                  No stores found. Create your first store to get started.
                </p>
              ) : (
                stores.map((store) => (
                  <div 
                    key={store.name}
                    className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-blue-500 transition"
                  >
                    <h3 className="text-lg font-semibold mb-2">
                      {store.display_name}
                    </h3>
                    <p className="text-gray-400 text-sm mb-4">
                      {store.file_count} files
                    </p>
                    <div className="flex gap-2">
                      <Link
                        href={`/stores/${encodeURIComponent(store.name)}`}
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        View Details
                      </Link>
                      <Link
                        href={`/query?store=${encodeURIComponent(store.name)}`}
                        className="text-green-400 hover:text-green-300 text-sm"
                      >
                        Query
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </main>
      </div>
    </>
  );
}
```

#### 3.2 Create Query Page `frontend/pages/query.jsx`

```jsx
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

export default function QueryPage() {
  const router = useRouter();
  const [stores, setStores] = useState([]);
  const [selectedStore, setSelectedStore] = useState('');
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState('{}');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load stores
    fetch('/api/stores/list')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setStores(data.stores);
          
          // Pre-select store from URL
          if (router.query.store) {
            setSelectedStore(router.query.store);
          }
        }
      })
      .catch(err => console.error(err));
  }, [router.query.store]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedStore || !query) {
      setError('Please select a store and enter a query');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const filterObj = JSON.parse(filters);
      
      const response = await fetch('/api/query/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          store_name: selectedStore,
          query: query,
          filters: filterObj
        })
      });

      const data = await response.json();

      if (data.success) {
        setResult(data.result);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Query Store - GeminiFileStoreManager</title>
      </Head>
      
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Query Store</h1>

          <form onSubmit={handleSubmit} className="space-y-6 mb-8">
            <div>
              <label className="block text-sm font-medium mb-2">
                Select Store
              </label>
              <select
                value={selectedStore}
                onChange={(e) => setSelectedStore(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2"
                required
              >
                <option value="">-- Select a store --</option>
                {stores.map(store => (
                  <option key={store.name} value={store.name}>
                    {store.display_name} ({store.file_count} files)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Query
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2 h-24"
                placeholder="Enter your question..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Metadata Filters (JSON, optional)
              </label>
              <textarea
                value={filters}
                onChange={(e) => setFilters(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2 h-20 font-mono text-sm"
                placeholder='{"doc_type": "Contratto"}'
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-3 rounded font-medium"
            >
              {loading ? 'Searching...' : 'Submit Query'}
            </button>
          </form>

          {error && (
            <div className="bg-red-900 border border-red-700 rounded p-4 mb-6">
              <p className="text-red-200">{error}</p>
            </div>
          )}

          {result && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Result</h2>
              
              <div className="prose prose-invert max-w-none mb-6">
                <p className="whitespace-pre-wrap">{result.text}</p>
              </div>

              {result.citations && result.citations.length > 0 && (
                <div className="border-t border-gray-700 pt-4">
                  <h3 className="font-medium mb-3">Citations ({result.citations.length})</h3>
                  <div className="space-y-2">
                    {result.citations.map((citation, idx) => (
                      <div key={idx} className="bg-gray-900 rounded p-3 text-sm">
                        <p className="text-gray-400">Source {idx + 1}</p>
                        <p className="text-gray-300">{JSON.stringify(citation)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-gray-500 text-sm mt-4">
                Tokens used: {result.tokens_used}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
```

---

### Phase 4: Vercel Configuration

#### 4.1 Create `vercel.json`

```json
{
  "version": 2,
  "name": "gemini-filestore-manager",
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    },
    {
      "src": "api/**/*.py",
      "use": "@vercel/python",
      "config": {
        "maxDuration": 60
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "env": {
    "GEMINI_API_KEY": "@gemini-api-key"
  },
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.9",
      "maxDuration": 60
    }
  }
}
```

#### 4.2 Create `.env.example`

```bash
# Copy this file to .env.local and fill in your values

# Gemini API Key (Get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_api_key_here

# Optional: Custom API endpoint
API_BASE_URL=http://localhost:3000/api
```

#### 4.3 Create `.gitignore`

```
# Dependencies
node_modules/
frontend/node_modules/
frontend/.next/
frontend/out/

# Environment variables
.env
.env.local
.env.production
.env.*.local
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
app.log

# Build
dist/
build/

# Vercel
.vercel
```

---

## 🚀 Deployment Steps

### Step 1: Prepare Repository

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Web version for Vercel"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/gemini-filestore-web.git
git branch -M main
git push -u origin main
```

### Step 2: Configure Vercel Project

1. **Login to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with your GitHub account

2. **Import Project:**
   - Click "Add New..." → "Project"
   - Select your GitHub repository
   - Click "Import"

3. **Configure Project:**
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)
   - **Install Command:** `npm install` (default)

4. **Environment Variables:**
   - Click "Environment Variables"
   - Add: `GEMINI_API_KEY` = `your_actual_api_key`
   - Select: Production, Preview, and Development

5. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete (2-5 minutes)

### Step 3: Verify Deployment

1. **Check Build Logs:**
   - Monitor for any errors during build
   - Common issues: Missing dependencies, environment variables

2. **Test Endpoints:**
   ```bash
   # Test store listing
   curl https://your-app.vercel.app/api/stores/list
   
   # Test store creation
   curl -X POST https://your-app.vercel.app/api/stores/create \
     -H "Content-Type: application/json" \
     -d '{"display_name":"Test Store","description":"Test"}'
   ```

3. **Access Frontend:**
   - Visit: `https://your-app.vercel.app`
   - Test dashboard, create store, query functionality

---

## ⚠️ Important Limitations & Considerations

### Vercel Serverless Limitations

1. **Execution Time:**
   - Free: 10 seconds max
   - Pro: 60 seconds max
   - This may be insufficient for large file uploads

2. **Payload Size:**
   - Request: 4.5MB max
   - Response: 4.5MB max
   - Use Vercel Blob or external storage for large files

3. **Memory:**
   - Free: 1024MB
   - Pro: 3008MB
   - Consider for processing large documents

4. **Cold Starts:**
   - Functions may take 2-3 seconds to initialize
   - Use Vercel Edge Functions for faster response

### Recommended Solutions

#### For Large File Uploads

**Option 1: Vercel Blob Storage**
```bash
npm install @vercel/blob
```

```javascript
// In your upload endpoint
import { put } from '@vercel/blob';

// Upload to Blob, then pass URL to Gemini
const blob = await put('filename.pdf', file, {
  access: 'public'
});
```

**Option 2: Direct Client Upload**
```javascript
// Upload directly from browser to Gemini
// (Requires exposing API key - use with caution)
```

**Option 3: AWS S3 Integration**
```bash
npm install @aws-sdk/client-s3
```

#### For Long-Running Operations

**Option 1: Queue System (Vercel + Redis)**
```bash
npm install @upstash/redis
```

**Option 2: Background Jobs (Vercel Cron)**
```javascript
// In vercel.json
{
  "crons": [{
    "path": "/api/cron/process-uploads",
    "schedule": "*/5 * * * *"
  }]
}
```

---

## 🔧 Advanced Configuration

### Custom Domain

1. In Vercel dashboard → Settings → Domains
2. Add your domain: `filestore.yourdomain.com`
3. Follow DNS configuration instructions
4. Wait for SSL certificate (automatic)

### Analytics

```javascript
// In frontend/pages/_app.jsx
import { Analytics } from '@vercel/analytics/react';

function MyApp({ Component, pageProps }) {
  return (
    <>
      <Component {...pageProps} />
      <Analytics />
    </>
  );
}
```

### Edge Functions (Faster Response)

```javascript
// api/edge/stores-list.js
export const config = {
  runtime: 'edge',
};

export default async function handler(req) {
  // Faster, but limited Node.js APIs
  return new Response(JSON.stringify({ stores: [] }), {
    headers: { 'content-type': 'application/json' }
  });
}
```

### Caching Strategy

```javascript
// In next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/api/stores/list',
        headers: [
          {
            key: 'Cache-Control',
            value: 's-maxage=60, stale-while-revalidate',
          },
        ],
      },
    ];
  },
};
```

---

## 🐛 Troubleshooting

### Build Fails

**Error:** `Module not found: Can't resolve 'filestore_manager'`
```bash
# Ensure api/requirements.txt includes all dependencies
# Check that filestore_manager.py is in api/ directory
```

**Error:** `Python version not supported`
```json
// In vercel.json, specify Python version
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.9"
    }
  }
}
```

### API Returns 500

**Check Logs:**
1. Vercel Dashboard → Your Project → Deployments
2. Click latest deployment → View Function Logs
3. Look for Python errors

**Common Issues:**
- Missing `GEMINI_API_KEY` environment variable
- Import errors (wrong file paths)
- API rate limiting from Gemini

### CORS Errors

```python
# Add CORS headers to all serverless functions
def do_OPTIONS(self):
    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    self.end_headers()
```

---

## 📊 Cost Estimation

### Vercel Pricing

**Free Tier:**
- 100GB bandwidth/month
- 100 hours serverless execution/month
- Hobby projects only

**Pro Tier ($20/month):**
- 1TB bandwidth
- 1000 hours execution
- Commercial use allowed
- Advanced analytics

**Additional Costs:**
- Vercel Blob: $0.15/GB stored + $0.30/GB bandwidth
- Gemini API: Pay-per-token (check Google AI pricing)

---

## 🔐 Security Best Practices

1. **Never expose API key to frontend**
   - Always use serverless functions as proxy

2. **Implement authentication**
   ```bash
   npm install next-auth
   ```

3. **Rate limiting**
   ```bash
   npm install @upstash/ratelimit
   ```

4. **Input validation**
   ```bash
   npm install zod
   ```

5. **Environment variable encryption**
   - Vercel encrypts all environment variables automatically

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Vercel Python Runtime](https://vercel.com/docs/runtimes#official-runtimes/python)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Vercel Blob Storage](https://vercel.com/docs/storage/vercel-blob)

---

## ✅ Deployment Checklist

- [ ] Convert Tkinter UI to React/Next.js
- [ ] Create Python serverless functions
- [ ] Test all API endpoints locally
- [ ] Set up Git repository
- [ ] Create Vercel account
- [ ] Configure environment variables
- [ ] Deploy to Vercel
- [ ] Test production deployment
- [ ] Set up custom domain (optional)
- [ ] Enable analytics (optional)
- [ ] Implement authentication (recommended)
- [ ] Set up monitoring and alerts

---

## 🆘 Support

If you encounter issues:

1. Check [Vercel Status](https://vercel.com/status)
2. Review [Vercel Community](https://github.com/vercel/vercel/discussions)
3. Check deployment logs in Vercel dashboard
4. Test API endpoints with curl/Postman
5. Enable debug mode in Next.js:
   ```bash
   DEBUG=* npm run dev
   ```

---

**Remember:** This is a complete rewrite, not a simple deployment. The desktop app cannot run on Vercel as-is. Budget 2-4 weeks for a production-ready web version.
