import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # Finnhub API 配置
    FINNHUB_API_KEY: str = Field(default="", description="Finnhub API Key")
    
    # Binance API 配置
    BINANCE_API_KEY: str = Field(default="", description="Binance API Key")
    BINANCE_API_SECRET: str = Field(default="", description="Binance API Secret")
    
    # Binance 配置选项
    BINANCE_DEMO: bool = Field(default=False, description="是否使用 Binance Demo Trading 模式（模拟交易）")
    BINANCE_FUTURES: bool = Field(default=False, description="是否使用合约交易（期货），默认为现货交易")
    
    # MCP 服务器配置
    MCP_SERVER_HOST: str = Field(default="127.0.0.1", description="MCP 服务器监听地址")
    MCP_SERVER_PORT: int = Field(default=8000, description="MCP 服务器端口")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    
    @field_validator("FINNHUB_API_KEY")
    @classmethod
    def validate_finnhub_key(cls, v):
        """验证 Finnhub API Key 是否存在"""
        if not v or v == "your_finnhub_api_key_here":
            print("警告：Finnhub API Key 未配置，新闻和技术指标功能将不可用")
        return v
    
    @field_validator("BINANCE_API_KEY", "BINANCE_API_SECRET")
    @classmethod
    def validate_binance_keys(cls, v, info):
        """验证 Binance API Key 是否存在"""
        if not v or v == "your_binance_api_key_here":
            print(f"警告：Binance API 密钥未配置，交易功能将不可用")
        return v
    
    @property
    def finnhub_configured(self) -> bool:
        """检查 Finnhub 是否已配置"""
        return bool(self.FINNHUB_API_KEY) and self.FINNHUB_API_KEY != "your_finnhub_api_key_here"
    
    @property
    def binance_configured(self) -> bool:
        """检查 Binance 是否已配置"""
        return (
            bool(self.BINANCE_API_KEY) and 
            self.BINANCE_API_KEY != "your_binance_api_key_here" and
            bool(self.BINANCE_API_SECRET) and
            self.BINANCE_API_SECRET != "your_binance_api_secret_here"
        )
    
    @property
    def binance_demo(self) -> bool:
        """检查是否使用 Demo Trading 模式"""
        return self.BINANCE_DEMO
    
    @property
    def binance_futures(self) -> bool:
        """检查是否使用合约交易"""
        return self.BINANCE_FUTURES
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取全局配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    return _settings
