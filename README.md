# Spermophilus - Telegram OCR Bot

A resilient Telegram bot that extracts text from images and PDFs using local AI models via LM Studio. Features atomic job processing, deduplication, and structured logging.

## 🚀 Features

- **Multi-format Support**: Process both images (JPG, PNG) and PDF documents
- **Local AI Processing**: Uses LM Studio for privacy-focused OCR
- **Atomic Job Queue**: Crash-resistant processing with SQLite backend
- **Smart Deduplication**: SHA256-based caching prevents redundant processing
- **Structured Logging**: JSON logs for production, colored console for development
- **Resilient Workers**: Health checks and automatic recovery
- **Docker Ready**: Complete containerization with docker-compose

## 🚀 Quick Start

Get running in 5 minutes! See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

```bash
# 1. Clone and setup
git clone <repository-url>
cd Spermophilus
uv sync

# 2. Configure
cp .env.example .env
# Edit with your bot token and user ID

# 3. Run
uv run python -m src.main
```

## 📋 Prerequisites

- Python 3.11+ (or use Docker)
- LM Studio with a vision-capable model
- Telegram Bot Token
- Poppler utilities (for PDF processing)

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Setup LM Studio

1. Install [LM Studio](https://lmstudio.ai/)
2. Download a vision model (e.g., `llava-v1.5-7b`)
3. Start the server with:
   - Model: Your chosen vision model
   - Port: 1234 (default)
   - Host: localhost

### 4. Run the Bot

```bash
uv run python -m src.main
```

## 📁 Project Structure

```
Spermophilus/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Main application entry point
│   ├── logger.py            # Structured logging configuration
│   ├── database.py          # SQLite database and job queue
│   ├── utils.py             # File hashing and PDF conversion
│   ├── worker.py            # OCR worker implementation
│   └── handlers.py          # Telegram bot handlers
├── data/                    # Database and temporary files
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── pyproject.toml          # Project configuration
└── .env.example            # Environment variables template
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required |
| `ALLOWED_USER_IDS` | Comma-separated user IDs | Required |
| `LM_STUDIO_URL` | LM Studio API endpoint | `http://localhost:1234/v1` |
| `WORKER_NAME` | Worker identifier | `worker_1` |
| `LOG_LEVEL` | Logging level (INFO/DEBUG) | `INFO` |

### LM Studio Setup

1. **Install LM Studio**: Download from [lmstudio.ai](https://lmstudio.ai/)
2. **Search for Vision Models**: Use the search tab to find models like:
   - `llava-v1.5-7b`
   - `bakllava-1-8b`
   - `moondream2`
3. **Download and Load**: Select your model and click "Load"
4. **Configure Server**:
   - Go to "Speech" tab (⚙️)
   - Set "Server Port" to 1234
   - Enable "CORS" if needed
   - Click "Start Server"

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Configure environment
cp .env.example .env
# Edit .env with your settings

# Build and run
docker-compose up -d
```

### Manual Docker Build

```bash
docker build -t spermophilus .
docker run -d \
  --name ocr-bot \
  --network host \
  -v $(pwd)/data:/app/data \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e ALLOWED_USER_IDS=123,456 \
  -e LM_STUDIO_URL=http://localhost:1234/v1 \
  spermophilus
```

## 📊 Monitoring

### Logs

The bot uses structured logging. In production (Docker), logs are JSON formatted:

```json
{
  "event": "Job completed",
  "job_id": 42,
  "file_hash": "a1b2c3d4",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Database

You can inspect the SQLite database:

```bash
sqlite3 data/ocr.db
.tables  -- Show tables
SELECT * FROM jobs;  -- View job history
SELECT * FROM results;  -- View cached results
```

## 🔧 Development

### Code Quality

```bash
# Lint and format
uv run ruff check
uv run ruff format

# Run tests
uv run pytest
```

### Project Structure

- **Atomic Queue**: Uses SQLite RETURNING clause for crash-safe job claiming
- **Deduplication**: SHA256 hashing prevents reprocessing identical files
- **Error Handling**: Comprehensive error recovery and user feedback
- **Resource Management**: Automatic cleanup of temporary files

## 🚨 Troubleshooting

### Common Issues

1. **"OCR API unavailable"**
   - Ensure LM Studio is running
   - Check the LM_STUDIO_URL in your .env
   - Verify the model supports vision

2. **"Unauthorized access attempt"**
   - Add your Telegram user ID to ALLOWED_USER_IDS
   - Use @userinfobot to get your user ID

3. **PDF Processing Fails**
   - Install poppler-utils: `sudo apt install poppler-utils`
   - Check file permissions in data/ directory

4. **Database Locked**
   - Ensure only one bot instance is running
   - Check for crashed processes: `ps aux | grep python`

### Debug Mode

Set `LOG_LEVEL=DEBUG` in your .env file for detailed logging.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the logs for error details