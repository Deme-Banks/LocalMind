"""
Bash/Shell code executor with sandboxing
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


class BashExecutor(BaseCodeExecutor):
    """Executor for Bash/Shell code"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.shell_path = config.get("shell_path", "/bin/bash")
        if os.name == 'nt':  # Windows
            # Try to use Git Bash or WSL bash
            possible_paths = [
                "C:\\Program Files\\Git\\bin\\bash.exe",
                "C:\\Program Files (x86)\\Git\\bin\\bash.exe",
                "bash.exe",  # If in PATH
                "wsl.exe",  # Windows Subsystem for Linux
            ]
            for path in possible_paths:
                if os.path.exists(path) or path in ["bash.exe", "wsl.exe"]:
                    self.shell_path = path
                    break
        self.timeout = config.get("timeout", 30)
        self.use_sandbox = config.get("use_sandbox", True)
        self.working_dir = Path(config.get("working_dir", tempfile.gettempdir())) / "bash_exec"
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def get_language(self) -> str:
        return "bash"
    
    def is_available(self) -> bool:
        """Check if Bash/Shell is available"""
        try:
            if os.name == 'nt':  # Windows
                # Check if Git Bash or WSL is available
                if "wsl.exe" in self.shell_path:
                    result = subprocess.run(
                        ["wsl.exe", "bash", "--version"],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    return result.returncode == 0
                else:
                    result = subprocess.run(
                        [self.shell_path, "--version"],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    return result.returncode == 0
            else:  # Unix/Linux/Mac
                result = subprocess.run(
                    [self.shell_path, "--version"],
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
        """Execute Bash/Shell code safely"""
        start_time = time.time()
        
        # Security validation - block dangerous operations
        dangerous_patterns = [
            ('rm -rf', 'Recursive deletion is not allowed'),
            ('rm -f /', 'System deletion is not allowed'),
            ('dd if=', 'Disk operations are not allowed'),
            ('mkfs', 'File system operations are not allowed'),
            ('fdisk', 'Disk partitioning is not allowed'),
            ('format', 'Formatting is not allowed'),
            ('> /dev/', 'Device operations are not allowed'),
            ('sudo', 'Sudo commands are not allowed'),
            ('su ', 'User switching is not allowed'),
            ('chmod 777', 'Dangerous permissions are not allowed'),
            ('chown', 'Ownership changes are not allowed'),
            ('nc ', 'Netcat is not allowed'),
            ('netcat', 'Netcat is not allowed'),
            ('wget', 'Network downloads are restricted'),
            ('curl', 'Network requests are restricted'),
            ('ssh ', 'SSH connections are not allowed'),
            ('scp ', 'SCP transfers are not allowed'),
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
                suffix='.sh',
                dir=self.working_dir,
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Make file executable (Unix only)
                if os.name != 'nt':
                    os.chmod(temp_file, 0o755)
                
                # Execute with shell
                if os.name == 'nt' and "wsl.exe" in self.shell_path:
                    # Use WSL
                    command = ["wsl.exe", "bash", temp_file]
                else:
                    command = [self.shell_path, temp_file]
                
                result = subprocess.run(
                    command,
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
            logger.error(f"Error executing Bash code: {e}", exc_info=True)
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
            "PATH", "LD_LIBRARY_PATH", "LD_PRELOAD",
            "HOME", "USER", "USERNAME", "SUDO_USER",
            "SSH_AUTH_SOCK", "SSH_AGENT_PID"
        ]
        for var in dangerous_vars:
            env.pop(var, None)
        
        # Set safe defaults
        env["SHELL"] = self.shell_path
        if os.name != 'nt':
            env["HOME"] = str(self.working_dir)
        
        return env

