# Setup and Configuration Guide

This guide walks you through setting up Spermophilus OCR bot from scratch.

## 📋 Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.11+ (or use Docker)
- **RAM**: Minimum 4GB (8GB+ recommended for AI models)
- **Storage**: 2GB+ free space
- **Network**: Internet connection for model downloads

### Required Software

1. **UV Package Manager** - Fast Python package management
2. **LM Studio** - Local AI model server
3. **Poppler Utils** - PDF processing (Linux/macOS)
4. **Git** - Version control (optional but recommended)

## 🔧 Step 1: Install System Dependencies

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python and build tools
sudo apt install python3 python3-pip python3-venv git

# Install Poppler for PDF processing
sudo apt install poppler-utils

# Install UV (recommended method)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 poppler git

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

```powershell
# Install UV (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install Poppler (using Chocolatey)
choco install poppler

# Or download manually from: http://blog.alivate.com.au/poppler-windows/
```

## 🚀 Step 2: Setup Project

### Clone Repository

```bash
git clone <repository-url>
cd Spermophilus
```

### Install Dependencies

```bash
# Install all project dependencies
uv sync

# This creates a virtual environment and installs:
# - python-telegram-bot[job-queue]
# - openai
# - pdf2image
# - pillow
# - python-dotenv
# - structlog
# - aiosqlite
# - pydantic-settings
# - ruff (dev)
# - pytest (dev)
```

### Verify Installation

```bash
# Check if dependencies are installed
uv run python -c "import telegram, openai, pdf2image; print('All dependencies OK!')"

# Run linting check
uv run ruff check
```

## 🤖 Step 3: Setup Telegram Bot

### Create Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start chat** with BotFather
3. **Create new bot**:
   ```
   /start
   /newbot
   ```
4. **Follow prompts**:
   - Bot name: `Spermophilus OCR`
   - Username: `spermophilus_ocr_bot` (must end with `_bot`)
5. **Save your token** - it looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### Get Your User ID

1. **Search for** `@userinfobot` in Telegram
2. **Send any message** to get your user ID
3. **Note the number** (e.g., `123456789`)

## 🧠 Step 4: Setup LM Studio

### Install LM Studio

1. **Download** from [lmstudio.ai](https://lmstudio.ai/)
2. **Install** for your operating system
3. **Launch** the application

### Download Vision Model

1. **Open LM Studio**
2. **Go to Search tab** (🔍)
3. **Search for vision models**:
   - `llava-v1.5-7b` (recommended)
   - `bakllava-1-8b`
   - `moondream2`
4. **Download** your chosen model (2-8GB)

### Configure LM Studio Server

1. **Go to Chat tab** (💬)
2. **Select your downloaded model**
3. **Click "Load Model"**
4. **Configure server settings**:
   - Click the gear icon (⚙️) next to model
   - Set "Server Port" to `1234`
   - Enable "CORS" if accessing from Docker
   - Set "Context Length" to `4096` or higher
5. **Start server**:
   - Click "Start Server" button
   - Verify it shows "Server running on http://localhost:1234"

### Test LM Studio

```bash
# Test if LM Studio is responding
curl http://localhost:1234/v1/models

# Should return JSON with model information
```

## ⚙️ Step 5: Configure Environment

### Create Environment File

```bash
# Copy the template
cp .env.example .env

# Edit with your configuration
nano .env  # or use your preferred editor
```

### Environment Variables Explained

```ini
# Required: Your Telegram bot token from BotFather
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Required: Comma-separated user IDs who can use the bot
ALLOWED_USER_IDS=123456789,987654321

# LM Studio API endpoint (usually localhost:1234)
LM_STUDIO_URL=http://localhost:1234/v1

# Worker identifier (useful for multiple instances)
WORKER_NAME=worker_1

# Logging level: INFO (normal) or DEBUG (verbose)
LOG_LEVEL=INFO
```

### Security Notes

- **Never commit** `.env` file to version control
- **Keep bot token** secret - anyone with it can control your bot
- **Limit user access** by only adding trusted user IDs
- **Consider using** a separate Telegram account for testing

## 📁 Step 6: Setup Data Directory

```bash
# Create data directories (should already exist)
mkdir -p data/temp
mkdir -p data/tmp

# Set proper permissions
chmod 755 data
chmod 755 data/temp
chmod 755 data/tmp
```

## ✅ Step 7: Verify Setup

### Test Dependencies

```bash
# Test all imports
uv run python -c "
import sys
sys.path.append('src')
from logger import setup_logging
from database import init_db
from worker import OCRWorker
from handlers import start, handle_document
print('✅ All modules imported successfully')
"
```

### Test Database

```bash
# Test database initialization
uv run python -c "
import asyncio
import sys
sys.path.append('src')
from database import init_db
asyncio.run(init_db())
print('✅ Database initialized successfully')
"
```

### Test LM Studio Connection

```bash
# Test API connectivity
uv run python -c "
import asyncio
from openai import AsyncOpenAI
async def test():
    client = AsyncOpenAI(base_url='http://localhost:1234/v1', api_key='test')
    models = await client.models.list()
    print('✅ LM Studio API is accessible')
    print(f'Available models: {[m.id for m in models.data]}')
asyncio.run(test())
"
```

## 🚀 Step 8: First Run

### Start the Bot

```bash
# Run in development mode
uv run python -m src.main
```

### Expected Output

```
2024-01-01 12:00:00 [INFO] Database initialized and stuck jobs reset
2024-01-01 12:00:00 [INFO] Worker started worker_id=worker_1
🚀 Bot is running...
```

### Test in Telegram

1. **Send `/start`** to your bot
2. **Should reply**: "👋 Send me an Image or PDF to extract text."
3. **Send an image** with text
4. **Should reply**: "⏳ Queued for processing..."
5. **Wait for result**: Should receive extracted text

## 🔧 Troubleshooting Setup Issues

### Common Problems

1. **"Module not found" errors**
   ```bash
   # Ensure you're in project directory
   cd Spermophilus
   uv sync
   ```

2. **LM Studio connection failed**
   ```bash
   # Check if LM Studio is running
   curl http://localhost:1234/v1/models
   
   # If connection fails, restart LM Studio server
   ```

3. **Permission denied errors**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER data/
   chmod -R 755 data/
   ```

4. **Bot token invalid**
   - Double-check token from BotFather
   - Ensure no extra spaces or characters
   - Create a new bot if needed

### Debug Mode

Enable verbose logging by setting in `.env`:

```ini
LOG_LEVEL=DEBUG
```

This will show detailed information about:
- Database operations
- API calls to LM Studio
- File processing steps
- Error stack traces

## 📱 Mobile Setup (Optional)

### Android

1. **Install Termux** from F-Droid
2. **Setup Python and dependencies** in Termux
3. **Install LM Studio** on your main computer
4. **Configure LM_STUDIO_URL** to your computer's IP

### iOS

1. **Use Pythonista** or similar app
2. **Run LM Studio** on Mac/PC
3. **Connect via network** to LM Studio

## 🎯 Next Steps

After successful setup:

1. **Read the Testing Guide** for comprehensive testing
2. **Check the Development Guide** for contributing
3. **Review the Deployment Guide** for production setup
4. **Monitor logs** to ensure smooth operation

Your Spermophilus OCR bot is now ready for use! 🎉