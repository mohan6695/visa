from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from datetime import datetime, timedelta
import json
import uuid
import hashlib
import logging
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from ..core.config import settings, telegram_config
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import orjson

logger = logging.getLogger(__name__)

class TelegramUploadService:
    """Optimized service for bulk uploading Telegram chat data to Supabase"""
    
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be configured")
        
        # Configure Supabase client with optimized settings
        client_options = ClientOptions(
            postgrest_client_timeout=telegram_config.POSTGREST_TIMEOUT,
            storage_client_timeout=telegram_config.STORAGE_TIMEOUT,
        )
        
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
            options=client_options
        )
        
        # Configuration from settings
        self.batch_size = telegram_config.BATCH_SIZE
        self.max_concurrent_uploads = telegram_config.MAX_CONCURRENT_UPLOADS
        self.chunk_size = telegram_config.CHUNK_SIZE
        
    async def process_telegram_export(
        self, 
        file_path: str, 
        chat_name: str,
        chat_id_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing Telegram export JSON
        
        Args:
            file_path: Path to the Telegram export JSON file
            chat_name: Name of the chat to process
            chat_id_override: Optional custom chat ID
            
        Returns:
            Processing summary with statistics
        """
        try:
            logger.info(f"Starting Telegram export processing for chat: {chat_name}")
            
            # Step 1: Load and preprocess JSON
            chat_data = await self._load_telegram_export(file_path, chat_name)
            if not chat_data:
                return {"error": f"Chat '{chat_name}' not found in export"}
            
            # Step 2: Split messages by date
            recent_msgs, older_msgs = self._split_messages_by_date(chat_data['messages'])
            
            logger.info(f"Found {len(recent_msgs)} recent messages and {len(older_msgs)} older messages")
            
            # Step 3: Process recent messages (last 30 days)
            chat_info = await self._process_recent_messages(
                chat_data, recent_msgs, chat_id_override
            )
            
            # Step 4: Upload older messages summary to Storage
            if older_msgs:
                summary_path = await self._upload_older_messages_summary(
                    chat_info['chat_id'], older_msgs
                )
                await self._update_chat_summary_path(chat_info['id'], summary_path)
            
            # Step 5: Generate processing summary
            summary = {
                "chat_id": chat_info['chat_id'],
                "chat_name": chat_data.get('name', chat_name),
                "total_messages_processed": len(recent_msgs),
                "older_messages_count": len(older_msgs),
                "summary_uploaded": bool(older_msgs),
                "processing_time": datetime.now().isoformat()
            }
            
            logger.info(f"Telegram export processing completed: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error processing Telegram export: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _load_telegram_export(self, file_path: str, chat_name: str) -> Optional[Dict[str, Any]]:
        """Load Telegram export JSON with streaming support for large files"""
        try:
            logger.info(f"Loading Telegram export from: {file_path}")
            
            # For very large files, we'll use streaming JSON parsing
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = orjson.loads(content)
            
            # Find the target chat
            chats = data.get('chats', {}).get('list', [])
            
            target_chat = None
            for chat in chats:
                if chat.get('name') == chat_name or chat.get('id') == chat_name:
                    target_chat = chat
                    break
            
            if not target_chat:
                logger.error(f"Chat '{chat_name}' not found in export")
                return None
            
            logger.info(f"Found target chat: {target_chat.get('name')} with {len(target_chat.get('messages', []))} messages")
            return target_chat
            
        except Exception as e:
            logger.error(f"Error loading Telegram export: {e}")
            return None
    
    def _split_messages_by_date(self, messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split messages into recent and older based on configuration"""
        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=telegram_config.RECENT_DAYS_THRESHOLD)
            
            recent_msgs = []
            older_msgs = []
            
            for msg in messages:
                msg_date = self._parse_telegram_date(msg.get('date'))
                if msg_date and msg_date >= cutoff_date:
                    recent_msgs.append(msg)
                else:
                    older_msgs.append(msg)
            
            logger.info(f"Split messages: {len(recent_msgs)} recent, {len(older_msgs)} older")
            return recent_msgs, older_msgs
            
        except Exception as e:
            logger.error(f"Error splitting messages by date: {e}")
            return messages, []
    
    def _parse_telegram_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Telegram date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Telegram date format: "2024-11-24 15:30:45"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None
    
    async def _process_recent_messages(
        self, 
        chat_data: Dict[str, Any], 
        recent_msgs: List[Dict[str, Any]], 
        chat_id_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process recent messages with bulk insert optimization"""
        try:
            # Step 1: Create or get chat record
            chat_info = await self._get_or_create_chat(chat_data, chat_id_override)
            
            # Step 2: Generate user aliases for pseudonymization
            user_aliases = self._generate_user_aliases(recent_msgs)
            await self._save_user_aliases(chat_info['id'], user_aliases)
            
            # Step 3: Transform messages for bulk insert
            transformed_msgs = self._transform_messages_for_insert(
                chat_info['id'], recent_msgs, user_aliases
            )
            
            # Step 4: Bulk insert messages with batching
            await self._bulk_insert_messages(transformed_msgs)
            
            logger.info(f"Successfully processed {len(recent_msgs)} recent messages for chat {chat_info['chat_id']}")
            return chat_info
            
        except Exception as e:
            logger.error(f"Error processing recent messages: {e}", exc_info=True)
            raise
    
    async def _get_or_create_chat(
        self, 
        chat_data: Dict[str, Any], 
        chat_id_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing chat or create new one"""
        try:
            chat_id = chat_id_override or str(chat_data.get('id', uuid.uuid4()))
            
            # Try to find existing chat
            result = self.supabase.table('telegram_chats').select('*').eq('chat_id', chat_id).execute()
            
            if result.data:
                return result.data[0]
            
            # Create new chat
            chat_record = {
                'chat_id': chat_id,
                'chat_name': chat_data.get('name'),
                'chat_type': chat_data.get('type', 'unknown'),
                'total_messages': len(chat_data.get('messages', []))
            }
            
            result = self.supabase.table('telegram_chats').insert(chat_record).execute()
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error getting or creating chat: {e}")
            raise
    
    def _generate_user_aliases(self, messages: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        """Generate pseudonymous aliases for users"""
        try:
            user_aliases = {}
            
            for msg in messages:
                # Extract user information
                user_id = str(msg.get('from_id', ''))
                username = msg.get('from', '')
                
                if user_id and user_id not in user_aliases:
                    # Generate pseudonymous alias
                    alias = f"user_{self._generate_short_hash(user_id)}"
                    
                    user_aliases[user_id] = {
                        'original_user_id': user_id,
                        'original_username': username,
                        'alias': alias
                    }
            
            logger.info(f"Generated aliases for {len(user_aliases)} users")
            return user_aliases
            
        except Exception as e:
            logger.error(f"Error generating user aliases: {e}")
            return {}
    
    def _generate_short_hash(self, input_str: str, length: int = None) -> str:
        """Generate a short hash for pseudonymization"""
        if length is None:
            length = telegram_config.ALIAS_LENGTH
        return hashlib.md5(input_str.encode()).hexdigest()[:length]
    
    async def _save_user_aliases(self, chat_id: int, user_aliases: Dict[str, Dict[str, str]]):
        """Save user aliases to database"""
        try:
            alias_records = []
            for user_id, alias_info in user_aliases.items():
                alias_records.append({
                    'chat_id': chat_id,
                    'original_user_id': alias_info['original_user_id'],
                    'original_username': alias_info['original_username'],
                    'alias': alias_info['alias']
                })
            
            if alias_records:
                # Use upsert to avoid duplicates
                self.supabase.table('telegram_user_aliases').upsert(alias_records).execute()
                logger.info(f"Saved {len(alias_records)} user aliases")
                
        except Exception as e:
            logger.error(f"Error saving user aliases: {e}")
            raise
    
    def _transform_messages_for_insert(
        self, 
        chat_id: int, 
        messages: List[Dict[str, Any]], 
        user_aliases: Dict[str, Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Transform Telegram messages for database insertion"""
        try:
            transformed = []
            
            for msg in messages:
                # Parse date
                sent_at = self._parse_telegram_date(msg.get('date'))
                if not sent_at:
                    continue
                
                # Get user alias
                user_id = str(msg.get('from_id', ''))
                sender_alias = user_aliases.get(user_id, {}).get('alias', f"user_{self._generate_short_hash(user_id)}")
                
                # Extract content
                text_content = msg.get('text', '')
                if isinstance(text_content, list):
                    # Telegram sometimes stores text as array of segments
                    text_content = ''.join([str(segment) if isinstance(segment, str) else str(segment.get('text', '')) for segment in text_content])
                
                # Determine message type
                message_type = msg.get('type', 'text')
                if 'photo' in msg:
                    message_type = 'photo'
                elif 'file' in msg:
                    message_type = 'file'
                elif 'sticker' in msg:
                    message_type = 'sticker'
                
                # Build message record
                message_record = {
                    'chat_id': chat_id,
                    'msg_id': str(msg.get('id', uuid.uuid4())),
                    'sender_alias': sender_alias,
                    'sender_id': user_id,
                    'message_type': message_type,
                    'text_content': text_content[:telegram_config.MAX_TEXT_CONTENT_LENGTH],
                    'raw_data': msg,  # Store full raw data in JSONB
                    'sent_at': sent_at.isoformat()
                }
                
                transformed.append(message_record)
            
            logger.info(f"Transformed {len(transformed)} messages for insertion")
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming messages: {e}")
            return []
    
    async def _bulk_insert_messages(self, messages: List[Dict[str, Any]]):
        """Perform optimized bulk insert with batching"""
        try:
            if not messages:
                logger.info("No messages to insert")
                return
            
            # Split into batches
            batches = [messages[i:i + self.batch_size] for i in range(0, len(messages), self.batch_size)]
            
            logger.info(f"Inserting {len(messages)} messages in {len(batches)} batches of {self.batch_size}")
            
            # Process batches sequentially to avoid overwhelming the database
            for i, batch in enumerate(batches):
                try:
                    # Use insert with multiple records
                    result = self.supabase.table('telegram_messages').insert(batch).execute()
                    
                    logger.info(f"Batch {i+1}/{len(batches)} inserted successfully: {len(result.data)} messages")
                    
                    # Add small delay between batches to prevent rate limiting
                    if i < len(batches) - 1:
                        await asyncio.sleep(telegram_config.BATCH_DELAY_SECONDS)
                        
                except Exception as e:
                    logger.error(f"Error inserting batch {i+1}: {e}")
                    # Continue with next batch instead of failing completely
                    continue
            
            logger.info("Bulk insert completed")
            
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            raise
    
    async def _upload_older_messages_summary(
        self, 
        chat_id: str, 
        older_msgs: List[Dict[str, Any]]
    ) -> str:
        """Upload older messages summary to Supabase Storage"""
        try:
            # Generate summary statistics
            summary = self._generate_messages_summary(older_msgs)
            
            # Create JSON content
            summary_content = {
                'chat_id': chat_id,
                'summary_range': {
                    'from': summary['date_range']['start'],
                    'to': summary['date_range']['end']
                },
                'total_messages': summary['total_messages'],
                'participants': summary['participants'],
                'message_types': summary['message_types'],
                'date_range': summary['date_range'],
                'buckets': summary['buckets']
            }
            
            # Serialize to JSON string
            json_content = orjson.dumps(summary_content, option=orjson.OPT_INDENT_2).decode('utf-8')
            
            # Generate storage path using configuration
            timestamp = datetime.now().strftime("%Y-%m-%d")
            storage_path = f"{telegram_config.STORAGE_BUCKET}/{chat_id}/{telegram_config.SUMMARY_FILE_PREFIX}_{timestamp}.json"
            
            # Upload to storage
            result = self.supabase.storage.from_(telegram_config.STORAGE_BUCKET).upload(
                storage_path,
                json_content,
                file_options={"content-type": "application/json"}
            )
            
            logger.info(f"Uploaded summary to storage: {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Error uploading summary to storage: {e}")
            raise
    
    def _generate_messages_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for older messages"""
        try:
            if not messages:
                return {
                    'total_messages': 0,
                    'participants': [],
                    'message_types': {},
                    'date_range': {'start': None, 'end': None},
                    'buckets': []
                }
            
            # Count message types
            message_types = {}
            participants = set()
            dates = []
            
            for msg in messages:
                msg_type = msg.get('type', 'unknown')
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
                
                user_id = msg.get('from_id', '')
                if user_id:
                    participants.add(str(user_id))
                
                msg_date = self._parse_telegram_date(msg.get('date'))
                if msg_date:
                    dates.append(msg_date)
            
            # Calculate date range
            date_range = {
                'start': min(dates).isoformat() if dates else None,
                'end': max(dates).isoformat() if dates else None
            }
            
            # Create monthly buckets
            buckets = self._create_monthly_buckets(messages)
            
            return {
                'total_messages': len(messages),
                'participants': list(participants),
                'message_types': message_types,
                'date_range': date_range,
                'buckets': buckets
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
    
    def _create_monthly_buckets(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create monthly message count buckets"""
        try:
            buckets = {}
            
            for msg in messages:
                msg_date = self._parse_telegram_date(msg.get('date'))
                if msg_date:
                    month_key = msg_date.strftime("%Y-%m")
                    if month_key not in buckets:
                        buckets[month_key] = 0
                    buckets[month_key] += 1
            
            # Convert to sorted list
            bucket_list = [
                {'month': month, 'count': count}
                for month, count in sorted(buckets.items())
            ]
            
            return bucket_list
            
        except Exception as e:
            logger.error(f"Error creating monthly buckets: {e}")
            return []
    
    async def _update_chat_summary_path(self, chat_db_id: int, summary_path: str):
        """Update chat record with summary path"""
        try:
            self.supabase.table('telegram_chats').update({
                'summary_uploaded': True,
                'summary_path': summary_path
            }).eq('id', chat_db_id).execute()
            
            logger.info(f"Updated chat {chat_db_id} with summary path: {summary_path}")
            
        except Exception as e:
            logger.error(f"Error updating chat summary path: {e}")
    
    async def get_chat_stats(self, chat_id: str) -> Dict[str, Any]:
        """Get statistics for a specific chat"""
        try:
            # Get chat info
            chat_result = self.supabase.table('telegram_chats').select('*').eq('chat_id', chat_id).execute()
            
            if not chat_result.data:
                return {"error": f"Chat {chat_id} not found"}
            
            chat_info = chat_result.data[0]
            
            # Get message stats
            msg_result = self.supabase.table('telegram_messages').select(
                'sent_at', count='exact'
            ).eq('chat_id', chat_info['id']).execute()
            
            # Get user stats
            user_result = self.supabase.table('telegram_user_aliases').select(
                'alias', count='exact'
            ).eq('chat_id', chat_info['id']).execute()
            
            return {
                'chat_id': chat_info['chat_id'],
                'chat_name': chat_info['chat_name'],
                'total_messages': chat_info['total_messages'],
                'stored_messages': msg_result.count or 0,
                'unique_users': user_result.count or 0,
                'summary_uploaded': chat_info['summary_uploaded'],
                'summary_path': chat_info['summary_path'],
                'created_at': chat_info['created_at']
            }
            
        except Exception as e:
            logger.error(f"Error getting chat stats: {e}")
            return {"error": str(e)}