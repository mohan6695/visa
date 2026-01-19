"""
MCP (Model Context Protocol) Configuration
Centralized MCP server configurations
"""

from .settings import settings


class MCPConfig:
    """MCP-specific configuration class"""
    
    @staticmethod
    def get_ollama_config() -> dict:
        """Get Ollama MCP server configuration"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return {
            "mcpServers": {
                "ollama": {
                    "command": "python",
                    "args": [f"{base_dir}/ollama_mcp_server.py"],
                    "disabled": False,
                    "env": {
                        "OLLAMA_URL": settings.ollama_url,
                        "OLLAMA_MODEL": settings.ollama_model,
                    }
                }
            }
        }
    
    @staticmethod
    def get_ollama_server_params() -> dict:
        """Get parameters for Ollama MCP server"""
        return {
            "base_url": settings.ollama_url,
            "default_model": settings.ollama_model,
            "embedding_model": "nomic-embed-text",
            "temperature": 0.7,
            "max_tokens": 1000,
        }
    
    @staticmethod
    def get_ai_config() -> dict:
        """Get AI provider configuration"""
        return {
            "provider": settings.ai_provider,
            "groq": {
                "api_key": settings.groq_api_key,
            },
            "openrouter": {
                "api_key": settings.openrouter_api_key,
            },
            "ollama": {
                "url": settings.ollama_url,
                "model": settings.ollama_model,
            }
        }


# Global MCP configuration instance
mcp_config = MCPConfig()
