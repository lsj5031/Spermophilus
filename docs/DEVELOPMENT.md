# Development Guide

This guide covers development practices, code architecture, and contribution guidelines for Spermophilus OCR bot.

## 🏗️ Project Architecture

### Core Components

```
src/
├── main.py          # Application entry point and bot setup
├── logger.py        # Structured logging configuration
├── database.py      # SQLite database and job queue management
├── utils.py         # File utilities (hashing, PDF conversion)
├── worker.py        # OCR worker with LM Studio integration
└── handlers.py      # Telegram bot message handlers
```

### Data Flow

```
Telegram Message → handlers.py → database.py → worker.py → LM Studio
                      ↓              ↓              ↓
                   File Cache → Job Queue → OCR Processing
                      ↓              ↓              ↓
                   Response ← Results ← Extracted Text
```

### Key Design Patterns

1. **Atomic Job Queue**: SQLite RETURNING clause for crash-safe job claiming
2. **Deduplication**: SHA256 hashing prevents redundant processing
3. **Structured Logging**: JSON logs for production, colored console for dev
4. **Error Recovery**: Comprehensive error handling with user feedback
5. **Resource Management**: Automatic cleanup of temporary files

## 🛠️ Development Setup

### Prerequisites

- Python 3.13+
- UV package manager
- Git
- Code editor (VS Code recommended)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd Spermophilus

# Install dependencies
uv sync

# Install pre-commit hooks (optional)
uv run pre-commit install
```

### Development Environment

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install development dependencies
uv sync --dev
```

## 📝 Code Style and Standards

### Linting and Formatting

```bash
# Check code style
uv run ruff check

# Auto-fix issues
uv run ruff check --fix

# Format code
uv run ruff format

# Check both
uv run ruff check --fix && uv run ruff format
```

### Code Style Rules

- **Line length**: 88 characters
- **Quotes**: Double quotes for strings
- **Imports**: Organized and sorted
- **Type hints**: Required for all functions
- **Docstrings**: Google-style for public functions

### Example Code Style

```python
"""Module docstring explaining purpose."""

import asyncio
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


async def process_file(file_path: Path, max_retries: int = 3) -> Optional[str]:
    """Process a file and return extracted text.
    
    Args:
        file_path: Path to the file to process
        max_retries: Maximum number of retry attempts
        
    Returns:
        Extracted text or None if processing failed
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ProcessingError: If processing fails after retries
    """
    for attempt in range(max_retries):
        try:
            logger.info("Processing file", path=str(file_path), attempt=attempt + 1)
            # Processing logic here
            return "extracted text"
        except Exception as e:
            logger.error("Processing failed", error=str(e), attempt=attempt + 1)
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return None
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_database.py

# Run with verbose output
uv run pytest -v
```

### Writing Tests

#### Test Structure

```python
"""Tests for database module."""

import pytest
import tempfile
from pathlib import Path

from src.database import init_db, add_job, claim_next_job


@pytest.fixture
async def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    # Override DB_PATH for test
    original_path = src.database.DB_PATH
    src.database.DB_PATH = db_path
    
    await init_db()
    
    yield db_path
    
    # Cleanup
    src.database.DB_PATH = original_path
    db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_add_and_claim_job(temp_db):
    """Test adding and claiming jobs."""
    # Add job
    job_id = await add_job(123, 456, "hash123", "/path/to/file")
    assert job_id > 0
    
    # Claim job
    job = await claim_next_job("test_worker")
    assert job is not None
    assert job["chat_id"] == 123
    assert job["file_hash"] == "hash123"
```

#### Test Categories

1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Component interaction
3. **End-to-End Tests**: Full workflow testing
4. **Performance Tests**: Load and timing tests

### Test Data Management

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_image():
    """Provide sample image for testing."""
    return Path("tests/fixtures/sample.jpg")

@pytest.fixture
def sample_pdf():
    """Provide sample PDF for testing."""
    return Path("tests/fixtures/sample.pdf")

