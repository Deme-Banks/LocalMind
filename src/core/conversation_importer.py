"""
Conversation Importer - imports conversations from other tools and formats
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConversationImporter:
    """Imports conversations from various formats and tools"""
    
    def __init__(self):
        """Initialize conversation importer"""
        pass
    
    def import_from_file(self, file_path: str, format: Optional[str] = None) -> Dict[str, Any]:
        """
        Import conversation from a file
        
        Args:
            file_path: Path to the file to import
            format: Optional format hint (auto-detect if not provided)
            
        Returns:
            Dictionary with conversation data
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect format if not provided
        if format is None:
            format = self._detect_format(path)
        
        # Read file
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse based on format
        if format == 'json':
            return self._import_json(content)
        elif format == 'markdown':
            return self._import_markdown(content)
        elif format == 'txt':
            return self._import_text(content)
        elif format == 'openai':
            return self._import_openai_format(content)
        elif format == 'anthropic':
            return self._import_anthropic_format(content)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_from_string(self, content: str, format: str) -> Dict[str, Any]:
        """
        Import conversation from a string
        
        Args:
            content: String content to import
            format: Format type (json, markdown, txt, openai, anthropic, auto)
            
        Returns:
            Dictionary with conversation data
        """
        # Auto-detect format if needed
        if format == 'auto':
            format = self._detect_format_from_content(content)
        
        if format == 'json':
            return self._import_json(content)
        elif format == 'markdown':
            return self._import_markdown(content)
        elif format == 'txt':
            return self._import_text(content)
        elif format == 'openai':
            return self._import_openai_format(content)
        elif format == 'anthropic':
            return self._import_anthropic_format(content)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _detect_format_from_content(self, content: str) -> str:
        """Auto-detect format from content"""
        content_stripped = content.strip()
        
        # Check for JSON
        if content_stripped.startswith('{') or content_stripped.startswith('['):
            try:
                data = json.loads(content)
                if isinstance(data, list) and len(data) > 0:
                    if 'role' in data[0] and 'content' in data[0]:
                        if 'function_call' in data[0] or 'tool_calls' in data[0]:
                            return 'openai'
                        return 'json'
                if isinstance(data, dict):
                    if 'messages' in data:
                        # Check if it's Anthropic format
                        if isinstance(data.get('messages'), list) and len(data.get('messages', [])) > 0:
                            first_msg = data['messages'][0]
                            if isinstance(first_msg.get('content'), list):
                                return 'anthropic'
                        return 'json'
            except:
                pass
        
        # Check for Markdown
        if content_stripped.startswith('#'):
            return 'markdown'
        
        # Default to text
        return 'txt'
    
    def _detect_format(self, path: Path) -> str:
        """Auto-detect file format from extension and content"""
        ext = path.suffix.lower()
        
        if ext == '.json':
            # Try to detect specific JSON formats
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        # Check for OpenAI format
                        if 'role' in data[0] and 'content' in data[0]:
                            if 'function_call' in data[0] or 'tool_calls' in data[0]:
                                return 'openai'
                            return 'json'
                    # Check for Anthropic format
                    if 'messages' in data:
                        return 'anthropic'
            except:
                pass
            return 'json'
        elif ext == '.md' or ext == '.markdown':
            return 'markdown'
        elif ext == '.txt':
            return 'txt'
        else:
            # Try to detect from content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1000 chars
                if content.strip().startswith('{'):
                    return 'json'
                elif content.strip().startswith('#'):
                    return 'markdown'
                else:
                    return 'txt'
    
    def _import_json(self, content: str) -> Dict[str, Any]:
        """Import from JSON format"""
        try:
            data = json.loads(content)
            
            # Handle different JSON structures
            if isinstance(data, dict):
                # Check if it's our export format
                if 'messages' in data:
                    return {
                        'model': data.get('model', 'Unknown'),
                        'messages': data['messages'],
                        'conversation_id': data.get('conversationId'),
                        'date': data.get('date')
                    }
                # Check for Anthropic format
                elif 'messages' in data:
                    return self._import_anthropic_format(content)
            elif isinstance(data, list):
                # OpenAI format or simple message list
                messages = []
                for item in data:
                    if isinstance(item, dict):
                        if 'role' in item and 'content' in item:
                            messages.append({
                                'role': item['role'],
                                'content': item['content']
                            })
                
                return {
                    'model': 'Unknown',
                    'messages': messages,
                    'date': None
                }
            
            raise ValueError("Unrecognized JSON format")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def _import_markdown(self, content: str) -> Dict[str, Any]:
        """Import from Markdown format"""
        messages = []
        model = 'Unknown'
        date = None
        
        # Extract metadata from header
        metadata_match = re.search(r'\*\*Model:\*\*\s*(.+?)(?:\n|$)', content)
        if metadata_match:
            model = metadata_match.group(1).strip()
        
        date_match = re.search(r'\*\*Date:\*\*\s*(.+?)(?:\n|$)', content)
        if date_match:
            date = date_match.group(1).strip()
        
        # Extract messages (## User, ## Assistant)
        message_pattern = r'##\s*(User|Assistant)\s*\n\n(.*?)(?=\n##|\n---|$)'
        matches = re.finditer(message_pattern, content, re.DOTALL)
        
        for match in matches:
            role = match.group(1).lower()
            content_text = match.group(2).strip()
            messages.append({
                'role': role,
                'content': content_text
            })
        
        return {
            'model': model,
            'messages': messages,
            'date': date
        }
    
    def _import_text(self, content: str) -> Dict[str, Any]:
        """Import from plain text format"""
        messages = []
        model = 'Unknown'
        
        # Extract metadata
        model_match = re.search(r'Model:\s*(.+?)(?:\n|$)', content)
        if model_match:
            model = model_match.group(1).strip()
        
        # Extract messages (USER:, ASSISTANT:)
        message_pattern = r'(USER|ASSISTANT):\s*\n(.*?)(?=\n(?:USER|ASSISTANT):|$)'
        matches = re.finditer(message_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            role = match.group(1).lower()
            content_text = match.group(2).strip()
            messages.append({
                'role': role,
                'content': content_text
            })
        
        return {
            'model': model,
            'messages': messages,
            'date': None
        }
    
    def _import_openai_format(self, content: str) -> Dict[str, Any]:
        """Import from OpenAI API format"""
        try:
            data = json.loads(content)
            
            messages = []
            model = 'Unknown'
            
            if isinstance(data, list):
                # Direct message list
                for item in data:
                    if 'role' in item and 'content' in item:
                        messages.append({
                            'role': item['role'],
                            'content': item['content']
                        })
            elif isinstance(data, dict):
                # OpenAI API response format
                if 'choices' in data:
                    # API response
                    if 'model' in data:
                        model = data['model']
                    # Extract messages from choices
                    for choice in data['choices']:
                        if 'message' in choice:
                            msg = choice['message']
                            if 'role' in msg and 'content' in msg:
                                messages.append({
                                    'role': msg['role'],
                                    'content': msg['content']
                                })
                elif 'messages' in data:
                    # Chat completion format
                    model = data.get('model', 'Unknown')
                    for item in data['messages']:
                        if 'role' in item and 'content' in item:
                            messages.append({
                                'role': item['role'],
                                'content': item['content']
                            })
            
            return {
                'model': model,
                'messages': messages,
                'date': None
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def _import_anthropic_format(self, content: str) -> Dict[str, Any]:
        """Import from Anthropic API format"""
        try:
            data = json.loads(content)
            
            messages = []
            model = 'Unknown'
            
            if isinstance(data, dict):
                if 'messages' in data:
                    model = data.get('model', 'Unknown')
                    for item in data['messages']:
                        if 'role' in item and 'content' in item:
                            # Handle Anthropic content format (can be string or array)
                            content_text = item['content']
                            if isinstance(content_text, list):
                                # Extract text from content blocks
                                text_parts = []
                                for block in content_text:
                                    if isinstance(block, dict) and block.get('type') == 'text':
                                        text_parts.append(block.get('text', ''))
                                content_text = '\n'.join(text_parts)
                            
                            messages.append({
                                'role': item['role'],
                                'content': str(content_text)
                            })
            
            return {
                'model': model,
                'messages': messages,
                'date': None
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def convert_to_localmind_format(self, imported_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert imported conversation to LocalMind format
        
        Args:
            imported_data: Imported conversation data
            
        Returns:
            LocalMind conversation format
        """
        messages = []
        for msg in imported_data.get('messages', []):
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Normalize role names
            if role in ['system', 'user', 'assistant']:
                messages.append({
                    'role': role,
                    'content': content,
                    'timestamp': msg.get('timestamp')
                })
        
        return {
            'model': imported_data.get('model', 'Unknown'),
            'title': imported_data.get('title') or f"Imported Conversation",
            'messages': messages,
            'created_at': imported_data.get('date') or imported_data.get('created_at'),
            'metadata': {
                'imported': True,
                'source_format': imported_data.get('source_format', 'unknown')
            }
        }

