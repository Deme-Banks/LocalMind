"""
Resource cleanup - manages cleanup of temporary files, cache, and old data
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ResourceCleanup:
    """Manages cleanup of system resources"""
    
    def __init__(self, cache_dir: Optional[Path] = None, conversations_dir: Optional[Path] = None):
        """
        Initialize resource cleanup
        
        Args:
            cache_dir: Cache directory path (default: ~/.localmind/cache)
            conversations_dir: Conversations directory path (default: conversations/)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".localmind" / "cache"
        if conversations_dir is None:
            conversations_dir = Path("conversations")
        
        self.cache_dir = Path(cache_dir)
        self.conversations_dir = Path(conversations_dir)
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_cache(self, max_age_days: int = 7, max_size_mb: Optional[int] = None) -> Dict[str, Any]:
        """
        Clean up old cache files
        
        Args:
            max_age_days: Maximum age in days for cache files (default: 7)
            max_size_mb: Maximum cache size in MB (optional)
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "files_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }
        
        if not self.cache_dir.exists():
            return stats
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        try:
            # Clean up by age
            for cache_file in self.cache_dir.rglob("*"):
                if cache_file.is_file():
                    try:
                        file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            file_size = cache_file.stat().st_size
                            cache_file.unlink()
                            stats["files_deleted"] += 1
                            stats["bytes_freed"] += file_size
                            logger.debug(f"Deleted old cache file: {cache_file}")
                    except Exception as e:
                        stats["errors"].append(f"Error deleting {cache_file}: {e}")
            
            # Clean up by size if specified
            if max_size_mb:
                total_size = sum(
                    f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file()
                )
                max_size_bytes = max_size_mb * 1024 * 1024
                
                if total_size > max_size_bytes:
                    # Sort files by modification time (oldest first)
                    files_with_mtime = []
                    for cache_file in self.cache_dir.rglob("*"):
                        if cache_file.is_file():
                            try:
                                mtime = cache_file.stat().st_mtime
                                size = cache_file.stat().st_size
                                files_with_mtime.append((mtime, size, cache_file))
                            except Exception:
                                continue
                    
                    files_with_mtime.sort()  # Sort by mtime (oldest first)
                    
                    # Delete oldest files until under limit
                    for mtime, size, cache_file in files_with_mtime:
                        if total_size <= max_size_bytes:
                            break
                        
                        try:
                            cache_file.unlink()
                            stats["files_deleted"] += 1
                            stats["bytes_freed"] += size
                            total_size -= size
                            logger.debug(f"Deleted cache file to free space: {cache_file}")
                        except Exception as e:
                            stats["errors"].append(f"Error deleting {cache_file}: {e}")
            
            # Remove empty directories
            for cache_dir_path in list(self.cache_dir.rglob("*")):
                if cache_dir_path.is_dir():
                    try:
                        if not any(cache_dir_path.iterdir()):
                            cache_dir_path.rmdir()
                            logger.debug(f"Removed empty cache directory: {cache_dir_path}")
                    except Exception:
                        pass
        
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}", exc_info=True)
            stats["errors"].append(str(e))
        
        return stats
    
    def cleanup_conversations(
        self,
        max_age_days: Optional[int] = None,
        keep_recent: int = 50,
        max_size_mb: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Clean up old conversations
        
        Args:
            max_age_days: Maximum age in days (optional)
            keep_recent: Always keep N most recent conversations (default: 50)
            max_size_mb: Maximum size in MB (optional)
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "conversations_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }
        
        if not self.conversations_dir.exists():
            return stats
        
        try:
            # Get all conversation files
            conversations = []
            index_file = self.conversations_dir / "index.json"
            
            if index_file.exists():
                import json
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
                    conversations = index_data.get("conversations", [])
            
            if not conversations:
                return stats
            
            # Sort by last_updated (oldest first)
            conversations.sort(key=lambda c: c.get("last_updated", ""))
            
            # Always keep the most recent N conversations
            if len(conversations) > keep_recent:
                conversations_to_check = conversations[:-keep_recent]
                keep_conversations = conversations[-keep_recent:]
            else:
                conversations_to_check = []
                keep_conversations = conversations
            
            cutoff_time = None
            if max_age_days:
                cutoff_time = datetime.now() - timedelta(days=max_age_days)
            
            # Check conversations for deletion
            for conv in conversations_to_check:
                conv_id = conv.get("id")
                if not conv_id:
                    continue
                
                should_delete = False
                
                # Check age
                if cutoff_time:
                    last_updated_str = conv.get("last_updated")
                    if last_updated_str:
                        try:
                            last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                            if last_updated < cutoff_time:
                                should_delete = True
                        except Exception:
                            pass
                
                if should_delete:
                    try:
                        conv_file = self.conversations_dir / f"{conv_id}.json"
                        if conv_file.exists():
                            file_size = conv_file.stat().st_size
                            conv_file.unlink()
                            stats["conversations_deleted"] += 1
                            stats["bytes_freed"] += file_size
                            logger.debug(f"Deleted old conversation: {conv_id}")
                    except Exception as e:
                        stats["errors"].append(f"Error deleting conversation {conv_id}: {e}")
            
            # Clean up by size if specified
            if max_size_mb:
                total_size = sum(
                    f.stat().st_size
                    for f in self.conversations_dir.glob("*.json")
                    if f.is_file()
                )
                max_size_bytes = max_size_mb * 1024 * 1024
                
                if total_size > max_size_bytes:
                    # Sort remaining conversations by size (largest first) or age
                    remaining_conversations = [
                        conv for conv in conversations
                        if conv.get("id") not in [c.get("id") for c in keep_conversations]
                    ]
                    
                    # Delete largest/oldest until under limit
                    for conv in sorted(remaining_conversations, key=lambda c: c.get("last_updated", "")):
                        if total_size <= max_size_bytes:
                            break
                        
                        conv_id = conv.get("id")
                        if not conv_id:
                            continue
                        
                        try:
                            conv_file = self.conversations_dir / f"{conv_id}.json"
                            if conv_file.exists():
                                file_size = conv_file.stat().st_size
                                conv_file.unlink()
                                stats["conversations_deleted"] += 1
                                stats["bytes_freed"] += file_size
                                total_size -= file_size
                                logger.debug(f"Deleted conversation to free space: {conv_id}")
                        except Exception as e:
                            stats["errors"].append(f"Error deleting conversation {conv_id}: {e}")
            
            # Update index if conversations were deleted
            if stats["conversations_deleted"] > 0 and index_file.exists():
                try:
                    import json
                    with open(index_file, 'r') as f:
                        index_data = json.load(f)
                    
                    # Remove deleted conversations from index
                    remaining_ids = {c.get("id") for c in keep_conversations}
                    index_data["conversations"] = [
                        c for c in index_data.get("conversations", [])
                        if c.get("id") in remaining_ids
                    ]
                    
                    with open(index_file, 'w') as f:
                        json.dump(index_data, f, indent=2)
                except Exception as e:
                    logger.error(f"Error updating conversation index: {e}")
                    stats["errors"].append(f"Error updating index: {e}")
        
        except Exception as e:
            logger.error(f"Error during conversation cleanup: {e}", exc_info=True)
            stats["errors"].append(str(e))
        
        return stats
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up temporary files
        
        Args:
            max_age_hours: Maximum age in hours (default: 24)
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "files_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }
        
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Look for LocalMind temp files
        temp_patterns = ["localmind_*", "*_localmind_*"]
        
        try:
            for pattern in temp_patterns:
                for temp_file in temp_dir.glob(pattern):
                    if temp_file.is_file():
                        try:
                            file_mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                            if file_mtime < cutoff_time:
                                file_size = temp_file.stat().st_size
                                temp_file.unlink()
                                stats["files_deleted"] += 1
                                stats["bytes_freed"] += file_size
                                logger.debug(f"Deleted temp file: {temp_file}")
                        except Exception as e:
                            stats["errors"].append(f"Error deleting {temp_file}: {e}")
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}", exc_info=True)
            stats["errors"].append(str(e))
        
        return stats
    
    def cleanup_logs(self, max_age_days: int = 30, max_size_mb: Optional[int] = None) -> Dict[str, Any]:
        """
        Clean up old log files
        
        Args:
            max_age_days: Maximum age in days (default: 30)
            max_size_mb: Maximum size in MB (optional)
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "files_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }
        
        # Look for log files in common locations
        log_dirs = [
            Path.home() / ".localmind" / "logs",
            Path("logs"),
            Path(".")  # Current directory
        ]
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        log_patterns = ["*.log", "*.log.*"]
        
        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
            
            try:
                for pattern in log_patterns:
                    for log_file in log_dir.glob(pattern):
                        if log_file.is_file():
                            try:
                                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                                if file_mtime < cutoff_time:
                                    file_size = log_file.stat().st_size
                                    log_file.unlink()
                                    stats["files_deleted"] += 1
                                    stats["bytes_freed"] += file_size
                                    logger.debug(f"Deleted old log file: {log_file}")
                            except Exception as e:
                                stats["errors"].append(f"Error deleting {log_file}: {e}")
            except Exception as e:
                stats["errors"].append(f"Error accessing {log_dir}: {e}")
        
        return stats
    
    def cleanup_all(
        self,
        cache_max_age_days: int = 7,
        cache_max_size_mb: Optional[int] = None,
        conversations_max_age_days: Optional[int] = None,
        conversations_keep_recent: int = 50,
        conversations_max_size_mb: Optional[int] = None,
        temp_max_age_hours: int = 24,
        logs_max_age_days: int = 30,
        logs_max_size_mb: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run all cleanup operations
        
        Returns:
            Dictionary with combined cleanup statistics
        """
        results = {
            "cache": self.cleanup_cache(cache_max_age_days, cache_max_size_mb),
            "conversations": self.cleanup_conversations(
                conversations_max_age_days,
                conversations_keep_recent,
                conversations_max_size_mb
            ),
            "temp_files": self.cleanup_temp_files(temp_max_age_hours),
            "logs": self.cleanup_logs(logs_max_age_days, logs_max_size_mb),
            "total_bytes_freed": 0,
            "total_files_deleted": 0
        }
        
        # Calculate totals
        for section in ["cache", "conversations", "temp_files", "logs"]:
            results["total_bytes_freed"] += results[section].get("bytes_freed", 0)
            results["total_files_deleted"] += results[section].get("files_deleted", 0)
            if section == "conversations":
                results["total_files_deleted"] += results[section].get("conversations_deleted", 0)
        
        return results
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about resources that could be cleaned up
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "cache": {"files": 0, "size_bytes": 0},
            "conversations": {"count": 0, "size_bytes": 0},
            "temp_files": {"files": 0, "size_bytes": 0},
            "logs": {"files": 0, "size_bytes": 0}
        }
        
        # Cache stats
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.rglob("*"):
                if cache_file.is_file():
                    try:
                        stats["cache"]["files"] += 1
                        stats["cache"]["size_bytes"] += cache_file.stat().st_size
                    except Exception:
                        pass
        
        # Conversation stats
        if self.conversations_dir.exists():
            for conv_file in self.conversations_dir.glob("*.json"):
                if conv_file.is_file():
                    try:
                        stats["conversations"]["count"] += 1
                        stats["conversations"]["size_bytes"] += conv_file.stat().st_size
                    except Exception:
                        pass
        
        # Temp file stats
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        for pattern in ["localmind_*", "*_localmind_*"]:
            for temp_file in temp_dir.glob(pattern):
                if temp_file.is_file():
                    try:
                        stats["temp_files"]["files"] += 1
                        stats["temp_files"]["size_bytes"] += temp_file.stat().st_size
                    except Exception:
                        pass
        
        # Log stats
        log_dirs = [
            Path.home() / ".localmind" / "logs",
            Path("logs"),
            Path(".")
        ]
        for log_dir in log_dirs:
            if log_dir.exists():
                for log_file in log_dir.glob("*.log*"):
                    if log_file.is_file():
                        try:
                            stats["logs"]["files"] += 1
                            stats["logs"]["size_bytes"] += log_file.stat().st_size
                        except Exception:
                            pass
        
        return stats

