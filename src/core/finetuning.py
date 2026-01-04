"""
Model Fine-tuning - Interface for fine-tuning models
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrainingData:
    """Training data entry"""
    prompt: str
    completion: str
    metadata: Dict[str, Any]


@dataclass
class FineTuningJob:
    """Fine-tuning job information"""
    job_id: str
    model: str
    base_model: str
    status: str  # pending, running, completed, failed
    training_data_path: Path
    created_at: datetime
    completed_at: Optional[datetime]
    metrics: Dict[str, Any]


class FineTuningManager:
    """Manages model fine-tuning"""
    
    def __init__(self, training_dir: Optional[Path] = None):
        """
        Initialize fine-tuning manager
        
        Args:
            training_dir: Directory for training data and jobs
        """
        if training_dir is None:
            training_dir = Path.home() / ".localmind" / "training"
        
        self.training_dir = training_dir
        self.training_dir.mkdir(parents=True, exist_ok=True)
        self.training_data_dir = self.training_dir / "data"
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir = self.training_dir / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        self.jobs: Dict[str, FineTuningJob] = {}
    
    def create_training_dataset(
        self,
        name: str,
        data: List[TrainingData]
    ) -> Path:
        """
        Create a training dataset
        
        Args:
            name: Dataset name
            data: List of training data entries
            
        Returns:
            Path to created dataset file
        """
        import json
        
        dataset_file = self.training_data_dir / f"{name}.jsonl"
        
        with open(dataset_file, 'w', encoding='utf-8') as f:
            for entry in data:
                line = json.dumps({
                    "prompt": entry.prompt,
                    "completion": entry.completion,
                    "metadata": entry.metadata
                }, ensure_ascii=False)
                f.write(line + '\n')
        
        logger.info(f"Created training dataset: {dataset_file}")
        return dataset_file
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all training datasets"""
        datasets = []
        
        for dataset_file in self.training_data_dir.glob("*.jsonl"):
            try:
                # Count lines
                with open(dataset_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                
                datasets.append({
                    "name": dataset_file.stem,
                    "file": str(dataset_file),
                    "entries": line_count,
                    "size": dataset_file.stat().st_size
                })
            except Exception as e:
                logger.error(f"Error reading dataset {dataset_file}: {e}")
        
        return datasets
    
    def create_finetuning_job(
        self,
        model: str,
        base_model: str,
        training_data_path: Path
    ) -> FineTuningJob:
        """
        Create a fine-tuning job
        
        Args:
            model: Target model name
            base_model: Base model to fine-tune
            training_data_path: Path to training data
            
        Returns:
            FineTuningJob object
        """
        import uuid
        
        job_id = str(uuid.uuid4())
        
        job = FineTuningJob(
            job_id=job_id,
            model=model,
            base_model=base_model,
            status="pending",
            training_data_path=training_data_path,
            created_at=datetime.utcnow(),
            completed_at=None,
            metrics={}
        )
        
        self.jobs[job_id] = job
        self._save_job(job)
        
        logger.info(f"Created fine-tuning job: {job_id} for model {model}")
        return job
    
    def get_job(self, job_id: str) -> Optional[FineTuningJob]:
        """Get fine-tuning job by ID"""
        return self.jobs.get(job_id)
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all fine-tuning jobs"""
        return [
            {
                "job_id": job.job_id,
                "model": job.model,
                "base_model": job.base_model,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "metrics": job.metrics
            }
            for job in self.jobs.values()
        ]
    
    def _save_job(self, job: FineTuningJob):
        """Save job to disk"""
        import json
        
        job_file = self.jobs_dir / f"{job.job_id}.json"
        
        job_data = {
            "job_id": job.job_id,
            "model": job.model,
            "base_model": job.base_model,
            "status": job.status,
            "training_data_path": str(job.training_data_path),
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "metrics": job.metrics
        }
        
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)

