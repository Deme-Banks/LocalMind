"""
Usage tracker - tracks API calls, tokens, costs, and usage statistics
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Single usage record"""
    timestamp: str
    backend: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    response_time: float = 0.0
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class UsageTracker:
    """Tracks API usage, costs, and statistics"""
    
    # Pricing per 1M tokens (input/output) - as of 2024
    PRICING = {
        "openai": {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "default": {"input": 1.00, "output": 3.00}
        },
        "anthropic": {
            "claude-3-opus": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
            "default": {"input": 1.00, "output": 5.00}
        },
        "google": {
            "gemini-pro": {"input": 0.50, "output": 1.50},
            "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            "default": {"input": 0.50, "output": 1.50}
        },
        "mistral-ai": {
            "mistral-large": {"input": 2.00, "output": 6.00},
            "mistral-medium": {"input": 0.50, "output": 1.50},
            "mistral-small": {"input": 0.20, "output": 0.60},
            "default": {"input": 0.50, "output": 1.50}
        },
        "cohere": {
            "command-r-plus": {"input": 3.00, "output": 15.00},
            "command-r": {"input": 0.50, "output": 1.50},
            "command": {"input": 0.50, "output": 1.50},
            "default": {"input": 0.50, "output": 1.50}
        },
        "groq": {
            "default": {"input": 0.00, "output": 0.00}  # Free tier
        }
    }
    
    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize usage tracker
        
        Args:
            data_path: Path to store usage data (default: ~/.localmind/usage.json)
        """
        if data_path is None:
            data_path = Path.home() / ".localmind" / "usage.json"
        
        self.data_path = data_path
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: List[UsageRecord] = self._load_records()
        
        # Budget settings
        self.budget_settings: Dict[str, Any] = self._load_budget_settings()
    
    def _load_records(self) -> List[UsageRecord]:
        """Load usage records from file"""
        if not self.data_path.exists():
            return []
        
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                records = []
                for record_data in data.get("records", []):
                    try:
                        records.append(UsageRecord(**record_data))
                    except Exception as e:
                        logger.warning(f"Error loading record: {e}")
                        continue
                return records
        except Exception as e:
            logger.error(f"Error loading usage records: {e}")
            return []
    
    def _save_records(self):
        """Save usage records to file"""
        try:
            data = {
                "records": [record.to_dict() for record in self.records],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage records: {e}")
    
    def _load_budget_settings(self) -> Dict[str, Any]:
        """Load budget settings"""
        budget_path = self.data_path.parent / "budget.json"
        if budget_path.exists():
            try:
                with open(budget_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading budget settings: {e}")
        return {
            "daily_budget": None,
            "monthly_budget": None,
            "alert_threshold": 0.8,  # Alert at 80% of budget
            "alerts_enabled": True
        }
    
    def _save_budget_settings(self):
        """Save budget settings"""
        budget_path = self.data_path.parent / "budget.json"
        try:
            with open(budget_path, 'w') as f:
                json.dump(self.budget_settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving budget settings: {e}")
    
    def calculate_cost(
        self,
        backend: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for API call
        
        Args:
            backend: Backend name (e.g., "openai")
            model: Model name (e.g., "gpt-4")
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        if backend not in self.PRICING:
            return 0.0
        
        pricing = self.PRICING[backend]
        model_pricing = pricing.get(model, pricing.get("default", {"input": 0.0, "output": 0.0}))
        
        input_cost = (prompt_tokens / 1_000_000) * model_pricing.get("input", 0.0)
        output_cost = (completion_tokens / 1_000_000) * model_pricing.get("output", 0.0)
        
        return input_cost + output_cost
    
    def record_usage(
        self,
        backend: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        response_time: float = 0.0,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Record API usage
        
        Args:
            backend: Backend name
            model: Model name
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            response_time: Response time in seconds
            success: Whether the call was successful
            error: Error message if failed
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(backend, model, prompt_tokens, completion_tokens) if success else 0.0
        
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            backend=backend,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            response_time=response_time,
            success=success,
            error=error
        )
        
        self.records.append(record)
        
        # Keep only last 10,000 records to prevent file from growing too large
        if len(self.records) > 10000:
            self.records = self.records[-10000:]
        
        self._save_records()
        
        # Check budget alerts
        if success and self.budget_settings.get("alerts_enabled", True):
            self._check_budget_alerts()
    
    def _check_budget_alerts(self):
        """Check if budget thresholds are exceeded and log alerts"""
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        
        daily_budget = self.budget_settings.get("daily_budget")
        monthly_budget = self.budget_settings.get("monthly_budget")
        threshold = self.budget_settings.get("alert_threshold", 0.8)
        
        alerts = []
        
        if daily_budget and daily_cost >= daily_budget * threshold:
            if daily_cost >= daily_budget:
                alerts.append(f"⚠️ Daily budget exceeded! ${daily_cost:.2f} / ${daily_budget:.2f}")
            else:
                alerts.append(f"⚠️ Daily budget warning: ${daily_cost:.2f} / ${daily_budget:.2f} ({daily_cost/daily_budget*100:.1f}%)")
        
        if monthly_budget and monthly_cost >= monthly_budget * threshold:
            if monthly_cost >= monthly_budget:
                alerts.append(f"⚠️ Monthly budget exceeded! ${monthly_cost:.2f} / ${monthly_budget:.2f}")
            else:
                alerts.append(f"⚠️ Monthly budget warning: ${monthly_cost:.2f} / ${monthly_budget:.2f} ({monthly_cost/monthly_budget*100:.1f}%)")
        
        for alert in alerts:
            logger.warning(alert)
    
    def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        """Get total cost for a specific day"""
        if date is None:
            date = datetime.now()
        date_str = date.date().isoformat()
        
        total = 0.0
        for record in self.records:
            if record.timestamp.startswith(date_str) and record.success:
                total += record.cost
        return total
    
    def get_monthly_cost(self, year: Optional[int] = None, month: Optional[int] = None) -> float:
        """Get total cost for a specific month"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        total = 0.0
        for record in self.records:
            record_date = datetime.fromisoformat(record.timestamp)
            if record_date.year == year and record_date.month == month and record.success:
                total += record.cost
        return total
    
    def get_total_cost(self) -> float:
        """Get total cost across all time"""
        return sum(record.cost for record in self.records if record.success)
    
    def get_statistics(
        self,
        backend: Optional[str] = None,
        model: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics
        
        Args:
            backend: Filter by backend (optional)
            model: Filter by model (optional)
            days: Number of days to look back (optional)
            
        Returns:
            Dictionary with statistics
        """
        # Filter records
        filtered_records = self.records
        
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            filtered_records = [
                r for r in filtered_records
                if datetime.fromisoformat(r.timestamp) >= cutoff
            ]
        
        if backend:
            filtered_records = [r for r in filtered_records if r.backend == backend]
        
        if model:
            filtered_records = [r for r in filtered_records if r.model == model]
        
        if not filtered_records:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_cost": 0.0,
                "average_response_time": 0.0,
                "by_backend": {},
                "by_model": {}
            }
        
        successful = [r for r in filtered_records if r.success]
        
        # Calculate totals
        total_calls = len(filtered_records)
        successful_calls = len(successful)
        failed_calls = total_calls - successful_calls
        
        total_tokens = sum(r.total_tokens for r in filtered_records)
        prompt_tokens = sum(r.prompt_tokens for r in filtered_records)
        completion_tokens = sum(r.completion_tokens for r in filtered_records)
        total_cost = sum(r.cost for r in successful)
        
        avg_response_time = sum(r.response_time for r in successful) / successful_calls if successful_calls > 0 else 0.0
        
        # Group by backend
        by_backend: Dict[str, Dict[str, Any]] = {}
        for record in filtered_records:
            if record.backend not in by_backend:
                by_backend[record.backend] = {
                    "calls": 0,
                    "cost": 0.0,
                    "tokens": 0
                }
            by_backend[record.backend]["calls"] += 1
            if record.success:
                by_backend[record.backend]["cost"] += record.cost
                by_backend[record.backend]["tokens"] += record.total_tokens
        
        # Group by model
        by_model: Dict[str, Dict[str, Any]] = {}
        for record in filtered_records:
            if record.model not in by_model:
                by_model[record.model] = {
                    "calls": 0,
                    "cost": 0.0,
                    "tokens": 0
                }
            by_model[record.model]["calls"] += 1
            if record.success:
                by_model[record.model]["cost"] += record.cost
                by_model[record.model]["tokens"] += record.total_tokens
        
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_cost": total_cost,
            "average_response_time": avg_response_time,
            "by_backend": by_backend,
            "by_model": by_model
        }
    
    def set_budget(
        self,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
        alert_threshold: Optional[float] = None,
        alerts_enabled: Optional[bool] = None
    ):
        """
        Set budget settings
        
        Args:
            daily_budget: Daily budget in USD (None to disable)
            monthly_budget: Monthly budget in USD (None to disable)
            alert_threshold: Alert threshold (0.0-1.0, default 0.8)
            alerts_enabled: Enable/disable alerts
        """
        if daily_budget is not None:
            self.budget_settings["daily_budget"] = daily_budget
        if monthly_budget is not None:
            self.budget_settings["monthly_budget"] = monthly_budget
        if alert_threshold is not None:
            self.budget_settings["alert_threshold"] = max(0.0, min(1.0, alert_threshold))
        if alerts_enabled is not None:
            self.budget_settings["alerts_enabled"] = alerts_enabled
        
        self._save_budget_settings()
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        
        daily_budget = self.budget_settings.get("daily_budget")
        monthly_budget = self.budget_settings.get("monthly_budget")
        
        status = {
            "daily": {
                "cost": daily_cost,
                "budget": daily_budget,
                "remaining": daily_budget - daily_cost if daily_budget else None,
                "percentage": (daily_cost / daily_budget * 100) if daily_budget else None,
                "exceeded": daily_budget and daily_cost >= daily_budget
            },
            "monthly": {
                "cost": monthly_cost,
                "budget": monthly_budget,
                "remaining": monthly_budget - monthly_cost if monthly_budget else None,
                "percentage": (monthly_cost / monthly_budget * 100) if monthly_budget else None,
                "exceeded": monthly_budget and monthly_cost >= monthly_budget
            },
            "alerts_enabled": self.budget_settings.get("alerts_enabled", True),
            "alert_threshold": self.budget_settings.get("alert_threshold", 0.8)
        }
        
        return status

