"""技术指标计算服务 - 使用 TA-Lib"""

import talib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .ccxt_service import get_ccxt_service


class TechnicalAnalysisService:
    """技术指标计算服务"""
    
    def __init__(self):
        self.ccxt_service = get_ccxt_service()
    
    def calculate_indicators(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> Dict:
        """
        计算多个技术指标
        
        Args:
            symbol: 交易对符号（如 BTC/USDT）
            timeframe: 时间周期（1m, 5m, 15m, 1h, 4h, 1d, 1w）
            limit: K线数量
            
        Returns:
            包含各种技术指标的字典
        """
        if not self.ccxt_service.is_configured():
            return {"error": "Binance 未配置，无法获取 K 线数据"}
        
        try:
            # 获取 K 线数据
            ohlcv = self.ccxt_service.exchange.fetch_ohlcv(
                symbol, 
                timeframe=timeframe, 
                limit=limit
            )
            
            if not ohlcv or len(ohlcv) < 50:
                return {"error": "K 线数据不足，至少需要 50 根 K 线"}
            
            # 转换为 numpy 数组
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            open_price = df['open'].values
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            volume = df['volume'].values
            
            # 计算各种技术指标
            indicators = {}
            
            # 1. 移动平均线 (MA)
            indicators['SMA_20'] = self._safe_array(talib.SMA(close_price, timeperiod=20))
            indicators['SMA_50'] = self._safe_array(talib.SMA(close_price, timeperiod=50))
            indicators['EMA_12'] = self._safe_array(talib.EMA(close_price, timeperiod=12))
            indicators['EMA_26'] = self._safe_array(talib.EMA(close_price, timeperiod=26))
            
            # 2. RSI
            indicators['RSI_14'] = self._safe_array(talib.RSI(close_price, timeperiod=14))
            
            # 3. MACD
            macd, macdsignal, macdhist = talib.MACD(close_price, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['MACD'] = self._safe_array(macd)
            indicators['MACD_Signal'] = self._safe_array(macdsignal)
            indicators['MACD_Hist'] = self._safe_array(macdhist)
            
            # 4. 布林带
            upper, middle, lower = talib.BBANDS(close_price, timeperiod=20, nbdevup=2, nbdevdn=2)
            indicators['BB_Upper'] = self._safe_array(upper)
            indicators['BB_Middle'] = self._safe_array(middle)
            indicators['BB_Lower'] = self._safe_array(lower)
            
            # 5. ATR (Average True Range)
            indicators['ATR_14'] = self._safe_array(talib.ATR(high_price, low_price, close_price, timeperiod=14))
            
            # 6. 成交量指标
            indicators['OBV'] = self._safe_array(talib.OBV(close_price, volume))
            
            # 7. 动量指标
            indicators['MOM_10'] = self._safe_array(talib.MOM(close_price, timeperiod=10))
            
            # 8. 威廉指标
            indicators['WILLR'] = self._safe_array(talib.WILLR(high_price, low_price, close_price, timeperiod=14))
            
            # 9. CCI (Commodity Channel Index)
            indicators['CCI_14'] = self._safe_array(talib.CCI(high_price, low_price, close_price, timeperiod=14))
            
            # 10. Stochastic
            slowk, slowd = talib.STOCH(high_price, low_price, close_price, 
                                       fastk_period=5, slowk_period=3, slowk_matype=0, 
                                       slowd_period=3, slowd_matype=0)
            indicators['STOCH_K'] = self._safe_array(slowk)
            indicators['STOCH_D'] = self._safe_array(slowd)
            
            # 获取最新值
            latest_indicators = {}
            for key, value in indicators.items():
                if value is not None and len(value) > 0:
                    latest_val = value[-1]
                    latest_indicators[key] = float(latest_val) if not np.isnan(latest_val) else None
            
            # 获取最新的 K 线数据
            latest_ohlcv = {
                "timestamp": int(ohlcv[-1][0]),
                "datetime": datetime.fromtimestamp(ohlcv[-1][0] / 1000).isoformat(),
                "open": float(ohlcv[-1][1]),
                "high": float(ohlcv[-1][2]),
                "low": float(ohlcv[-1][3]),
                "close": float(ohlcv[-1][4]),
                "volume": float(ohlcv[-1][5])
            }
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "data_points": len(ohlcv),
                "timestamp": datetime.now().isoformat(),
                "latest_ohlcv": latest_ohlcv,
                "indicators": latest_indicators
            }
            
        except Exception as e:
            return {"error": f"计算技术指标失败：{str(e)}"}
    
    def calculate_single_indicator(self, symbol: str, indicator: str, timeframe: str = "1d", 
                                   limit: int = 100, **kwargs) -> Dict:
        """
        计算单个技术指标
        
        Args:
            symbol: 交易对符号
            indicator: 指标名称（RSI, MACD, SMA, EMA, BB, ATR 等）
            timeframe: 时间周期
            limit: K线数量
            **kwargs: 指标参数
            
        Returns:
            包含指标数据的字典
        """
        if not self.ccxt_service.is_configured():
            return {"error": "Binance 未配置，无法获取 K 线数据"}
        
        try:
            # 获取 K 线数据
            ohlcv = self.ccxt_service.exchange.fetch_ohlcv(
                symbol, 
                timeframe=timeframe, 
                limit=limit
            )
            
            if not ohlcv or len(ohlcv) < 20:
                return {"error": "K 线数据不足"}
            
            # 转换为 numpy 数组
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            close_price = df['close'].values
            high_price = df['high'].values
            low_price = df['low'].values
            volume = df['volume'].values
            
            indicator = indicator.upper()
            result = {}
            
            if indicator == "RSI":
                period = kwargs.get('period', 14)
                rsi = talib.RSI(close_price, timeperiod=period)
                result = {
                    "name": "RSI",
                    "period": period,
                    "values": self._get_last_values(rsi, 10),
                    "latest": float(rsi[-1]) if not np.isnan(rsi[-1]) else None
                }
            
            elif indicator == "MACD":
                fast = kwargs.get('fast', 12)
                slow = kwargs.get('slow', 26)
                signal = kwargs.get('signal', 9)
                macd, macdsignal, macdhist = talib.MACD(close_price, fastperiod=fast, 
                                                        slowperiod=slow, signalperiod=signal)
                result = {
                    "name": "MACD",
                    "parameters": {"fast": fast, "slow": slow, "signal": signal},
                    "MACD": float(macd[-1]) if not np.isnan(macd[-1]) else None,
                    "Signal": float(macdsignal[-1]) if not np.isnan(macdsignal[-1]) else None,
                    "Histogram": float(macdhist[-1]) if not np.isnan(macdhist[-1]) else None,
                    "values": {
                        "MACD": self._get_last_values(macd, 10),
                        "Signal": self._get_last_values(macdsignal, 10),
                        "Histogram": self._get_last_values(macdhist, 10)
                    }
                }
            
            elif indicator in ["SMA", "EMA"]:
                period = kwargs.get('period', 20)
                if indicator == "SMA":
                    ma = talib.SMA(close_price, timeperiod=period)
                else:
                    ma = talib.EMA(close_price, timeperiod=period)
                result = {
                    "name": indicator,
                    "period": period,
                    "values": self._get_last_values(ma, 10),
                    "latest": float(ma[-1]) if not np.isnan(ma[-1]) else None
                }
            
            elif indicator == "BB" or indicator == "BOLLINGER":
                period = kwargs.get('period', 20)
                std_dev = kwargs.get('std_dev', 2)
                upper, middle, lower = talib.BBANDS(close_price, timeperiod=period, 
                                                    nbdevup=std_dev, nbdevdn=std_dev)
                result = {
                    "name": "Bollinger Bands",
                    "period": period,
                    "std_dev": std_dev,
                    "Upper": float(upper[-1]) if not np.isnan(upper[-1]) else None,
                    "Middle": float(middle[-1]) if not np.isnan(middle[-1]) else None,
                    "Lower": float(lower[-1]) if not np.isnan(lower[-1]) else None,
                    "values": {
                        "Upper": self._get_last_values(upper, 10),
                        "Middle": self._get_last_values(middle, 10),
                        "Lower": self._get_last_values(lower, 10)
                    }
                }
            
            elif indicator == "ATR":
                period = kwargs.get('period', 14)
                atr = talib.ATR(high_price, low_price, close_price, timeperiod=period)
                result = {
                    "name": "ATR",
                    "period": period,
                    "values": self._get_last_values(atr, 10),
                    "latest": float(atr[-1]) if not np.isnan(atr[-1]) else None
                }
            
            else:
                return {"error": f"不支持的指标：{indicator}"}
            
            result["symbol"] = symbol
            result["timeframe"] = timeframe
            result["timestamp"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            return {"error": f"计算指标失败：{str(e)}"}
    
    def _safe_array(self, arr):
        """安全处理数组，将 NaN 转换为 None"""
        if arr is None:
            return None
        result = []
        for val in arr:
            if np.isnan(val):
                result.append(None)
            else:
                result.append(float(val))
        return result
    
    def _get_last_values(self, arr, count: int) -> List[float]:
        """获取最后 N 个有效值"""
        if arr is None or len(arr) == 0:
            return []
        values = []
        for i in range(max(0, len(arr) - count), len(arr)):
            if not np.isnan(arr[i]):
                values.append(float(arr[i]))
        return values


_service_instance = None

def get_technical_analysis_service() -> TechnicalAnalysisService:
    """获取技术分析服务实例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = TechnicalAnalysisService()
    return _service_instance
