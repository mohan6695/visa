#!/usr/bin/env python3
"""
Telegram Chat Bulk Upload Example

This example demonstrates how to use the TelegramUploadService to upload
Telegram chat data to Supabase with optimized bulk operations.

Usage:
    python telegram_upload_example.py --file result.json --chat "My Group Chat"
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add the backend src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

from services.telegram_upload_service import TelegramUploadService
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the Telegram upload example"""
    
    parser = argparse.ArgumentParser(description='Upload Telegram chat data to Supabase')
    parser.add_argument('--file', required=True, help='Path to Telegram export JSON file')
    parser.add_argument('--chat', required=True, help='Name or ID of the chat to process')
    parser.add_argument('--chat-id', help='Optional custom chat ID for the database')
    parser.add_argument('--dry-run', action='store_true', help='Validate without uploading')
    
    args = parser.parse_args()
    
    # Validate inputs
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {args.file}")
        return 1
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.error("Supabase URL and Key must be configured in environment variables")
        logger.error("Set SUPABASE_URL and SUPABASE_KEY environment variables")
        return 1
    
    try:
        # Initialize the upload service
        upload_service = TelegramUploadService()
        
        if args.dry_run:
            logger.info("Dry run mode - validating file structure...")
            chat_data = await upload_service._load_telegram_export(str(file_path), args.chat)
            if not chat_data:
                logger.error(f"Chat '{args.chat}' not found in export")
                return 1
            
            messages = chat_data.get('messages', [])
            recent_msgs, older_msgs = upload_service._split_messages_by_date(messages)
            
            logger.info(f"Validation successful!")
            logger.info(f"Total messages: {len(messages)}")
            logger.info(f"Recent messages (last 30 days): {len(recent_msgs)}")
            logger.info(f"Older messages: {len(older_msgs)}")
            
            # Show sample recent messages
            if recent_msgs:
                logger.info("Sample recent messages:")
                for i, msg in enumerate(recent_msgs[:3]):
                    date = upload_service._parse_telegram_date(msg.get('date'))
                    user = msg.get('from', 'Unknown')
                    text = msg.get('text', '')[:50]
                    logger.info(f"  {i+1}. {date} - {user}: {text}...")
            
            return 0
        
        # Process the Telegram export
        logger.info(f"Starting upload for chat: {args.chat}")
        summary = await upload_service.process_telegram_export(
            file_path=str(file_path),
            chat_name=args.chat,
            chat_id_override=args.chat_id
        )
        
        if "error" in summary:
            logger.error(f"Upload failed: {summary['error']}")
            return 1
        
        # Print summary
        logger.info("=" * 60)
        logger.info("UPLOAD SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Chat ID: {summary['chat_id']}")
        logger.info(f"Chat Name: {summary['chat_name']}")
        logger.info(f"Messages Processed: {summary['total_messages_processed']}")
        logger.info(f"Older Messages: {summary['older_messages_count']}")
        logger.info(f"Summary Uploaded: {summary['summary_uploaded']}")
        logger.info(f"Processing Time: {summary['processing_time']}")
        logger.info("=" * 60)
        
        # Get additional statistics
        stats = await upload_service.get_chat_stats(summary['chat_id'])
        if "error" not in stats:
            logger.info("ADDITIONAL STATISTICS:")
            logger.info(f"  Total Messages in Export: {stats['total_messages']}")
            logger.info(f"  Messages in Database: {stats['stored_messages']}")
            logger.info(f"  Unique Users: {stats['unique_users']}")
            logger.info(f"  Summary Path: {stats['summary_path']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)