"""
Code Execution Manager - manages different code execution backends
"""

from typing import Dict, Optional, List
from pathlib import Path
import logging

from ..backends.code_execution.base import BaseCodeExecutor, CodeExecutionResult, ExecutionStatus
from ..backends.code_execution.python_executor import PythonExecutor
from ..backends.code_execution.javascript_executor import JavaScriptExecutor
from ..backends.code_execution.bash_executor import BashExecutor
from ..utils.config import ConfigManager, LocalMindConfig

logger = logging.getLogger(__name__)


class CodeExecutionManager:
    """Manages code execution backends"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize code execution manager
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.executors: Dict[str, BaseCodeExecutor] = {}
        self._initialize_executors()
    
    def _initialize_executors(self) -> None:
        """Initialize available code execution backends"""
        # Get code execution configs (try both names for compatibility)
        code_exec_config = getattr(self.config, 'code_execution', {}) or getattr(self.config, 'code_executors', {})
        
        # Initialize Python executor
        if code_exec_config.get('python', {}).get('enabled', True):
            try:
                executor = PythonExecutor(code_exec_config.get('python', {}).get('settings', {}))
                if executor.is_available():
                    self.executors['python'] = executor
                    logger.info("✅ Python code executor initialized")
                else:
                    logger.warning("⚠️ Python executor not available (Python not found)")
            except Exception as e:
                logger.error(f"Failed to initialize Python executor: {e}")
        
        # Initialize JavaScript executor
        if code_exec_config.get('javascript', {}).get('enabled', True):
            try:
                executor = JavaScriptExecutor(code_exec_config.get('javascript', {}).get('settings', {}))
                if executor.is_available():
                    self.executors['javascript'] = executor
                    logger.info("✅ JavaScript code executor initialized")
                else:
                    logger.warning("⚠️ JavaScript executor not available (Node.js not found)")
            except Exception as e:
                logger.error(f"Failed to initialize JavaScript executor: {e}")
        
        # Initialize Bash executor
        if code_exec_config.get('bash', {}).get('enabled', True):
            try:
                executor = BashExecutor(code_exec_config.get('bash', {}).get('settings', {}))
                if executor.is_available():
                    self.executors['bash'] = executor
                    logger.info("✅ Bash/Shell code executor initialized")
                else:
                    logger.warning("⚠️ Bash executor not available (Bash/Shell not found)")
            except Exception as e:
                logger.error(f"Failed to initialize Bash executor: {e}")
    
    def get_executor(self, language: str) -> Optional[BaseCodeExecutor]:
        """Get a code executor by language"""
        return self.executors.get(language.lower())
    
    def list_executors(self) -> List[str]:
        """List available code execution languages"""
        return list(self.executors.keys())
    
    def execute_code(
        self,
        code: str,
        language: str,
        timeout: Optional[int] = None,
        **kwargs
    ) -> CodeExecutionResult:
        """
        Execute code using specified language executor
        
        Args:
            code: Code to execute
            language: Programming language (python, javascript)
            timeout: Execution timeout in seconds
            **kwargs: Additional execution parameters
        
        Returns:
            CodeExecutionResult
        """
        executor = self.get_executor(language)
        if not executor:
            return CodeExecutionResult(
                status=ExecutionStatus.ERROR,
                error=f"Language '{language}' not supported or executor not available",
                language=language,
                code=code
            )
        
        try:
            return executor.execute(code, timeout=timeout, **kwargs)
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            return CodeExecutionResult(
                status=ExecutionStatus.ERROR,
                error=str(e),
                language=language,
                code=code
            )
    
    def detect_language(self, code: str) -> Optional[str]:
        """
        Detect programming language from code
        
        Args:
            code: Code to analyze
        
        Returns:
            Detected language or None
        """
        code_lower = code.lower().strip()
        
        # Python indicators
        if any(keyword in code for keyword in ['def ', 'import ', 'print(', 'if __name__']):
            return 'python'
        
        # JavaScript indicators
        if any(keyword in code for keyword in ['function ', 'const ', 'let ', 'var ', 'console.log']):
            return 'javascript'
        
        # Bash/Shell indicators
        if any(keyword in code for keyword in ['#!/bin/bash', '#!/bin/sh', 'echo ', 'export ', 'if [', 'for ' in code and 'in ' in code]):
            return 'bash'
        
        # Check for language hints in comments
        if '#!/usr/bin/env python' in code or '# python' in code_lower:
            return 'python'
        if '#!/usr/bin/env node' in code or '// javascript' in code_lower:
            return 'javascript'
        if '#!/bin/bash' in code or '#!/bin/sh' in code:
            return 'bash'
        
        return None
