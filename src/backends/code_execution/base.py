"""
Base code execution interface
All code executors must implement this interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ExecutionStatus(str, Enum):
    """Code execution status"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"


class CodeExecutionResult(BaseModel):
    """Result from code execution"""
    status: ExecutionStatus
    output: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0  # in seconds
    memory_used: Optional[int] = None  # in bytes
    language: str
    code: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseCodeExecutor(ABC):
    """Base class for all code execution backends"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize code executor
        
        Args:
            config: Executor-specific configuration
        """
        self.config = config
        self.name = self.__class__.__name__
        self.language = self.get_language()
        self.timeout = config.get("timeout", 30)  # Default 30 seconds
        self.max_memory = config.get("max_memory", 128 * 1024 * 1024)  # Default 128MB
        self.allowed_imports = config.get("allowed_imports", [])
        self.blocked_imports = config.get("blocked_imports", [
            "os", "sys", "subprocess", "shutil", "socket", "multiprocessing",
            "ctypes", "pickle", "marshal", "eval", "exec", "compile"
        ])
    
    @abstractmethod
    def get_language(self) -> str:
        """
        Get the programming language this executor handles
        
        Returns:
            Language name (e.g., "python", "javascript")
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if executor is available and ready
        
        Returns:
            True if executor is available
        """
        pass
    
    @abstractmethod
    def execute(
        self,
        code: str,
        timeout: Optional[int] = None,
        **kwargs
    ) -> CodeExecutionResult:
        """
        Execute code safely
        
        Args:
            code: Code to execute
            timeout: Execution timeout in seconds (overrides config)
            **kwargs: Additional execution parameters
        
        Returns:
            CodeExecutionResult with execution output
        """
        pass
    
    def validate_code(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate code before execution (security checks)
        
        Args:
            code: Code to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for dangerous patterns
        dangerous_patterns = [
            (r'__import__\s*\(', "Direct __import__ calls are not allowed"),
            (r'eval\s*\(', "eval() is not allowed"),
            (r'exec\s*\(', "exec() is not allowed"),
            (r'compile\s*\(', "compile() is not allowed"),
            (r'open\s*\([^)]*[\'"]w', "File writing is restricted"),
            (r'open\s*\([^)]*[\'"]a', "File appending is restricted"),
            (r'subprocess\s*\.', "subprocess is not allowed"),
            (r'os\s*\.system', "os.system() is not allowed"),
            (r'os\s*\.popen', "os.popen() is not allowed"),
        ]
        
        import re
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                return False, message
        
        return True, None
    
    def get_executor_info(self) -> Dict[str, Any]:
        """
        Get information about this executor
        
        Returns:
            Dictionary with executor information
        """
        return {
            "name": self.name,
            "language": self.language,
            "timeout": self.timeout,
            "max_memory": self.max_memory,
            "available": self.is_available()
        }

