"""Finnhub 数据服务模块"""

import finnhub
from typing import Optional
from datetime import datetime, timedelta
from ..config.settings import get_settings


class FinnhubService:
    """Finnhub API 服务封装"""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.FINNHUB_API_KEY
        self.client = finnhub.Client(api_key=self.api_key) if settings.finnhub_configured else None
        self._configured = settings.finnhub_configured
    
    def is_configured(self) -> bool:
        """检查服务是否已配置"""
        return self._configured
    
    def get_news(self, symbol: str, limit: int = 10) -> list[dict]:
        """
        获取指定标的的新闻
        
        Args:
            symbol: 股票代码或加密货币符号（如 AAPL, BTCUSD）
            limit: 返回新闻数量限制
            
        Returns:
            新闻列表
        """
        if not self._configured:
            return {"error": "Finnhub API 未配置"}
        
        try:
            # 获取最近 7 天的新闻
            to_date = datetime.now()
            from_date = to_date - timedelta(days=7)
            
            news = self.client.company_news(
                symbol=symbol.upper(),
                _from=from_date.strftime("%Y-%m-%d"),
                to=to_date.strftime("%Y-%m-%d")
            )
            
            # 限制返回数量并格式化
            if news:
                return news[:limit]
            return []
            
        except Exception as e:
            return {"error": f"获取新闻失败：{str(e)}"}
    
    def get_market_news(self, category: str = "general", min_id: int = 0) -> list[dict]:
        """
        获取市场新闻（按类别）
        
        Args:
            category: 新闻类别，可选值：general, forex, crypto, merger
            min_id: 获取此ID之后的新闻，默认为0获取最新新闻
            
        Returns:
            新闻列表
        """
        if not self._configured:
            return {"error": "Finnhub API 未配置"}
        
        valid_categories = ["general", "forex", "crypto", "merger"]
        if category.lower() not in valid_categories:
            return {"error": f"无效的新闻类别，可选值：{', '.join(valid_categories)}"}
        
        try:
            news = self.client.general_news(
                category=category.lower(),
                min_id=min_id
            )
            
            return news if news else []
            
        except Exception as e:
            return {"error": f"获取市场新闻失败：{str(e)}"}
    
    def get_technical_indicators(self, symbol: str, resolution: str = "D") -> dict:
        """
        获取技术指标数据
        
        Args:
            symbol: 股票代码或加密货币符号
            resolution: K 线周期 (D=日，W=周，M=月)
            
        Returns:
            包含各种技术指标的字典
        """
        if not self._configured:
            return {"error": "Finnhub API 未配置"}
        
        try:
            # 获取多个技术指标
            indicators = {}
            
            # 获取 RSI
            try:
                rsi = self.client.technical_indicator(
                    symbol=symbol.upper(),
                    resolution=resolution,
                    _from=int((datetime.now() - timedelta(days=30)).timestamp()),
                    to=int(datetime.now().timestamp()),
                    indicator='RSI'
                )
                indicators['RSI'] = rsi
            except Exception as e:
                indicators['RSI'] = {'error': str(e)}
            
            # 获取 MACD
            try:
                macd = self.client.technical_indicator(
                    symbol=symbol.upper(),
                    resolution=resolution,
                    _from=int((datetime.now() - timedelta(days=30)).timestamp()),
                    to=int(datetime.now().timestamp()),
                    indicator='MACD'
                )
                indicators['MACD'] = macd
            except Exception as e:
                indicators['MACD'] = {'error': str(e)}
            
            # 获取 SMA
            try:
                sma = self.client.technical_indicator(
                    symbol=symbol.upper(),
                    resolution=resolution,
                    _from=int((datetime.now() - timedelta(days=30)).timestamp()),
                    to=int(datetime.now().timestamp()),
                    indicator='SMA'
                )
                indicators['SMA'] = sma
            except Exception as e:
                indicators['SMA'] = {'error': str(e)}
            
            return {
                "symbol": symbol.upper(),
                "resolution": resolution,
                "timestamp": datetime.now().isoformat(),
                "data": indicators
            }
            
        except Exception as e:
            return {"error": f"获取技术指标失败：{str(e)}"}
    
    def get_stock_quote(self, symbol: str) -> dict:
        """
        获取股票实时行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            行情数据字典
        """
        if not self._configured:
            return {"error": "Finnhub API 未配置"}
        
        try:
            quote = self.client.quote(symbol.upper())
            return {
                "symbol": symbol.upper(),
                "data": quote
            }
        except Exception as e:
            return {"error": f"获取行情失败：{str(e)}"}
    
    def get_crypto_candles(self, symbol: str, resolution: str = "D", count: int = 100) -> dict:
        """
        获取加密货币 K 线数据
        
        Args:
            symbol: 加密货币符号（如 BINANCE:BTCUSDT）
            resolution: K 线周期
            count: 返回 K 线数量
            
        Returns:
            K 线数据字典
        """
        if not self._configured:
            return {"error": "Finnhub API 未配置"}
        
        try:
            # 计算时间范围
            to_timestamp = int(datetime.now().timestamp())
            from_timestamp = to_timestamp - (count * 24 * 60 * 60)  # 默认获取 count 天的数据
            
            candles = self.client.crypto_candles(
                symbol=symbol.upper(),
                resolution=resolution,
                from_=from_timestamp,
                to=to_timestamp
            )
            
            return {
                "symbol": symbol.upper(),
                "resolution": resolution,
                "count": len(candles.get('c', [])) if candles else 0,
                "data": candles or {}
            }
            
        except Exception as e:
            return {"error": f"获取 K 线数据失败：{str(e)}"}


# 全局服务实例
_finnhub_service: Optional[FinnhubService] = None


def get_finnhub_service() -> FinnhubService:
    """获取 Finnhub 服务单例"""
    global _finnhub_service
    if _finnhub_service is None:
        _finnhub_service = FinnhubService()
    return _finnhub_service
