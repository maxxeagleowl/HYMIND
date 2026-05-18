# Failure Pattern Registry

---

## FP-001

### Problem
NewsAPI returned HTTP 429

### Cause
API rate limit exceeded

### Detection
Response status code 429

### Mitigation
- Retry with exponential backoff
- Fallback to RSS feeds
- Log occurrence

### Prevention
Reduce polling frequency

---

## FP-002

### Problem
Malformed RSS XML

### Cause
Invalid feed structure

### Detection
XML parser exception

### Mitigation
Skip source
Log parsing error
Continue workflow