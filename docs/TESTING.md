# Testing Guide

This comprehensive guide helps you test Spermophilus OCR bot thoroughly before production use.

## 🧪 Test Environment Setup

### Prerequisites

- Completed [Setup Guide](SETUP.md)
- LM Studio running with a vision model
- Test files ready (images and PDFs)
- Telegram access with bot configured

### Test Files Preparation

Create a `test_files/` directory with sample files:

```bash
mkdir test_files
cd test_files
```

#### Required Test Files

1. **Simple Text Image** (`simple_text.jpg`)
   - Clear, readable text
   - Good lighting
   - Multiple lines

2. **Handwritten Text** (`handwritten.jpg`)
   - Mixed handwriting styles
   - Various sizes

3. **Document with Tables** (`document_table.jpg`)
   - Structured data
   - Multiple columns

4. **Multi-page PDF** (`multi_page.pdf`)
   - 3-5 pages
   - Mixed content (text + images)

5. **Scanned Document** (`scanned_doc.pdf`)
   - Real-world scan
   - Some noise/imperfections

6. **Large File** (`large_image.jpg`)
   - High resolution
   - 2MB+ size

## 🚀 Quick Smoke Test

### 1. Bot Responsiveness Test

```bash
# Start bot in debug mode
LOG_LEVEL=DEBUG uv run python -m src.main
```

**In Telegram:**
1. Send `/start` to your bot
2. **Expected**: "👋 Send me an Image or PDF to extract text."
3. Send any message (text only)
4. **Expected**: No response (bot ignores text)

### 2. Basic OCR Test

**Steps:**
1. Send `simple_text.jpg` to bot
2. **Expected Response**: "⏳ Queued for processing..."
3. **Wait 10-30 seconds**
4. **Expected Response**: "✅ OCR Result:" followed by extracted text

**Success Indicators:**
- Bot acknowledges receipt immediately
- Processing completes without errors
- Extracted text matches source image
- No error messages in logs

## 🔍 Functional Testing

### Test Case 1: Image Processing

#### Test 1.1: Standard JPEG

```bash
# Test with clear text image
# File: simple_text.jpg
```

**Expected Results:**
- Processing time: < 30 seconds
- Accuracy: > 95% text extraction
- Response format: HTML with proper formatting

#### Test 1.2: PNG Format

```bash
# Convert test image to PNG
convert simple_text.jpg simple_text.png
```

**Expected Results:**
- Same accuracy as JPEG
- No format-related errors

#### Test 1.3: Large Image

```bash
# Check file size
ls -lh large_image.jpg  # Should be > 2MB
```

**Expected Results:**
- Bot handles large files without crashing
- Processing may take longer (up to 60 seconds)
- Memory usage remains stable

### Test Case 2: PDF Processing

#### Test 2.1: Single Page PDF

```bash
# Create single page PDF
convert simple_text.jpg single_page.pdf
```

**Expected Results:**
- PDF converted to image successfully
- Text extracted accurately
- Temporary files cleaned up

#### Test 2.2: Multi-page PDF

```bash
# Send multi_page.pdf (3-5 pages)
```

**Expected Results:**
- All pages processed
- Text separated by "--- Page Break ---"
- Processing time scales with page count

#### Test 2.3: Scanned Document

```bash
# Send scanned_doc.pdf
```

**Expected Results:**
- Handles lower quality scans
- Reasonable accuracy (> 80%)
- No crashes on poor quality input

### Test Case 3: Error Handling

#### Test 3.1: Unsupported File Type

```bash
# Send a .txt file
echo "test" > test.txt
# Send test.txt to bot
```

**Expected Results:**
- Bot ignores the file
- No error responses
- Logs show file type filtering

#### Test 3.2: Corrupted File

```bash
# Create corrupted image
echo "corrupted" > fake.jpg
# Send fake.jpg to bot
```

**Expected Results:**
- Graceful error handling
- User receives error message
- Bot continues functioning

#### Test 3.3: Empty File

