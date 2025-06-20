"""
Base tool class for agent capabilities.

This follows the Model Context Protocol (MCP) pattern for tool definitions
and can be easily extended for various external API integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from dataclasses import dataclass
import structlog


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata or {}
        }


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: str = "string"  # string, number, boolean, object, array
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


class BaseTool(ABC):
    """Base class for all agent tools."""
    
    def __init__(self):
        self.logger = structlog.get_logger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for agents."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """Tool parameters definition."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with provided parameters.
        
        Args:
            **kwargs: Parameter values
            
        Returns:
            ToolResult with execution outcome
        """
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate provided parameters against the tool's parameter definitions.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}
        
        # Check required parameters
        required_params = {p.name for p in self.parameters if p.required}
        provided_params = set(parameters.keys())
        
        missing_params = required_params - provided_params
        if missing_params:
            errors["missing_required"] = f"Missing required parameters: {', '.join(missing_params)}"
        
        # Check parameter types (basic validation)
        for param in self.parameters:
            if param.name in parameters:
                value = parameters[param.name]
                
                # Type checking
                if param.type == "string" and not isinstance(value, str):
                    errors[param.name] = f"Expected string, got {type(value).__name__}"
                elif param.type == "number" and not isinstance(value, (int, float)):
                    errors[param.name] = f"Expected number, got {type(value).__name__}"
                elif param.type == "boolean" and not isinstance(value, bool):
                    errors[param.name] = f"Expected boolean, got {type(value).__name__}"
                
                # Enum validation
                if param.enum and value not in param.enum:
                    errors[param.name] = f"Value must be one of: {', '.join(param.enum)}"
        
        return errors
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the tool schema for agent consumption.
        
        Returns:
            Tool schema following MCP format
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                        **({"enum": param.enum} if param.enum else {}),
                        **({"default": param.default} if param.default is not None else {})
                    }
                    for param in self.parameters
                },
                "required": [param.name for param in self.parameters if param.required]
            }
        }
    
    async def safe_execute(self, **kwargs) -> ToolResult:
        """
        Safely execute the tool with error handling and validation.
        
        Args:
            **kwargs: Parameter values
            
        Returns:
            ToolResult with execution outcome
        """
        try:
            # Validate parameters
            validation_errors = self.validate_parameters(kwargs)
            if validation_errors:
                return ToolResult(
                    success=False,
                    error=f"Parameter validation failed: {validation_errors}",
                    metadata={"validation_errors": validation_errors}
                )
            
            # Execute the tool
            self.logger.info(f"Executing tool {self.name}", parameters=kwargs)
            result = await self.execute(**kwargs)
            
            self.logger.info(f"Tool {self.name} executed successfully", 
                           success=result.success, 
                           has_data=result.data is not None)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Tool {self.name} execution failed", error=str(e))
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
                metadata={"exception_type": type(e).__name__}
            ) 