"""
JavaScript/Node.js code executor with sandboxing
"""

import subprocess
import tempfile
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .base import BaseCodeExecutor, CodeExecutionResult, ExecutionStatus
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class JavaScriptExecutor(BaseCodeExecutor):
    """Executor for JavaScript/Node.js code"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.node_path = config.get("node_path", "node")
        self.use_sandbox = config.get("use_sandbox", True)
        self.working_dir = Path(config.get("working_dir", tempfile.gettempdir())) / "js_exec"
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def get_language(self) -> str:
        return "javascript"
    
    def is_available(self) -> bool:
        """Check if Node.js is available"""
        try:
            result = subprocess.run(
                [self.node_path, "--version"],
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
        """Execute JavaScript code safely"""
        start_time = time.time()
        
        # Validate code
        is_valid, error_msg = self.validate_code(code)
        if not is_valid:
            return CodeExecutionResult(
                status=ExecutionStatus.SECURITY_VIOLATION,
                error=error_msg,
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
                suffix='.js',
                dir=self.working_dir,
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with Node.js
                result = subprocess.run(
                    [self.node_path, temp_file],
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
            logger.error(f"Error executing JavaScript code: {e}", exc_info=True)
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
            "NODE_PATH", "PATH", "LD_LIBRARY_PATH",
            "HOME", "USER", "USERNAME"
        ]
        for var in dangerous_vars:
            env.pop(var, None)
        
        return env