```bash
# Create empty file
touch empty.jpg
# Send empty.jpg to bot
```

**Expected Results:**
- Error handling without crash
- Appropriate error message

## 🔄 Performance Testing

### Test 4: Concurrent Processing

#### Test 4.1: Multiple Files

```bash
# Send 3 different images rapidly
# Within 10 seconds, send:
# - simple_text.jpg
# - handwritten.jpg  
# - document_table.jpg
```

**Expected Results:**
- All files queued successfully
- Processed sequentially without conflicts
- No job duplication

#### Test 4.2: Duplicate Files

```bash
# Send same file twice
# Send simple_text.jpg
# Wait for completion
# Send simple_text.jpg again
```

**Expected Results:**
- Second request returns cached result
- Response includes "(⚡ Cached Result)"
- No reprocessing occurs

### Test 5: Resource Usage

#### Monitor System Resources

```bash
# In one terminal, monitor resources
htop  # or top

# In another, run bot
LOG_LEVEL=INFO uv run python -m src.main

# Send test files and observe:
# - CPU usage during processing
# - Memory consumption
# - Disk I/O
```

**Expected Results:**
- CPU spikes only during processing
- Memory usage stable (< 500MB)
- Temporary files cleaned up

## 🛡️ Security Testing

### Test 6: Access Control

#### Test 6.1: Unauthorized User

1. **Get friend's Telegram ID** (or use second account)
2. **Don't add** to `ALLOWED_USER_IDS`
3. **Send file** from unauthorized account

**Expected Results:**
- Bot ignores the message
- No response sent
- Log entry: "Unauthorized access attempt"

#### Test 6.2: Empty User List

```bash
# Edit .env
ALLOWED_USER_IDS=

# Restart bot
# Try to send file
```

**Expected Results:**
- All requests rejected
- No processing occurs

### Test 7: Input Validation

#### Test 7.1: Malicious Filenames

```bash
# Create file with special characters
touch "file;rm -rf /.jpg"
# Send to bot
```

**Expected Results:**
- Filename sanitized
- No command execution
- Safe processing

#### Test 7.2: Oversized File

```bash
# Create very large file (>10MB)
dd if=/dev/zero of=huge.jpg bs=1M count=15
# Send to bot
```

**Expected Results:**
- Telegram blocks large files
- Or bot handles gracefully
- No memory exhaustion

## 📊 Accuracy Testing

### Test 8: OCR Quality

#### Test 8.1: Text Accuracy

**Method:**
1. Send test image with known text
2. Compare extracted text with original
3. Calculate accuracy percentage

```python
# Simple accuracy test
original = "The quick brown fox jumps over the lazy dog"
extracted = "The quick brown fox jumps over the lazy dog"  # From bot

accuracy = sum(1 for a, b in zip(original, extracted) if a == b) / len(original) * 100
print(f"Accuracy: {accuracy:.2f}%")
```

**Expected Results:**
- Clear text: > 95% accuracy
- Handwritten: > 80% accuracy
- Scanned docs: > 85% accuracy

#### Test 8.2: Special Characters

**Test with:**
- Numbers and symbols
- Currency signs ($, €, £)
- Mathematical expressions
- Foreign characters

**Expected Results:**
- Most special characters preserved
- Unicode support working
- No character encoding issues

## 🔧 Integration Testing

### Test 9: LM Studio Integration

#### Test 9.1: API Health Check

```bash
# Test API directly
curl http://localhost:1234/v1/models
```

#### Test 9.2: Model Unavailable

```bash
# Stop LM Studio
# Send image to bot
```

**Expected Results:**
- Bot detects API unavailability
- Logs: "OCR API unavailable. Waiting..."
- Retries every 10 seconds
- Resumes when API returns

#### Test 9.3: Model Switch

```bash
# Change model in LM Studio
# Send test image
```

**Expected Results:**
- Bot adapts to new model
- No configuration changes needed
- May affect accuracy/processing time

### Test 10: Database Operations