@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
```

## 🔧 Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... code changes ...

# Run tests
uv run pytest

# Run linting
uv run ruff check --fix && uv run ruff format

# Commit changes
git add .
git commit -m "feat: add new feature description"

# Push branch
git push origin feature/new-feature
```

### 2. Bug Fixes

```bash
# Create bugfix branch
git checkout -b fix/issue-description

# Reproduce bug
# Write failing test
uv run pytest tests/test_bug.py

# Fix bug
# ... code changes ...

# Verify fix
uv run pytest tests/test_bug.py

# Commit
git add .
git commit -m "fix: resolve issue description"
```

### 3. Code Review Process

1. **Self-Review**: Check your own code
2. **Automated Checks**: Ensure CI/CD passes
3. **Peer Review**: Request review from team
4. **Testing**: Verify on different environments
5. **Documentation**: Update relevant docs

## 📊 Monitoring and Debugging

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uv run python -m src.main
```

### Log Analysis

```bash
# Filter logs by level
grep "ERROR" logs/bot.log

# Monitor job processing
grep "Job" logs/bot.log | tail -f

# Analyze performance
grep "completed" logs/bot.log | awk '{print $NF}' | sort -n
```

### Database Debugging

```bash
# Connect to database
sqlite3 data/ocr.db

# Useful queries
.schema                    # Show table structure
SELECT * FROM jobs;        # View all jobs
SELECT * FROM results;      # View cached results
SELECT status, COUNT(*) FROM jobs GROUP BY status;  # Job statistics
```

### Performance Profiling

```python
# Add to worker.py for profiling
import time
import cProfile

