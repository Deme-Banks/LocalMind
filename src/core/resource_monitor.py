"""
Resource monitor - tracks system resource usage (CPU, memory, GPU)
"""

import platform
import psutil
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import GPU monitoring libraries
try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False


class ResourceMonitor:
    """Monitors system resource usage"""
    
    def __init__(self):
        """Initialize resource monitor"""
        self._init_gpu_monitoring()
    
    def _init_gpu_monitoring(self):
        """Initialize GPU monitoring if available"""
        self.gpu_available = False
        self.gpu_count = 0
        
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_count = pynvml.nvmlDeviceGetCount()
                self.gpu_available = self.gpu_count > 0
            except Exception as e:
                logger.warning(f"Failed to initialize NVIDIA GPU monitoring: {e}")
                self.gpu_available = False
        elif GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                self.gpu_count = len(gpus)
                self.gpu_available = self.gpu_count > 0
            except Exception as e:
                logger.warning(f"Failed to initialize GPU monitoring: {e}")
                self.gpu_available = False
    
    def get_cpu_usage(self) -> Dict[str, Any]:
        """
        Get CPU usage statistics
        
        Returns:
            Dictionary with CPU usage information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            cpu_freq = psutil.cpu_freq()
            
            # Per-core usage
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            return {
                "usage_percent": cpu_percent,
                "cores": cpu_count,
                "physical_cores": cpu_count_physical,
                "frequency_mhz": cpu_freq.current if cpu_freq else None,
                "frequency_max_mhz": cpu_freq.max if cpu_freq else None,
                "per_core": cpu_per_core,
                "available": True
            }
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return {"available": False, "error": str(e)}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics
        
        Returns:
            Dictionary with memory usage information
        """
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "total_gb": memory.total / (1024 ** 3),
                "available_gb": memory.available / (1024 ** 3),
                "used_gb": memory.used / (1024 ** 3),
                "percent": memory.percent,
                "swap_total_gb": swap.total / (1024 ** 3),
                "swap_used_gb": swap.used / (1024 ** 3),
                "swap_percent": swap.percent,
                "available": True
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {"available": False, "error": str(e)}
    
    def get_gpu_usage(self) -> Dict[str, Any]:
        """
        Get GPU usage statistics
        
        Returns:
            Dictionary with GPU usage information
        """
        if not self.gpu_available:
            return {
                "available": False,
                "gpus": [],
                "message": "GPU monitoring not available (install pynvml or GPUtil)"
            }
        
        gpus = []
        
        if PYNVML_AVAILABLE:
            try:
                for i in range(self.gpu_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    
                    # Get GPU name
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    
                    # Get memory info
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    total_mem = mem_info.total / (1024 ** 3)  # GB
                    used_mem = mem_info.used / (1024 ** 3)  # GB
                    free_mem = mem_info.free / (1024 ** 3)  # GB
                    
                    # Get utilization
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = util.gpu
                    memory_util = util.memory
                    
                    # Get temperature
                    try:
                        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    except Exception:
                        temp = None
                    
                    # Get power usage
                    try:
                        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                    except Exception:
                        power = None
                    
                    gpus.append({
                        "index": i,
                        "name": name,
                        "memory_total_gb": total_mem,
                        "memory_used_gb": used_mem,
                        "memory_free_gb": free_mem,
                        "memory_percent": (used_mem / total_mem) * 100 if total_mem > 0 else 0,
                        "utilization_percent": gpu_util,
                        "memory_utilization_percent": memory_util,
                        "temperature_c": temp,
                        "power_watts": power
                    })
            except Exception as e:
                logger.error(f"Error getting GPU usage with pynvml: {e}")
                return {"available": False, "error": str(e), "gpus": []}
        
        elif GPUTIL_AVAILABLE:
            try:
                gpu_list = GPUtil.getGPUs()
                for i, gpu in enumerate(gpu_list):
                    gpus.append({
                        "index": i,
                        "name": gpu.name,
                        "memory_total_gb": gpu.memoryTotal / 1024.0,
                        "memory_used_gb": gpu.memoryUsed / 1024.0,
                        "memory_free_gb": gpu.memoryFree / 1024.0,
                        "memory_percent": gpu.memoryUtil * 100,
                        "utilization_percent": gpu.load * 100,
                        "memory_utilization_percent": gpu.memoryUtil * 100,
                        "temperature_c": gpu.temperature,
                        "power_watts": None  # GPUtil doesn't provide power
                    })
            except Exception as e:
                logger.error(f"Error getting GPU usage with GPUtil: {e}")
                return {"available": False, "error": str(e), "gpus": []}
        
        return {
            "available": True,
            "gpu_count": len(gpus),
            "gpus": gpus
        }
    
    def get_disk_usage(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get disk usage statistics
        
        Args:
            path: Path to check (default: root partition)
            
        Returns:
            Dictionary with disk usage information
        """
        try:
            if path is None:
                if platform.system() == "Windows":
                    path = "C:\\"
                else:
                    path = "/"
            
            disk = psutil.disk_usage(path)
            
            return {
                "path": path,
                "total_gb": disk.total / (1024 ** 3),
                "used_gb": disk.used / (1024 ** 3),
                "free_gb": disk.free / (1024 ** 3),
                "percent": (disk.used / disk.total) * 100 if disk.total > 0 else 0,
                "available": True
            }
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {"available": False, "error": str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information
        
        Returns:
            Dictionary with all system information
        """
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu": self.get_cpu_usage(),
            "memory": self.get_memory_usage(),
            "gpu": self.get_gpu_usage(),
            "disk": self.get_disk_usage()
        }
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get a quick summary of resource usage
        
        Returns:
            Dictionary with resource summary
        """
        cpu = self.get_cpu_usage()
        memory = self.get_memory_usage()
        gpu = self.get_gpu_usage()
        
        summary = {
            "cpu_percent": cpu.get("usage_percent", 0) if cpu.get("available") else None,
            "memory_percent": memory.get("percent", 0) if memory.get("available") else None,
            "memory_used_gb": memory.get("used_gb", 0) if memory.get("available") else None,
            "memory_total_gb": memory.get("total_gb", 0) if memory.get("available") else None,
            "gpu_available": gpu.get("available", False),
            "gpu_count": gpu.get("gpu_count", 0)
        }
        
        if gpu.get("available") and gpu.get("gpus"):
            # Get average GPU utilization
            gpu_utils = [g.get("utilization_percent", 0) for g in gpu["gpus"]]
            summary["gpu_utilization_percent"] = sum(gpu_utils) / len(gpu_utils) if gpu_utils else 0
        else:
            summary["gpu_utilization_percent"] = None
        
        return summary

