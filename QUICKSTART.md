# Quick Start Guide

Get your Spermophilus OCR bot running in minutes!

## 🚀 5-Minute Quick Start

### Prerequisites
- Python 3.13+ or Docker
- LM Studio installed
- Telegram Bot Token

### Step 1: Get Bot Token
1. Message `@BotFather` in Telegram
2. Send `/newbot`
3. Follow prompts → Save your token

### Step 2: Setup LM Studio
1. Install [LM Studio](https://lmstudio.ai/)
2. Search for `Qwen3-VL-4B`
3. Download and load model
4. Start server on port 1234

### Step 3: Configure Bot
```bash
# Clone and setup
git clone <repository-url>
cd Spermophilus
cp .env.example .env

# Edit .env with:
# - TELEGRAM_BOT_TOKEN=your_token
# - ALLOWED_USER_IDS=your_telegram_id
# - LM_STUDIO_URL=http://localhost:1234/v1
```

### Step 4: Run Bot
```bash
# Option A: Direct Python
uv sync
uv run python -m src.main

# Option B: Docker
docker-compose up -d
```

### Step 5: Test!
1. Send `/start` to your bot
2. Send an image with text
3. Receive extracted text! 🎉

## 📱 Testing Your Bot

### Quick Test Files
Create these test files in `test_files/`:

1. **Text Image**: Any photo with clear text
2. **PDF Document**: 2-3 page PDF
3. **Handwritten Note**: Photo of handwritten text

### Expected Results
- ✅ Bot responds immediately with "⏳ Queued for processing..."
- ✅ Returns extracted text in 10-30 seconds
- ✅ Shows "✅ OCR Result:" with formatted text
- ✅ Duplicate files return cached results instantly

## 🔧 Common Fixes

### "OCR API unavailable"
```bash
# Check LM Studio
curl http://localhost:1234/v1/models

# Restart LM Studio server
```

### "Unauthorized access"
```bash
# Get your user ID
# Message @userinfobot in Telegram
# Add ID to ALLOWED_USER_IDS in .env
```

### PDF processing fails
```bash
# Linux/macOS
sudo apt install poppler-utils  # Linux
brew install poppler          # macOS

# Windows: Download from http://blog.alivate.com.au/poppler-windows/
```

## 📊 Monitor Your Bot

### Check Logs
```bash
# Real-time logs
docker-compose logs -f

# Debug mode
LOG_LEVEL=DEBUG uv run python -m src.main
```

### Database Stats
```bash
# View job history
sqlite3 data/ocr.db "SELECT status, COUNT(*) FROM jobs GROUP BY status;"

# View cached results
sqlite3 data/ocr.db "SELECT COUNT(*) FROM results;"
```

## 🎯 Next Steps

1. **Read Full Documentation**: `docs/SETUP.md`
2. **Run Comprehensive Tests**: `docs/TESTING.md`
3. **Deploy to Production**: `docs/DEPLOYMENT.md`
4. **Contribute**: `docs/DEVELOPMENT.md`

## 🆘 Need Help?

- **Issues**: Check `docs/TESTING.md` → Troubleshooting section
- **Logs**: Enable `LOG_LEVEL=DEBUG` in .env
- **Community**: Create GitHub issue with details

Happy OCR processing! 📸→📝