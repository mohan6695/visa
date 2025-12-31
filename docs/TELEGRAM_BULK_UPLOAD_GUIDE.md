# Telegram Chat Bulk Upload to Supabase

This guide explains how to efficiently upload Telegram chat data to Supabase using the optimized bulk upload system.

## Overview

The Telegram bulk upload system provides:

- **Optimized bulk inserts** with configurable batch sizes (default: 1000 messages per batch)
- **Username pseudonymization** for privacy protection
- **Date-based filtering** (last 30 days to database, older to storage)
- **Streaming JSON processing** for large export files
- **Comprehensive error handling** and logging
- **Supabase Storage integration** for older message summaries

## Architecture

```
Telegram Export JSON
    ↓
JSON Preprocessing & Date Filtering
    ↓
Recent Messages (Last 30 Days) → Bulk Insert → Supabase Database
    ↓
Older Messages → Summary Generation → Supabase Storage
    ↓
User Aliases → Pseudonymization → Database
```

## Database Schema

### Tables Created

1. **telegram_chats** - Chat metadata and statistics
2. **telegram_messages** - Recent messages with full-text search and embeddings
3. **telegram_user_aliases** - Pseudonymous user mapping

### Key Features

- **Row Level Security (RLS)** enabled for data protection
- **GIN indexes** for fast full-text search
- **Vector indexes** for semantic search (if using embeddings)
- **Automatic statistics** tracking message counts

## Configuration

### Environment Variables

```bash
# Required
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Optional (uses defaults if not set)
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Upload Configuration

```python
# In backend/src/core/config.py
class TelegramUploadConfig:
    BATCH_SIZE: int = 1000                    # Messages per bulk insert
    MAX_CONCURRENT_UPLOADS: int = 5           # Concurrent operations limit
    CHUNK_SIZE: int = 50000                   # JSON streaming chunk size
    RECENT_DAYS_THRESHOLD: int = 30           # Days threshold for recent messages
    MAX_TEXT_CONTENT_LENGTH: int = 10000      # Text content size limit
    ALIAS_LENGTH: int = 8                     # User alias length
    STORAGE_BUCKET: str = "telegram-archives" # Supabase Storage bucket
    SUMMARY_FILE_PREFIX: str = "summary_before"
    BATCH_DELAY_SECONDS: float = 0.1          # Delay between batches
    POSTGREST_TIMEOUT: int = 60               # Bulk operation timeout
    STORAGE_TIMEOUT: int = 120                # Storage upload timeout
```

## Usage

### 1. Prepare Telegram Export

Export your Telegram chat as JSON:

1. Open Telegram Desktop
2. Go to Settings → Advanced → Export Telegram data
3. Select "Machine-readable JSON"
4. Choose your chat and export

### 2. Run Migration

Apply the database schema:

```bash
# Run the migration
psql -d your_database -f supabase_migrations/002_telegram_chat_schema.sql
```

### 3. Upload Data

#### Using the Example Script

```bash
# Basic upload
python telegram_upload_example.py --file result.json --chat "My Group Chat"

# With custom chat ID
python telegram_upload_example.py --file result.json --chat "My Group Chat" --chat-id "custom_chat_123"

# Dry run to validate
python telegram_upload_example.py --file result.json --chat "My Group Chat" --dry-run
```

#### Using the Service Directly

```python
from services.telegram_upload_service import TelegramUploadService

async def upload_chat():
    service = TelegramUploadService()
    
    summary = await service.process_telegram_export(
        file_path="result.json",
        chat_name="My Group Chat",
        chat_id_override="custom_id"
    )
    
    print(f"Uploaded {summary['total_messages_processed']} messages")
    print(f"Summary uploaded: {summary['summary_uploaded']}")

# Run the upload
import asyncio
asyncio.run(upload_chat())
```

## Performance Optimization

### Batch Size Tuning

- **Small datasets (< 10K messages)**: Use batch size 500-1000
- **Medium datasets (10K-100K)**: Use batch size 1000-2000
- **Large datasets (> 100K)**: Use batch size 2000-5000

### Memory Management

For very large files (> 1GB), the system uses:

- **Streaming JSON parsing** with `orjson`
- **Chunked file reading** with `aiofiles`
- **Batched database operations** to prevent memory overflow

### Network Optimization

- **Connection pooling** with configurable timeouts
- **Concurrent upload limits** to prevent rate limiting
- **Automatic retry logic** for failed batches

## Data Processing

### Username Pseudonymization

```python
# Original data
{
    "from_id": "user12345",
    "from": "John Doe",
    "text": "Hello everyone!"
}