#### Test 10.1: Database Persistence

```bash
# Process a file
# Stop bot
# Restart bot
# Send same file again
```

**Expected Results:**
- Cache persists across restarts
- Cached result returned immediately

#### Test 10.2: Database Corruption

```bash
# Corrupt database file
echo "corrupted" > data/ocr.db
# Start bot
```

**Expected Results:**
- Database recreated automatically
- No data loss (fresh start)
- Bot continues functioning

## 📝 Test Results Template

Use this template to track your test results:

```markdown
# Test Results - [Date]

## Environment
- OS: [Linux/macOS/Windows]
- Python: [version]
- LM Studio Model: [model name]
- Bot Token: [working/not working]

## Smoke Test
- [ ] Bot starts successfully
- [ ] Responds to /start
- [ ] Processes basic image

## Functional Tests
- [ ] Standard JPEG processing
- [ ] PNG support
- [ ] Large file handling
- [ ] Single page PDF
- [ ] Multi-page PDF
- [ ] Scanned document
- [ ] Unsupported file handling
- [ ] Corrupted file handling
- [ ] Empty file handling

## Performance Tests
- [ ] Concurrent processing
- [ ] Duplicate file caching
- [ ] Resource usage within limits

## Security Tests
- [ ] Unauthorized user blocking
- [ ] Input validation
- [ ] Filename sanitization

## Accuracy Tests
- [ ] Clear text accuracy >95%
- [ ] Handwritten text accuracy >80%
- [ ] Special character support

## Integration Tests
- [ ] LM Studio API connectivity
- [ ] API failure handling
- [ ] Database persistence

## Issues Found
[Document any issues discovered]

## Overall Status
[READY FOR PRODUCTION / NEEDS FIXES]
```

## 🚨 Common Test Failures

### Issue 1: LM Studio Connection Failed

**Symptoms:**
- "OCR API unavailable" in logs
- No response to image uploads

**Solutions:**
```bash
# Check LM Studio is running
curl http://localhost:1234/v1/models

# Verify model is loaded
# Check LM Studio UI

# Restart LM Studio server
# Stop and restart server in LM Studio
```

### Issue 2: PDF Processing Fails

**Symptoms:**
- Error on PDF uploads
- "PDF Conversion failed" in logs

**Solutions:**
```bash
# Install poppler-utils
sudo apt install poppler-utils  # Linux
brew install poppler  # macOS

# Check PDF file validity
file test.pdf
pdfinfo test.pdf
```

### Issue 3: Database Locked

**Symptoms:**
- "database is locked" errors
- Jobs not processing

**Solutions:**
```bash
# Check for other bot instances
ps aux | grep python

# Remove lock file
rm -f data/ocr.db-journal

# Restart bot
```

### Issue 4: Memory Issues

**Symptoms:**
- Bot crashes on large files
- System becomes unresponsive

**Solutions:**
```bash
# Monitor memory usage
htop

# Limit concurrent processing
# Process one file at a time

# Increase system swap if needed
```

## ✅ Success Criteria

Your bot is ready for production when:

- [x] All smoke tests pass
- [x] Functional tests complete with >90% success rate
- [x] Performance within acceptable limits
- [x] Security measures working correctly
- [x] OCR accuracy meets requirements
- [x] Integration with LM Studio stable
- [x] Database operations reliable
- [x] Error handling graceful
- [x] Resource usage predictable

## 🔄 Continuous Testing

For production deployment:

1. **Automated Testing**: Set up test scripts
2. **Monitoring**: Log analysis and alerts
3. **Health Checks**: Regular bot status verification
4. **Performance Metrics**: Track processing times and accuracy
5. **User Feedback**: Monitor user-reported issues

## 📞 Getting Help

If tests fail:

1. **Check logs** with `LOG_LEVEL=DEBUG`
2. **Review** this guide's troubleshooting sections
3. **Search** GitHub issues for similar problems
4. **Create** new issue with detailed test results
5. **Include** environment details and error logs

Happy testing! 🧪