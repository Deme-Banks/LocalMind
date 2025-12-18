"""
Module Loader - manages and loads modules
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from ..modules.base import BaseModule, ModuleResponse

logger = logging.getLogger(__name__)


class ModuleLoader:
    """
    Manages module loading and execution.
    
    The ModuleLoader handles:
    - Discovering and loading modules
    - Registering modules for use
    - Routing prompts to appropriate modules
    - Managing module lifecycle
    - Inter-module communication
    
    Modules extend LocalMind's capabilities with specialized functionality
    like coding assistance, text generation, automation, etc.
    
    Attributes:
        modules_dir: Directory containing module files
        modules: Dictionary of loaded module instances
    """
    
    def __init__(self, modules_dir: Optional[Path] = None) -> None:
        """
        Initialize module loader.
        
        Args:
            modules_dir: Directory containing modules (default: src/modules)
        """
        if modules_dir is None:
            modules_dir = Path(__file__).parent.parent / "modules"
        
        self.modules_dir = modules_dir
        self.modules: Dict[str, BaseModule] = {}
        self._load_builtin_modules()
    
    def _load_builtin_modules(self):
        """Load built-in modules"""
        try:
            # Coding Assistant
            from ..modules.coding.assistant import CodingAssistantModule
            self.register_module(CodingAssistantModule())
        except ImportError as e:
            logger.debug(f"Could not load CodingAssistantModule: {e}")
        
        try:
            # Text Generator
            from ..modules.text_gen.generator import TextGeneratorModule
            self.register_module(TextGeneratorModule())
        except ImportError as e:
            logger.debug(f"Could not load TextGeneratorModule: {e}")
        
        try:
            # Automation Tools
            from ..modules.automation.tools import AutomationToolsModule
            self.register_module(AutomationToolsModule())
        except ImportError as e:
            logger.debug(f"Could not load AutomationToolsModule: {e}")
        
        try:
            # File Processor
            from ..modules.file_processor.processor import FileProcessorModule
            self.register_module(FileProcessorModule())
        except ImportError as e:
            logger.debug(f"Could not load FileProcessorModule: {e}")
    
    def register_module(self, module: BaseModule):
        """
        Register a module
        
        Args:
            module: Module instance to register
        """
        module_name = module.name
        module._module_loader = self  # Enable inter-module communication
        self.modules[module_name] = module
        logger.info(f"Registered module: {module_name}")
    
    def unregister_module(self, module_name: str) -> bool:
        """
        Unregister a module
        
        Args:
            module_name: Name of module to unregister
        
        Returns:
            True if module was unregistered
        """
        if module_name in self.modules:
            del self.modules[module_name]
            logger.info(f"Unregistered module: {module_name}")
            return True
        return False
    
    def get_module(self, module_name: str) -> Optional[BaseModule]:
        """
        Get a module by name
        
        Args:
            module_name: Name of module
        
        Returns:
            Module instance or None if not found
        """
        return self.modules.get(module_name)
    
    def list_modules(self) -> List[Dict[str, Any]]:
        """
        List all registered modules
        
        Returns:
            List of module information dictionaries
        """
        modules_info = []
        for name, module in self.modules.items():
            if module.is_enabled():
                info = module.get_info()
                info["name"] = name
                modules_info.append(info)
        return modules_info
    
    def find_module_for_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Optional[BaseModule]:
        """
        Find the best module to handle a prompt
        
        Args:
            prompt: User prompt
            context: Optional context
        
        Returns:
            Module that can handle the prompt, or None
        """
        # Check each enabled module
        for name, module in self.modules.items():
            if not module.is_enabled():
                continue
            
            try:
                if module.can_handle(prompt, context):
                    return module
            except Exception as e:
                logger.error(f"Error checking if module {name} can handle prompt: {e}")
                continue
        
        return None
    
    def call_module(self, module_name: str, prompt: str, model_loader: Any = None, 
                   context: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[ModuleResponse]:
        """
        Call a specific module
        
        Args:
            module_name: Name of module to call
            prompt: Prompt to process
            model_loader: ModelLoader instance
            context: Optional context
            **kwargs: Additional parameters
        
        Returns:
            ModuleResponse or None if module not found
        """
        module = self.get_module(module_name)
        if not module:
            logger.warning(f"Module {module_name} not found")
            return None
        
        if not module.is_enabled():
            logger.warning(f"Module {module_name} is disabled")
            return None
        
        try:
            return module.process(prompt, model_loader=model_loader, context=context, **kwargs)
        except Exception as e:
            logger.error(f"Error processing prompt in module {module_name}: {e}")
            return ModuleResponse(
                content="",
                metadata={},
                success=False,
                error=str(e)
            )
    
    def process_prompt(self, prompt: str, model_loader: Any = None,
                      context: Optional[Dict[str, Any]] = None,
                      preferred_module: Optional[str] = None,
                      **kwargs) -> ModuleResponse:
        """
        Process a prompt using the appropriate module
        
        Args:
            prompt: User prompt
            model_loader: ModelLoader instance
            context: Optional context
            preferred_module: Preferred module name (optional)
            **kwargs: Additional parameters
        
        Returns:
            ModuleResponse
        """
        # If preferred module specified, try that first
        if preferred_module:
            module = self.get_module(preferred_module)
            if module and module.is_enabled():
                try:
                    if module.can_handle(prompt, context):
                        return module.process(prompt, model_loader=model_loader, context=context, **kwargs)
                except Exception as e:
                    logger.error(f"Error in preferred module {preferred_module}: {e}")
        
        # Find best module for prompt
        module = self.find_module_for_prompt(prompt, context)
        
        if module:
            return module.process(prompt, model_loader=model_loader, context=context, **kwargs)
        
        # No module found - return empty response
        return ModuleResponse(
            content="",
            metadata={"module": None},
            success=False,
            error="No module found to handle this prompt"
        )
    
    def get_all_commands(self) -> List[Dict[str, str]]:
        """
        Get all commands from all modules
        
        Returns:
            List of all available commands
        """
        commands = []
        for name, module in self.modules.items():
            if module.is_enabled():
                module_commands = module.get_commands()
                for cmd in module_commands:
                    cmd["module"] = name
                    commands.append(cmd)
        return commands
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all tools from all modules
        
        Returns:
            List of all available tools
        """
        tools = []
        for name, module in self.modules.items():
            if module.is_enabled():
                module_tools = module.get_tools()
                for tool in module_tools:
                    tool["module"] = name
                    tools.append(tool)
        return tools