def profile_processing(func):
    """Decorator to profile processing functions."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        profiler.print_stats(sort='cumulative')
        
        end_time = time.time()
        logger.info("Processing completed", duration=end_time - start_time)
        return result
    return wrapper

# Usage
@profile_processing
async def extract_text_from_image(self, image_path: str) -> str:
    # ... existing code ...
```

## 🔌 Extending Functionality

### Adding New File Types

1. **Update utils.py**:

```python
def convert_docx_to_images(docx_path: str) -> list[str]:
    """Convert DOCX to images."""
    # Implementation here
    pass

def convert_file_to_images(file_path: str) -> list[str]:
    """Universal file converter."""
    if file_path.endswith(".pdf"):
        return convert_pdf_to_images(file_path)
    elif file_path.endswith(".docx"):
        return convert_docx_to_images(file_path)
    else:
        return [file_path]  # Assume it's already an image
```

2. **Update worker.py**:

```python
async def process_job(self, job: dict):
    # ... existing code ...
    
    # Use universal converter
    image_paths = await asyncio.to_thread(convert_file_to_images, file_path)
```

### Adding New OCR Providers

```python
# src/ocr_providers.py
class BaseOCRProvider:
    """Base class for OCR providers."""
    
    async def extract_text(self, image_path: str) -> str:
        raise NotImplementedError

class TesseractProvider(BaseOCRProvider):
    """Tesseract OCR provider."""
    
    async def extract_text(self, image_path: str) -> str:
        import pytesseract
        from PIL import Image
        
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)

# Update worker.py to use provider
class OCRWorker:
    def __init__(self, app: Application, worker_id: str, ocr_provider: BaseOCRProvider):
        self.ocr_provider = ocr_provider
```

### Adding Web Interface

```python
# src/web_api.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    """Web API endpoint for OCR processing."""
    # Save file
    # Process with existing worker logic
    # Return results
    pass
```

## 🚀 Performance Optimization

### Database Optimization

```python
# Add indexes for better performance
async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        # ... existing code ...
        
        # Add indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_results_hash ON results(file_hash)")
```

### Memory Management

```python
# Process large files in chunks
async def process_large_image(image_path: str) -> str:
    """Process large images efficiently."""
    from PIL import Image
    
    with Image.open(image_path) as img:
        # Resize if too large
        if img.size[0] > 2000 or img.size[1] > 2000:
            img.thumbnail((2000, 2000))
            # Save to temp and process
```

### Caching Strategy

```python
# Add Redis caching for frequently accessed data
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def get_cached_text_with_redis(file_hash: str) -> Optional[str]:
    """Get cached text with Redis fallback."""
    # Try Redis first
    cached = redis_client.get(f"ocr:{file_hash}")
    if cached:
        return cached.decode('utf-8')
    
    # Fallback to SQLite
    return await get_cached_text(file_hash)
```

## 🔒 Security Considerations

### Input Validation

```python
# Enhanced file validation
def validate_file(file_path: Path, max_size_mb: int = 10) -> bool:
    """Validate uploaded file."""
    # Check file size
    if file_path.stat().st_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"File too large: {max_size_mb}MB max")
    
    # Check file signature
    with open(file_path, 'rb') as f:
        header = f.read(8)
    
    # Validate image signatures
    valid_signatures = {
        b'\xff\xd8\xff': 'jpg',
        b'\x89PNG': 'png',
        b'%PDF': 'pdf'
    }
    
    if not any(header.startswith(sig) for sig in valid_signatures):
        raise ValueError("Invalid file type")
    
    return True
```

### Rate Limiting

```python
# Add rate limiting per user
from collections import defaultdict
import time

user_requests = defaultdict(list)

async def check_rate_limit(user_id: int, max_requests: int = 10, window: int = 60) -> bool:
    """Check if user exceeds rate limit."""
    now = time.time()
    user_requests[user_id] = [
        req_time for req_time in user_requests[user_id] 
        if now - req_time < window
    ]
    
    if len(user_requests[user_id]) >= max_requests:
        return False
    
    user_requests[user_id].append(now)
    return True
```

## 📚 Documentation

### Code Documentation

- **Docstrings**: Google-style for all public functions
- **Type hints**: Required for all function parameters and returns
- **Comments**: Explain complex logic, not obvious code

### API Documentation

```python
# Use OpenAPI/Swagger for web API
from fastapi import FastAPI
from pydantic import BaseModel

class OCRRequest(BaseModel):
    """OCR request model."""
    image_url: str
    language: str = "auto"
    
    class Config:
        schema_extra = {
            "example": {
                "image_url": "https://example.com/image.jpg",
                "language": "en"
            }
        }
```

### README Updates

Keep README.md updated with:
- New features
- Breaking changes
- Installation requirements
- Usage examples

## 🤝 Contributing Guidelines

### Before Contributing

1. **Read** this development guide
2. **Set up** development environment
3. **Run existing tests** to ensure they pass
4. **Create issue** for new features or bug fixes

### Pull Request Process

1. **Fork** repository
2. **Create** feature branch
3. **Make changes** with tests
4. **Ensure** all tests pass
5. **Update** documentation
6. **Submit** pull request

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## 🐛 Common Development Issues

### Import Errors

```bash
# If you get import errors, ensure:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# or run with:
uv run python -m src.main
```

### Database Locks

```bash
# Remove stuck database locks
rm -f data/ocr.db-journal
rm -f data/ocr.db-wal
```

### Test Isolation

```bash
# Use separate test database
TEST_DB_PATH="test_ocr.db" uv run pytest
```

## 📈 Performance Benchmarks

### Target Metrics

- **Image Processing**: < 30 seconds for standard images
- **PDF Processing**: < 60 seconds for 5-page documents
- **Memory Usage**: < 500MB during processing
- **Database Queries**: < 10ms for standard operations
- **API Response**: < 1 second for cached results

### Benchmarking Tools

```python
# Add to tests/test_performance.py
import time
import asyncio

async def benchmark_processing():
    """Benchmark OCR processing performance."""
    start_time = time.time()
    
    # Process test file
    result = await process_test_file()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Processing time: {duration:.2f} seconds")
    assert duration < 30, "Processing too slow"
```

Happy coding! 🚀