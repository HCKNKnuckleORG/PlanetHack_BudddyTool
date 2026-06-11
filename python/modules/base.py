"""
Base module class for all PlanetHack modules
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path


class BaseModule(ABC):
    """Base class for all security testing modules"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.name = self.__class__.__name__
        self.results = []

    @abstractmethod
    def run(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        Run the module against a target

        Args:
            target: Target URL or IP address
            **kwargs: Additional module-specific parameters

        Returns:
            Dictionary containing results
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, str]:
        """
        Get module information

        Returns:
            Dictionary with name, description, and version
        """
        pass

    def validate_target(self, target: str) -> bool:
        """Validate target format"""
        if not target:
            return False

        # Basic validation - can be enhanced
        return (
            target.startswith(("http://", "https://"))
            or target.replace(".", "").replace(":", "").isdigit()
        )

    def log_result(self, result: Dict[str, Any]):
        """Log and store result"""
        self.results.append(result)
        self.logger.info(f"Result: {result}")

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all results"""
        return self.results

    def clear_results(self):
        """Clear stored results"""
        self.results = []
