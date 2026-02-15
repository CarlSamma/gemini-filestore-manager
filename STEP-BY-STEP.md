# GeminiFileStoreManager - Step-by-Step Guide for Everyone

## What Is This?

Think of GeminiFileStoreManager like a smart filing cabinet powered by AI. You put your documents in, and later you can ask questions about them in plain English. The AI reads through all your documents and gives you answers with references to where it found the information.

**Perfect for:** Legal documents, contracts, research papers, client files, or any collection of documents you need to search through quickly.

---

## What You Need Before Starting

### 1. A Computer
- Windows, Mac, or Linux
- At least 4GB of RAM (memory)
- Internet connection

### 2. Python Installed
Don't worry if this sounds technical - it's like installing any other program:

**For Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow "Download Python" button
3. Run the installer
4. ✅ **IMPORTANT:** Check the box that says "Add Python to PATH"
5. Click "Install Now"

**For Mac:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the macOS installer
3. Open the downloaded file and follow the steps

**For Linux:**
- Python is usually already installed! Open Terminal and type `python3 --version` to check

### 3. A Gemini API Key (Free)
This is like a password that lets your computer talk to Google's AI:

1. Go to [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the long text that appears (it looks like: `AIzaSyD...`)
5. Save it somewhere safe - you'll need it in Step 3

---

## Installation - Getting the App on Your Computer

### Step 1: Download the App

**Option A - If you have the ZIP file:**
1. Find the `gemini_filestore_app.zip` file
2. Right-click it and choose "Extract" or "Unzip"
3. Remember where you saved the folder!

**Option B - If you're downloading from the internet:**
1. Download the project files to your computer
2. Unzip them to a folder like `Documents/GeminiFileStore`

### Step 2: Install Dependencies

Dependencies are like helper programs the app needs to work.

**Windows:**
1. Open the Start Menu
2. Type `cmd` and press Enter (this opens Command Prompt)
3. Type this command and press Enter:
   ```
   cd Documents\GeminiFileStore
   ```
   (Change this to wherever you unzipped the folder)
4. Then type:
   ```
   pip install -r requirements.txt
   ```
5. Wait for it to finish (might take 1-2 minutes)

**Mac/Linux:**
1. Open Terminal (search for it in Applications)
2. Type:
   ```
   cd ~/Documents/GeminiFileStore
   ```
   (Change this to wherever you unzipped the folder)
3. Then type:
   ```
   pip3 install -r requirements.txt
   ```
4. Wait for it to finish

### Step 3: Add Your API Key

1. In the folder where you unzipped the app, create a new text file
2. Name it exactly: `.env` (yes, it starts with a dot!)
3. Open it with Notepad or any text editor
4. Type this line:
   ```
   GEMINI_API_KEY=paste_your_key_here
   ```
   Replace `paste_your_key_here` with the key you copied earlier
5. Save and close the file

**Windows tip:** To see files starting with a dot, in File Explorer click View → Show → Hidden items

---

## Using the App

### Starting the App

**Windows:**
1. Open Command Prompt (Start Menu → type `cmd`)
2. Navigate to your folder:
   ```
   cd Documents\GeminiFileStore
   ```
3. Type:
   ```
   python app.py
   ```

**Mac/Linux:**
1. Open Terminal
2. Navigate to your folder:
   ```
   cd ~/Documents/GeminiFileStore
   ```
3. Type:
   ```
   python3 app.py
   ```

A window will open - this is your app! 🎉

---

## How to Use Each Part

### Tab 1: Dashboard - Your Main View

**What you see:**
- A list of all your document "stores" (filing cabinets)
- How many files are in each store
- When each store was created

**What you can do:**
- **Right-click** a store to see options (Query, Delete)
- **Double-click** a store to quickly search it
- Click the **Refresh** button to update the list

### Tab 2: New Store - Adding Documents

Think of this like creating a new filing cabinet and filling it with documents.

**Step-by-step:**

1. **Enter a Store Name**
   - Example: "Client Contracts 2024" or "Research Papers"
   - This is just for your reference

2. **Add a Description (Optional)**
   - Example: "All contracts signed in Q1 2024"

3. **Select Your Files**
   - Click **"Select Folder"** to add all files from a folder, or
   - Click **"Select Files"** to pick specific files
   - The app supports: PDF, Word, text files, and more

4. **Add Metadata (Optional but Helpful)**
   
   Metadata is like labels on your files. You can add:
   - **Practice**: Like "Real Estate" or "Corporate Law"
   - **Document Type**: Choose from dropdown (Contract, Invoice, etc.)
   - **Tags**: Add keywords like "urgent", "2024", "client-A"
   - **Date**: When the document was created
   - **Client**: Who the document is for
   
   This helps you filter later when searching!

5. **Adjust Chunking (Usually Leave as Default)**
   - This controls how the AI breaks up your documents
   - Default settings work great for most documents

6. **Click "Create Store & Upload Files"**
   - A progress bar will show how the upload is going
   - Larger files take longer - be patient!
   - You can click **Cancel** if needed

**Tips:**
- Upload 5-10 documents at a time for best results
- Each file should be under 100MB
- Total files per store should be under 1GB

### Tab 3: Query - Asking Questions

This is where the magic happens!

**Step-by-step:**

1. **Select a Store** from the dropdown
   - Choose which filing cabinet you want to search

2. **Type Your Question**
   - Ask in plain English!
   - Examples:
     - "What are the payment terms in the Smith contract?"
     - "Which documents mention trademark infringement?"
     - "Summarize the main points about data privacy"

3. **Add Filters (Optional)**
   - If you added metadata earlier, you can filter here
   - Example: Only search documents tagged "urgent"
   - Format: `{"tags": ["urgent"]}`
   - Leave blank if you want to search everything

4. **Click "Submit Query"**
   - Wait a few seconds (the AI is reading your documents!)

5. **Read the Results**
   - The answer appears in the results panel
   - Below the answer, you'll see **Citations** - these show which documents the AI used
   - You can verify the information by checking those source documents

**Example Questions:**
- "What are the key terms in contract X?"
- "List all documents that mention [specific topic]"
- "When was payment due according to invoice Y?"
- "Compare the warranties in these three contracts"

### Tab 4: Settings

**What you can do here:**
1. **Update Your API Key** if it changes
2. **Change the Theme** (different color schemes)
3. **Save Changes** when you're done

### Tab 5: Logs

This shows what's happening behind the scenes. Useful if something goes wrong - you can see error messages here.

---

## Keyboard Shortcuts (Time-Savers!)

- **Ctrl+N** - Create a new store quickly
- **F5** - Refresh the store list
- **Ctrl+Q** - Jump to query tab
- **Alt+F4** - Close the app

---

## Common Questions

### "The app won't start!"

**Check these things:**
1. Did you install Python? Type `python --version` in Command Prompt/Terminal
2. Did you install the dependencies? (The `pip install` step)
3. Did you add your API key to the `.env` file?
4. Is your internet working? The app needs to connect to Google's servers

### "My query isn't giving good answers"

**Try these tips:**
1. Be more specific in your question
2. Check that you uploaded the right documents
3. Make sure the documents are readable (not scanned images without OCR)
4. Try adding metadata to help narrow down the search

### "Upload is taking forever"

**This is normal if:**
- You have large files (PDFs can be big!)
- You have many files (uploading 50 files takes time)
- Your internet is slow

**What to do:**
- Upload fewer files at a time (5-10 is good)
- Upload during off-peak internet hours
- Be patient - it's worth the wait!

### "I got an error about API limits"

Google's free tier has limits. If you hit them:
- Wait a few minutes and try again
- Upload fewer files at once
- Check [Google AI pricing](https://ai.google.dev/pricing) for limits

### "Can I share my stores with others?"

Not directly with this desktop version. Each person needs their own:
- Installation of the app
- Their own API key
- Their own uploaded documents

For team use, consider the web version (see VERCELDEPLOY.md).

---

## Best Practices

### For Best Results:

1. **Organize Before Uploading**
   - Group related documents in one store
   - Example: All contracts in "Contracts 2024", all invoices in "Invoices"

2. **Use Good Metadata**
   - Tag documents with relevant keywords
   - Fill in the date and client fields
   - Choose the correct document type

3. **Write Clear Questions**
   - ❌ Bad: "What about payment?"
   - ✅ Good: "What are the payment terms in the Johnson contract?"

4. **Verify Important Information**
   - Always check the citations
   - Don't rely 100% on AI for legal/financial decisions
   - Use the AI as a research assistant, not a lawyer

5. **Regular Maintenance**
   - Delete old stores you don't need
   - Update documents when they change
   - Back up important files separately

---

## Troubleshooting

### Error: "Module not found"
**Fix:** You didn't install dependencies. Go back to Installation Step 2.

### Error: "API key not found"
**Fix:** Your `.env` file is missing or incorrect. Check Installation Step 3.

### Error: "Connection refused"
**Fix:** Check your internet connection. The app needs internet to work.

### The app crashes when uploading
**Fix:** 
- Try uploading fewer files at once
- Check if you have enough disk space
- Make sure files aren't corrupted

### Dark theme is hard to read
**Fix:** Go to Settings tab → Change theme to a lighter option

---

## Safety & Privacy

### Your Data:
- **Files are uploaded to Google's servers** (Gemini API)
- Google's privacy policy applies
- Don't upload highly confidential data unless you trust Google's security
- Your API key is stored locally on your computer

### Recommendations:
- Don't share your API key with anyone
- Don't upload client-confidential information without permission
- Keep backups of important documents
- Review Google's terms of service for Gemini API

---

## Getting Help

### If you're stuck:

1. **Check the Logs tab** - error messages often explain the problem
2. **Read error messages carefully** - they usually tell you what's wrong
3. **Google the error message** - others have probably had the same issue
4. **Check your API key** - expired or wrong keys are a common issue
5. **Restart the app** - sometimes this fixes weird glitches

### Where to learn more:

- Gemini API Docs: [ai.google.dev/docs](https://ai.google.dev/docs)
- Python Help: [python.org/about/help](https://www.python.org/about/help/)
- Project Documentation: See README.md in your folder

---

## Quick Reference Card

### To Start the App:
```
Windows: python app.py
Mac/Linux: python3 app.py
```

### Supported File Types:
PDF, Word (.doc, .docx), Text (.txt, .md), HTML, CSV, JSON, and code files

### File Size Limits:
- Per file: 100MB max
- Per store: 1GB total max

### Common Metadata Fields:
- practice (text)
- doc_type (dropdown)
- tags (keywords)
- date (YYYY-MM-DD)
- client (text)

---

## You're All Set! 🎉

Remember:
1. Create a store for your document collection
2. Upload your files with good metadata
3. Ask questions in plain English
4. Check the citations to verify answers

The more you use it, the more comfortable you'll get. Start with a small test - upload 5 documents and try asking a few questions. You'll get the hang of it quickly!

**Happy searching!** 📚🔍
