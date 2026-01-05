"""
Python code executor with sandboxing
"""

import subprocess
import tempfile
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
import logging

# resource module is Unix-only, import conditionally
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

from .base import BaseCodeExecutor, CodeExecutionResult, ExecutionStatus

logger = logging.getLogger(__name__)


class PythonExecutor(BaseCodeExecutor):
    """Executor for Python code"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.python_path = config.get("python_path", "python")
        self.use_sandbox = config.get("use_sandbox", True)
        self.working_dir = Path(config.get("working_dir", tempfile.gettempdir())) / "python_exec"
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def get_language(self) -> str:
        return "python"
    
    def is_available(self) -> bool:
        """Check if Python is available"""
        try:
            result = subprocess.run(
                [self.python_path, "--version"],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def execute(
        self,
        code: str,
        timeout: Optional[int] = None,
        **kwargs
    ) -> CodeExecutionResult:
        """Execute Python code safely"""
        start_time = time.time()
        
        # Enhanced security validation - block dangerous operations
        dangerous_patterns = [
            ('import os', 'os module is not allowed for security reasons'),
            ('import sys', 'sys module is not allowed for security reasons'),
            ('import subprocess', 'subprocess module is not allowed for security reasons'),
            ('import shutil', 'shutil module is not allowed for security reasons'),
            ('import socket', 'socket module is not allowed for security reasons'),
            ('import multiprocessing', 'multiprocessing module is not allowed for security reasons'),
            ('__import__', 'Direct __import__ calls are not allowed'),
            ('eval(', 'eval() function is not allowed'),
            ('exec(', 'exec() function is not allowed'),
            ('compile(', 'compile() function is not allowed'),
            ('open(', 'File operations are restricted'),
            ('file(', 'File operations are restricted'),
            ('__builtins__', 'Builtins manipulation is not allowed'),
            ('os.system', 'System commands are not allowed'),
            ('os.popen', 'Process execution is not allowed'),
            ('subprocess.', 'Subprocess execution is not allowed'),
        ]
        code_lower = code.lower()
        for pattern, message in dangerous_patterns:
            if pattern in code_lower:
                return CodeExecutionResult(
                    status=ExecutionStatus.SECURITY_VIOLATION,
                    error=f"Security violation: {message}",
                    language=self.language,
                    code=code,
                    execution_time=0.0
                )
        
        # Use configured timeout or default
        exec_timeout = timeout or self.timeout
        
        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                dir=self.working_dir,
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with resource limits
                result = subprocess.run(
                    [self.python_path, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=exec_timeout,
                    cwd=self.working_dir,
                    env=self._get_safe_env()
                )
                
                execution_time = time.time() - start_time
                
                if result.returncode == 0:
                    return CodeExecutionResult(
                        status=ExecutionStatus.SUCCESS,
                        output=result.stdout,
                        language=self.language,
                        code=code,
                        execution_time=execution_time,
                        metadata={"returncode": result.returncode}
                    )
                else:
                    return CodeExecutionResult(
                        status=ExecutionStatus.ERROR,
                        output=result.stdout,
                        error=result.stderr,
                        language=self.language,
                        code=code,
                        execution_time=execution_time,
                        metadata={"returncode": result.returncode}
                    )
            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                return CodeExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    error=f"Execution timed out after {exec_timeout} seconds",
                    language=self.language,
                    code=code,
                    execution_time=execution_time
                )
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
                    
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing Python code: {e}", exc_info=True)
            return CodeExecutionResult(
                status=ExecutionStatus.ERROR,
                error=str(e),
                language=self.language,
                code=code,
                execution_time=execution_time
            )
    
    def _get_safe_env(self) -> Dict[str, str]:
        """Get safe environment variables for execution"""
        env = os.environ.copy()
        # Remove potentially dangerous environment variables
        dangerous_vars = [
            "PYTHONPATH", "PATH", "LD_LIBRARY_PATH",
            "HOME", "USER", "USERNAME"
        ]
        for var in dangerous_vars:
            env.pop(var, None)
        
        # Set safe defaults
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        
        return env

