"""
Model Versioning - Manage model versions and updates
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelVersion:
    """Model version information"""
    version: str
    model_name: str
    backend: str
    created_at: datetime
    file_path: Optional[Path]
    metadata: Dict[str, Any]
    checksum: Optional[str] = None


class ModelVersionManager:
    """Manages model versions"""
    
    def __init__(self, versions_dir: Optional[Path] = None):
        """
        Initialize model version manager
        
        Args:
            versions_dir: Directory for version metadata
        """
        if versions_dir is None:
            versions_dir = Path.home() / ".localmind" / "versions"
        
        self.versions_dir = versions_dir
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        self.versions: Dict[str, List[ModelVersion]] = {}  # {model_name: [versions]}
        self._load_versions()
    
    def _load_versions(self):
        """Load version information from disk"""
        version_file = self.versions_dir / "versions.json"
        
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for model_name, version_list in data.items():
                    self.versions[model_name] = [
                        ModelVersion(
                            version=v["version"],
                            model_name=v["model_name"],
                            backend=v["backend"],
                            created_at=datetime.fromisoformat(v["created_at"]),
                            file_path=Path(v["file_path"]) if v.get("file_path") else None,
                            metadata=v.get("metadata", {}),
                            checksum=v.get("checksum")
                        )
                        for v in version_list
                    ]
            except Exception as e:
                logger.error(f"Error loading versions: {e}")
    
    def _save_versions(self):
        """Save version information to disk"""
        version_file = self.versions_dir / "versions.json"
        
        data = {}
        for model_name, version_list in self.versions.items():
            data[model_name] = [
                {
                    "version": v.version,
                    "model_name": v.model_name,
                    "backend": v.backend,
                    "created_at": v.created_at.isoformat(),
                    "file_path": str(v.file_path) if v.file_path else None,
                    "metadata": v.metadata,
                    "checksum": v.checksum
                }
                for v in version_list
            ]
        
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def register_version(
        self,
        model_name: str,
        version: str,
        backend: str,
        file_path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None,
        checksum: Optional[str] = None
    ) -> ModelVersion:
        """
        Register a new model version
        
        Args:
            model_name: Name of the model
            version: Version string (e.g., "1.0.0")
            backend: Backend name
            file_path: Optional path to model file
            metadata: Optional metadata
            checksum: Optional file checksum
            
        Returns:
            ModelVersion object
        """
        model_version = ModelVersion(
            version=version,
            model_name=model_name,
            backend=backend,
            created_at=datetime.utcnow(),
            file_path=file_path,
            metadata=metadata or {},
            checksum=checksum
        )
        
        if model_name not in self.versions:
            self.versions[model_name] = []
        
        self.versions[model_name].append(model_version)
        self._save_versions()
        
        logger.info(f"Registered version {version} for model {model_name}")
        return model_version
    
    def get_versions(self, model_name: str) -> List[ModelVersion]:
        """Get all versions for a model"""
        return self.versions.get(model_name, [])
    
    def get_latest_version(self, model_name: str) -> Optional[ModelVersion]:
        """Get latest version for a model"""
        versions = self.get_versions(model_name)
        if not versions:
            return None
        
        # Sort by created_at, return most recent
        return max(versions, key=lambda v: v.created_at)
    
    def compare_versions(self, model_name: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two versions of a model
        
        Args:
            model_name: Model name
            version1: First version
            version2: Second version
            
        Returns:
            Comparison dictionary
        """
        versions = self.get_versions(model_name)
        v1 = next((v for v in versions if v.version == version1), None)
        v2 = next((v for v in versions if v.version == version2), None)
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        return {
            "model": model_name,
            "version1": {
                "version": v1.version,
                "created_at": v1.created_at.isoformat(),
                "metadata": v1.metadata
            },
            "version2": {
                "version": v2.version,
                "created_at": v2.created_at.isoformat(),
                "metadata": v2.metadata
            },
            "newer": v1.version if v1.created_at > v2.created_at else v2.version
        }