# Processed data
{
    "sender_alias": "user_a1b2c3d4",
    "sender_id": "user12345",  # Original ID stored separately
    "text_content": "Hello everyone!"
}
```

### Date Filtering

- **Recent messages**: Last 30 days (configurable) → Database
- **Older messages**: Beyond 30 days → Storage summary

### Message Types

The system handles various Telegram message types:

- **Text messages** → `text_content` field
- **Photos** → `message_type: 'photo'`
- **Files** → `message_type: 'file'`
- **Stickers** → `message_type: 'sticker'`
- **System messages** → `message_type: 'service'`

## Storage Structure

### Database Storage

```
telegram_chats/
├── chat_id: unique identifier
├── chat_name: display name
├── total_messages: total count from export
├── recent_messages_count: recent message count
└── summary_path: path to older messages summary

telegram_messages/
├── chat_id: foreign key to telegram_chats
├── msg_id: unique message ID
├── sender_alias: pseudonymous user identifier
├── message_type: text/photo/file/etc.
├── text_content: extracted text content
├── raw_data: full Telegram message JSON
├── sent_at: message timestamp
└── search_vector: for full-text search

telegram_user_aliases/
├── chat_id: foreign key
├── original_user_id: Telegram user ID
├── original_username: Telegram username
└── alias: generated pseudonym
```

### Storage Bucket Structure

```
telegram-archives/
├── chat_id_1/
│   └── summary_before_2024-11-24.json
├── chat_id_2/
│   └── summary_before_2024-11-24.json
└── ...
```

### Summary File Format

```json
{
  "chat_id": "telegram_chat_123",
  "summary_range": {
    "from": "2024-01-01T00:00:00",
    "to": "2024-10-24T23:59:59"
  },
  "total_messages": 15000,
  "participants": ["user_abc123", "user_def456"],
  "message_types": {
    "text": 12000,
    "photo": 2500,
    "file": 500
  },
  "date_range": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-10-24T23:59:59"
  },
  "buckets": [
    {"month": "2024-01", "count": 1200},
    {"month": "2024-02", "count": 1100},
    // ... monthly breakdown
  ]
}
```

## Monitoring and Troubleshooting

### Logging

The system provides detailed logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Monitor upload progress
logger.info("Starting Telegram export processing for chat: My Group Chat")
logger.info("Found 15000 recent messages and 50000 older messages")
logger.info("Batch 1/15 inserted successfully: 1000 messages")
```

### Common Issues

#### 1. Large File Memory Issues

**Problem**: Out of memory when processing large exports

**Solution**: The system automatically uses streaming for files > 100MB

#### 2. Rate Limiting

**Problem**: Supabase rate limiting during bulk inserts

**Solution**: System includes automatic delays between batches (configurable)

#### 3. Authentication Errors

**Problem**: "Invalid API key" or "Unauthorized"

**Solution**: Verify `SUPABASE_URL` and `SUPABASE_KEY` environment variables

#### 4. Database Connection Issues

**Problem**: Connection timeouts during bulk operations

**Solution**: Increase `POSTGREST_TIMEOUT` in configuration

### Performance Metrics

Monitor these key metrics:

- **Upload speed**: Messages per second
- **Memory usage**: Peak memory during processing
- **Database performance**: Insert time per batch
- **Storage usage**: Summary file sizes

## Security Considerations

### Data Privacy

- **Pseudonymization**: User IDs are replaced with random aliases
- **Separation**: Original user data stored separately from messages
- **Access Control**: RLS policies restrict data access

### Supabase Security

- **RLS Policies**: Row-level security on all tables
- **API Keys**: Use service keys for server-side operations
- **Storage Permissions**: Configure bucket policies appropriately

## Integration with Existing System

The Telegram upload service integrates with the existing visa community platform:

1. **Database Schema**: Compatible with existing Supabase setup
2. **Authentication**: Uses existing Supabase auth system
3. **Storage**: Integrates with existing Supabase Storage
4. **API**: Can be exposed through existing FastAPI endpoints

## Future Enhancements

Potential improvements:

1. **Parallel Processing**: Multi-threaded message processing
2. **Compression**: Compress large summary files
3. **Incremental Uploads**: Resume interrupted uploads
4. **Analytics**: Generate usage statistics and insights
5. **Web Interface**: GUI for upload management

## Support

For issues or questions:

1. Check the logging output for detailed error information
2. Verify your Supabase credentials and permissions
3. Ensure the database schema is properly applied
4. Test with smaller files first to validate the setup