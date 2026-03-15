"""技术指标计算服务 - 专业级技术分析"""

import talib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .binance_service import get_binance_service


INDICATOR_CONFIG = {
    "ema_fast": 9,
    "ema_medium": 21,
    "ema_slow": 55,
    "sma_trend": 200,
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "stoch_k": 14,
    "stoch_d": 3,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2.0,
    "atr_period": 14,
    "adx_period": 14,
    "adx_threshold": 25,
    "obv_period": 20,
    "mfi_period": 14,
    "vwap_period": 20,
}


class TechnicalAnalysisService:
    """技术指标计算服务 - 专业级"""
    
    def __init__(self):
        self.binance_service = get_binance_service()
        self.config = INDICATOR_CONFIG
    
    def _fetch_ohlcv(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> Tuple[Optional[np.ndarray], Optional[str]]:
        """
        统一的 OHLCV 数据获取方法
        
        Returns:
            (ohlcv_data, error_message)
        """
        if not self.binance_service.can_fetch_public_data():
            return None, "Binance 未配置，无法获取 K 线数据"
        
        ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if "error" in ohlcv_data:
            return None, ohlcv_data["error"]
        
        ohlcv = ohlcv_data.get('candles', [])
        if not ohlcv or len(ohlcv) < 20:
            return None, "K 线数据不足，至少需要 20 根 K 线"
        
        return ohlcv, None
    
    def calculate_indicators(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> Dict:
        """
        计算多个技术指标（基础版）
        """
        ohlcv, error = self._fetch_ohlcv(symbol, timeframe, limit)
        if error:
            return {"error": error}
        
        try:
            
            if not ohlcv or len(ohlcv) < 50:
                return {"error": "K 线数据不足，至少需要 50 根 K 线"}
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 转换为 numpy 数组
            open_price = df['open'].values
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            volume = df['volume'].values
            
            indicators = {}
            
            indicators['SMA_20'] = self._safe_array(talib.SMA(close_price, timeperiod=20))
            indicators['SMA_50'] = self._safe_array(talib.SMA(close_price, timeperiod=50))
            indicators['EMA_12'] = self._safe_array(talib.EMA(close_price, timeperiod=12))
            indicators['EMA_26'] = self._safe_array(talib.EMA(close_price, timeperiod=26))
            indicators['RSI_14'] = self._safe_array(talib.RSI(close_price, timeperiod=14))
            
            macd, macdsignal, macdhist = talib.MACD(close_price, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['MACD'] = self._safe_array(macd)
            indicators['MACD_Signal'] = self._safe_array(macdsignal)
            indicators['MACD_Hist'] = self._safe_array(macdhist)
            
            upper, middle, lower = talib.BBANDS(close_price, timeperiod=20, nbdevup=2, nbdevdn=2)
            indicators['BB_Upper'] = self._safe_array(upper)
            indicators['BB_Middle'] = self._safe_array(middle)
            indicators['BB_Lower'] = self._safe_array(lower)
            
            indicators['ATR_14'] = self._safe_array(talib.ATR(high_price, low_price, close_price, timeperiod=14))
            indicators['OBV'] = self._safe_array(talib.OBV(close_price, volume))
            indicators['MOM_10'] = self._safe_array(talib.MOM(close_price, timeperiod=10))
            indicators['WILLR'] = self._safe_array(talib.WILLR(high_price, low_price, close_price, timeperiod=14))
            indicators['CCI_14'] = self._safe_array(talib.CCI(high_price, low_price, close_price, timeperiod=14))
            
            slowk, slowd = talib.STOCH(high_price, low_price, close_price, 
                                       fastk_period=5, slowk_period=3, slowk_matype=0, 
                                       slowd_period=3, slowd_matype=0)
            indicators['STOCH_K'] = self._safe_array(slowk)
            indicators['STOCH_D'] = self._safe_array(slowd)
            
            window = self.config.get('vwap_period', 20)
            typical_price = (high_price + low_price + close_price) / 3
            indicators['Rolling_VWAP'] = self._safe_array(self._calculate_rolling_vwap(typical_price, volume, window))
            
            latest_indicators = {}
            for key, value in indicators.items():
                if value is not None and len(value) > 0:
                    latest_val = value[-1]
                    latest_indicators[key] = float(latest_val) if not np.isnan(latest_val) else None
            
            latest_ohlcv = {
                "timestamp": int(ohlcv[-1]['timestamp']),
                "datetime": datetime.fromtimestamp(ohlcv[-1]['timestamp'] / 1000).isoformat(),
                "open": float(ohlcv[-1]['open']),
                "high": float(ohlcv[-1]['high']),
                "low": float(ohlcv[-1]['low']),
                "close": float(ohlcv[-1]['close']),
                "volume": float(ohlcv[-1]['volume'])
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
            import traceback
            error_msg = f"计算技术指标失败：{str(e)}"
            print(f"[Technical Analysis Error] {error_msg}")
            traceback.print_exc()
            return {"error": error_msg}
    
    def comprehensive_analysis(self, symbol: str, timeframes: List[str] = None, 
                               analysis_type: str = "full") -> Dict:
        """
        综合技术分析报告
        
        Args:
            symbol: 交易对
            timeframes: 时间周期列表，默认 ["4h", "1d"]
            analysis_type: 分析类型 "full" | "quick" | "custom"
        """
        if not self.binance_service.can_fetch_public_data():
            return {"error": "Binance 未配置"}
        
        if timeframes is None:
            timeframes = ["4h", "1d"]
        
        try:
            primary_tf = timeframes[0] if timeframes else "1d"
            ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=primary_tf, limit=200)
            if "error" in ohlcv_data:
                return ohlcv_data
            ohlcv = ohlcv_data.get('candles', [])
            
            if not ohlcv or len(ohlcv) < 20:
                return {"error": f"K线数据不足，至少需要 20 根 K 线，当前只有 {len(ohlcv)} 根"}
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            open_price = df['open'].values
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            volume = df['volume'].values
            current_price = float(close_price[-1])
            
            trend_analysis = self._analyze_trend(open_price, high_price, low_price, close_price, volume)
            momentum_analysis = self._analyze_momentum(high_price, low_price, close_price, volume)
            volume_analysis = self._analyze_volume(close_price, high_price, low_price, volume)
            volatility_analysis = self._analyze_volatility(high_price, low_price, close_price)
            
            support_resistance = self._identify_support_resistance(high_price, low_price, close_price, volume)
            
            overall_signal, signal_score, signal_components = self._generate_overall_signal(
                trend_analysis, momentum_analysis, volume_analysis, volatility_analysis
            )
            
            risk_management = self._calculate_risk_management(
                current_price, 
                volatility_analysis.get('atr', 0),
                support_resistance
            )
            
            warnings = self._generate_warnings(
                trend_analysis, momentum_analysis, volume_analysis, volatility_analysis
            )
            
            return {
                "symbol": symbol,
                "timeframe": primary_tf,
                "timestamp": datetime.now().isoformat(),
                "current_price": current_price,
                "trend": trend_analysis,
                "momentum": momentum_analysis,
                "volume": volume_analysis,
                "volatility": volatility_analysis,
                "signals": {
                    "overall": overall_signal,
                    "score": signal_score,
                    "components": signal_components
                },
                "key_levels": {
                    "resistance": support_resistance.get('resistance', [])[:3],
                    "support": support_resistance.get('support', [])[:3],
                    "pivot": support_resistance.get('pivot', current_price)
                },
                "risk_management": risk_management,
                "warnings": warnings,
                "analysis_type": analysis_type
            }
            
        except Exception as e:
            return {"error": f"综合分析失败：{str(e)}"}
    
    def trend_strength(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> Dict:
        """
        趋势强度分析（ADX/DMI系统）
        """
        if not self.binance_service.can_fetch_public_data():
            return {"error": "Binance 未配置"}
        
        try:
            ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if "error" in ohlcv_data:
                return ohlcv_data
            ohlcv = ohlcv_data.get('candles', [])
            
            if not ohlcv or len(ohlcv) < 50:
                return {"error": "K线数据不足"}
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            current_price = float(close_price[-1])
            
            adx = talib.ADX(high_price, low_price, close_price, timeperiod=14)
            plus_di = talib.PLUS_DI(high_price, low_price, close_price, timeperiod=14)
            minus_di = talib.MINUS_DI(high_price, low_price, close_price, timeperiod=14)
            
            adx_val = float(adx[-1]) if not np.isnan(adx[-1]) else 0
            plus_di_val = float(plus_di[-1]) if not np.isnan(plus_di[-1]) else 0
            minus_di_val = float(minus_di[-1]) if not np.isnan(minus_di[-1]) else 0
            
            if adx_val >= 50:
                trend_strength_desc = "very_strong"
            elif adx_val >= 25:
                trend_strength_desc = "strong"
            elif adx_val >= 20:
                trend_strength_desc = "weak"
            else:
                trend_strength_desc = "no_trend"
            
            if plus_di_val > minus_di_val:
                trend_direction = "bullish"
            elif minus_di_val > plus_di_val:
                trend_direction = "bearish"
            else:
                trend_direction = "neutral"
            
            if adx_val >= 25:
                trend_type = "trending"
            else:
                trend_type = "ranging"
            
            ema9 = talib.EMA(close_price, timeperiod=9)
            ema21 = talib.EMA(close_price, timeperiod=21)
            ema55 = talib.EMA(close_price, timeperiod=55)
            
            ema9_val = float(ema9[-1]) if not np.isnan(ema9[-1]) else current_price
            ema21_val = float(ema21[-1]) if not np.isnan(ema21[-1]) else current_price
            ema55_val = float(ema55[-1]) if not np.isnan(ema55[-1]) else current_price
            
            ema_alignment = "bullish" if ema9_val > ema21_val > ema55_val else \
                           "bearish" if ema9_val < ema21_val < ema55_val else "mixed"
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "current_price": current_price,
                "adx": round(adx_val, 2),
                "plus_di": round(plus_di_val, 2),
                "minus_di": round(minus_di_val, 2),
                "trend_direction": trend_direction,
                "trend_strength": trend_strength_desc,
                "trend_type": trend_type,
                "ema_alignment": ema_alignment,
                "ema_values": {
                    "ema9": round(ema9_val, 4),
                    "ema21": round(ema21_val, 4),
                    "ema55": round(ema55_val, 4)
                },
                "interpretation": self._interpret_adx(adx_val, plus_di_val, minus_di_val)
            }
            
        except Exception as e:
            return {"error": f"趋势强度分析失败：{str(e)}"}
    
    def multi_timeframe_analysis(self, symbol: str, timeframes: List[str] = None) -> Dict:
        """
        多周期共振分析
        """
        if not self.binance_service.can_fetch_public_data():
            return {"error": "Binance 未配置"}
        
        if timeframes is None:
            timeframes = ["1h", "4h", "1d", "1w"]
        
        try:
            timeframe_signals = {}
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0
            
            for tf in timeframes:
                limit = 100 if tf != "1w" else 52
                ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=tf, limit=limit)
                if "error" in ohlcv_data:
                    timeframe_signals[tf] = ohlcv_data
                    continue
                ohlcv = ohlcv_data.get('candles', [])
                
                if not ohlcv or len(ohlcv) < 50:
                    timeframe_signals[tf] = {"error": "数据不足"}
                    continue
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                close_price = df['close'].values
                high_price = df['high'].values
                low_price = df['low'].values
                volume = df['volume'].values
                
                signal = self._calculate_single_timeframe_signal(close_price, high_price, low_price, volume)
                timeframe_signals[tf] = signal
                
                if signal.get('trend') == 'bullish':
                    bullish_count += 1
                elif signal.get('trend') == 'bearish':
                    bearish_count += 1
                else:
                    neutral_count += 1
            
            total = len(timeframes)
            alignment_score = max(bullish_count, bearish_count) / total * 100 if total > 0 else 0
            
            if bullish_count > bearish_count and bullish_count >= total * 0.6:
                conclusion = "strong_alignment_bullish"
            elif bearish_count > bullish_count and bearish_count >= total * 0.6:
                conclusion = "strong_alignment_bearish"
            elif bullish_count > bearish_count:
                conclusion = "moderate_alignment_bullish"
            elif bearish_count > bullish_count:
                conclusion = "moderate_alignment_bearish"
            else:
                conclusion = "mixed_signals"
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "timeframes_analyzed": timeframes,
                "alignment_score": round(alignment_score, 1),
                "timeframe_signals": timeframe_signals,
                "summary": {
                    "bullish_count": bullish_count,
                    "bearish_count": bearish_count,
                    "neutral_count": neutral_count
                },
                "conclusion": conclusion,
                "recommendation": self._get_mtf_recommendation(conclusion)
            }
            
        except Exception as e:
            return {"error": f"多周期分析失败：{str(e)}"}
    
    def pattern_recognition(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> Dict:
        """
        K线形态识别
        """
        if not self.binance_service.can_fetch_public_data():
            return {"error": "Binance 未配置"}
        
        try:
            ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if "error" in ohlcv_data:
                return ohlcv_data
            ohlcv = ohlcv_data.get('candles', [])
            
            if not ohlcv or len(ohlcv) < 50:
                return {"error": "K线数据不足"}
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            open_price = df['open'].values
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            
            patterns = []
            
            candlestick_patterns = [
                ('CDLDOJI', 'doji', 'neutral'),
                ('CDLHAMMER', 'hammer', 'bullish'),
                ('CDLHANGINGMAN', 'hanging_man', 'bearish'),
                ('CDLENGULFING', 'engulfing', 'both'),
                ('CDLMORNINGSTAR', 'morning_star', 'bullish'),
                ('CDLEVENINGSTAR', 'evening_star', 'bearish'),
                ('CDLSHOOTINGSTAR', 'shooting_star', 'bearish'),
                ('CDL3WHITESOLDIERS', 'three_white_soldiers', 'bullish'),
                ('CDL3BLACKCROWS', 'three_black_crows', 'bearish'),
                ('CDLHARAMI', 'harami', 'both'),
                ('CDLPIERCING', 'piercing', 'bullish'),
                ('CDLDARKCLOUDCOVER', 'dark_cloud_cover', 'bearish'),
                ('CDLTASUKIGAP', 'tasuki_gap', 'both'),
                ('CDLKICKING', 'kicking', 'both'),
                ('CDLABANDONEDBABY', 'abandoned_baby', 'bullish'),
            ]
            
            for pattern_name, display_name, signal_type in candlestick_patterns:
                try:
                    pattern_func = getattr(talib, pattern_name)
                    result = pattern_func(open_price, high_price, low_price, close_price)
                    
                    if len(result) > 0 and result[-1] != 0:
                        strength = abs(int(result[-1]))
                        patterns.append({
                            "name": display_name,
                            "signal": signal_type if signal_type != 'both' else ('bullish' if result[-1] > 0 else 'bearish'),
                            "strength": strength,
                            "position": "last_candle"
                        })
                except Exception:
                    continue
            
            chart_patterns = self._detect_chart_patterns(df)
            
            bullish_patterns = [p for p in patterns if p['signal'] == 'bullish']
            bearish_patterns = [p for p in patterns if p['signal'] == 'bearish']
            
            if len(bullish_patterns) > len(bearish_patterns):
                overall_signal = "bullish"
            elif len(bearish_patterns) > len(bullish_patterns):
                overall_signal = "bearish"
            else:
                overall_signal = "neutral"
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "current_price": float(close_price[-1]),
                "candlestick_patterns": patterns[:10],
                "chart_patterns": chart_patterns,
                "summary": {
                    "bullish_count": len(bullish_patterns),
                    "bearish_count": len(bearish_patterns),
                    "total_patterns": len(patterns)
                },
                "overall_signal": overall_signal
            }
            
        except Exception as e:
            return {"error": f"形态识别失败：{str(e)}"}
    
    def support_resistance(self, symbol: str, timeframe: str = "1d", limit: int = 200) -> Dict:
        """
        支撑阻力分析
        """
        if not self.binance_service.can_fetch_public_data():
            return {"error": "Binance 未配置"}
        
        try:
            ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if "error" in ohlcv_data:
                return ohlcv_data
            ohlcv = ohlcv_data.get('candles', [])
            
            if not ohlcv or len(ohlcv) < 50:
                return {"error": "K线数据不足"}
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            volume = df['volume'].values
            current_price = float(close_price[-1])
            
            result = self._identify_support_resistance(high_price, low_price, close_price, volume)
            
            pivot = (float(high_price[-1]) + float(low_price[-1]) + float(close_price[-1])) / 3
            r1 = 2 * pivot - float(low_price[-1])
            s1 = 2 * pivot - float(high_price[-1])
            r2 = pivot + (float(high_price[-1]) - float(low_price[-1]))
            s2 = pivot - (float(high_price[-1]) - float(low_price[-1]))
            
            fib_levels = self._calculate_fibonacci_levels(float(np.max(high_price[-50:])), float(np.min(low_price[-50:])))
            
            nearest_resistance = None
            nearest_support = None
            
            for r in result.get('resistance', []):
                if r['price'] > current_price:
                    nearest_resistance = r
                    break
            
            for s in result.get('support', []):
                if s['price'] < current_price:
                    nearest_support = s
                    break
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "current_price": current_price,
                "resistance_levels": result.get('resistance', [])[:5],
                "support_levels": result.get('support', [])[:5],
                "pivot_points": {
                    "pivot": round(pivot, 4),
                    "r1": round(r1, 4),
                    "r2": round(r2, 4),
                    "s1": round(s1, 4),
                    "s2": round(s2, 4)
                },
                "fibonacci_levels": fib_levels,
                "nearest_resistance": nearest_resistance,
                "nearest_support": nearest_support,
                "current_zone": self._determine_price_zone(current_price, result)
            }
            
        except Exception as e:
            return {"error": f"支撑阻力分析失败：{str(e)}"}
    
    def risk_calculator(self, symbol: str, entry_price: float, account_balance: float,
                        risk_per_trade: float = 1.0, target_type: str = "atr",
                        timeframe: str = "1d") -> Dict:
        """
        风险管理计算器
        """
        if not self.binance_service.can_fetch_public_data():
            return {"error": "Binance 未配置"}
        
        try:
            ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=timeframe, limit=100)
            if "error" in ohlcv_data:
                return ohlcv_data
            ohlcv = ohlcv_data.get('candles', [])
            
            if not ohlcv or len(ohlcv) < 50:
                return {"error": "K线数据不足"}
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            
            atr = talib.ATR(high_price, low_price, close_price, timeperiod=14)
            atr_value = float(atr[-1]) if not np.isnan(atr[-1]) else entry_price * 0.02
            
            max_loss_amount = account_balance * (risk_per_trade / 100)
            
            if target_type == "atr":
                stop_loss_price = entry_price - (atr_value * 2)
                stop_loss_distance_pct = ((entry_price - stop_loss_price) / entry_price) * 100
            else:
                recent_low = float(np.min(low_price[-20:]))
                stop_loss_price = recent_low * 0.99
                stop_loss_distance_pct = ((entry_price - stop_loss_price) / entry_price) * 100
            
            position_size = max_loss_amount / (entry_price - stop_loss_price) if entry_price != stop_loss_price else 0
            position_value = position_size * entry_price
            
            take_profit_levels = []
            for rr in [1.0, 2.0, 3.0]:
                tp_price = entry_price + (entry_price - stop_loss_price) * rr
                take_profit_levels.append({
                    "price": round(tp_price, 4),
                    "rr_ratio": rr,
                    "target": f"TP{int(rr)}"
                })
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "entry_price": entry_price,
                "account_balance": account_balance,
                "risk_per_trade_pct": risk_per_trade,
                "stop_loss": {
                    "price": round(stop_loss_price, 4),
                    "distance_pct": round(stop_loss_distance_pct, 2),
                    "atr_multiple": 2.0,
                    "atr_value": round(atr_value, 4)
                },
                "take_profit_levels": take_profit_levels,
                "position_sizing": {
                    "position_size": round(position_size, 6),
                    "position_value": round(position_value, 2),
                    "max_loss_amount": round(max_loss_amount, 2),
                    "risk_reward_ratio": 2.0
                },
                "risk_assessment": {
                    "risk_level": "low" if stop_loss_distance_pct < 3 else "medium" if stop_loss_distance_pct < 5 else "high",
                    "recommended": stop_loss_distance_pct <= 5
                }
            }
            
        except Exception as e:
            return {"error": f"风险计算失败：{str(e)}"}
    
    def divergence_detector(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> Dict:
        """
        背离检测
        """
        if not self.binance_service.can_fetch_public_data():
            return {"error": "Binance 未配置"}
        
        try:
            ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if "error" in ohlcv_data:
                return ohlcv_data
            ohlcv = ohlcv_data.get('candles', [])
            
            if not ohlcv or len(ohlcv) < 50:
                return {"error": "K线数据不足"}
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            
            rsi = talib.RSI(close_price, timeperiod=14)
            macd, macdsignal, macdhist = talib.MACD(close_price, fastperiod=12, slowperiod=26, signalperiod=9)
            
            rsi_divergence = self._detect_divergence(close_price, rsi, high_price, low_price, 'rsi')
            macd_divergence = self._detect_divergence(close_price, macdhist, high_price, low_price, 'macd')
            
            divergences = []
            if rsi_divergence:
                divergences.append(rsi_divergence)
            if macd_divergence:
                divergences.append(macd_divergence)
            
            overall_signal = "neutral"
            if any(d['type'] == 'bullish' for d in divergences):
                overall_signal = "potential_bullish_reversal"
            elif any(d['type'] == 'bearish' for d in divergences):
                overall_signal = "potential_bearish_reversal"
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "current_price": float(close_price[-1]),
                "rsi_divergence": rsi_divergence,
                "macd_divergence": macd_divergence,
                "all_divergences": divergences,
                "overall_signal": overall_signal,
                "interpretation": self._interpret_divergences(divergences)
            }
            
        except Exception as e:
            return {"error": f"背离检测失败：{str(e)}"}
    
    def _analyze_trend(self, open_price, high_price, low_price, close_price, volume) -> Dict:
        """趋势分析"""
        ema9 = talib.EMA(close_price, timeperiod=9)
        ema21 = talib.EMA(close_price, timeperiod=21)
        ema55 = talib.EMA(close_price, timeperiod=55)
        sma200 = talib.SMA(close_price, timeperiod=200)
        
        adx = talib.ADX(high_price, low_price, close_price, timeperiod=14)
        plus_di = talib.PLUS_DI(high_price, low_price, close_price, timeperiod=14)
        minus_di = talib.MINUS_DI(high_price, low_price, close_price, timeperiod=14)
        
        macd, macdsignal, macdhist = talib.MACD(close_price, fastperiod=12, slowperiod=26, signalperiod=9)
        
        current_price = float(close_price[-1])
        ema9_val = float(ema9[-1]) if not np.isnan(ema9[-1]) else current_price
        ema21_val = float(ema21[-1]) if not np.isnan(ema21[-1]) else current_price
        ema55_val = float(ema55[-1]) if not np.isnan(ema55[-1]) else current_price
        sma200_val = float(sma200[-1]) if not np.isnan(sma200[-1]) else current_price
        adx_val = float(adx[-1]) if not np.isnan(adx[-1]) else 0
        plus_di_val = float(plus_di[-1]) if not np.isnan(plus_di[-1]) else 0
        minus_di_val = float(minus_di[-1]) if not np.isnan(minus_di[-1]) else 0
        
        if current_price > ema9_val > ema21_val > ema55_val:
            direction = "bullish"
            strength = min(100, adx_val + 20)
        elif current_price < ema9_val < ema21_val < ema55_val:
            direction = "bearish"
            strength = min(100, adx_val + 20)
        else:
            direction = "neutral"
            strength = adx_val
        
        confidence = "high" if adx_val >= 25 else "medium" if adx_val >= 20 else "low"
        
        return {
            "direction": direction,
            "strength": round(strength, 1),
            "confidence": confidence,
            "adx": round(adx_val, 2),
            "plus_di": round(plus_di_val, 2),
            "minus_di": round(minus_di_val, 2),
            "ema_alignment": {
                "ema9": round(ema9_val, 4),
                "ema21": round(ema21_val, 4),
                "ema55": round(ema55_val, 4),
                "sma200": round(sma200_val, 4)
            },
            "above_sma200": current_price > sma200_val
        }
    
    def _analyze_momentum(self, high_price, low_price, close_price, volume) -> Dict:
        """动量分析"""
        rsi = talib.RSI(close_price, timeperiod=14)
        slowk, slowd = talib.STOCH(high_price, low_price, close_price, 
                                   fastk_period=14, slowk_period=3, slowk_matype=0, 
                                   slowd_period=3, slowd_matype=0)
        cci = talib.CCI(high_price, low_price, close_price, timeperiod=14)
        willr = talib.WILLR(high_price, low_price, close_price, timeperiod=14)
        
        rsi_val = float(rsi[-1]) if not np.isnan(rsi[-1]) else 50
        stoch_k = float(slowk[-1]) if not np.isnan(slowk[-1]) else 50
        stoch_d = float(slowd[-1]) if not np.isnan(slowd[-1]) else 50
        cci_val = float(cci[-1]) if not np.isnan(cci[-1]) else 0
        willr_val = float(willr[-1]) if not np.isnan(willr[-1]) else -50
        
        if rsi_val >= 70:
            rsi_signal = "overbought"
        elif rsi_val <= 30:
            rsi_signal = "oversold"
        else:
            rsi_signal = "neutral"
        
        if stoch_k >= 80:
            stoch_signal = "overbought"
        elif stoch_k <= 20:
            stoch_signal = "oversold"
        else:
            stoch_signal = "neutral"
        
        return {
            "rsi": round(rsi_val, 2),
            "rsi_signal": rsi_signal,
            "stoch_k": round(stoch_k, 2),
            "stoch_d": round(stoch_d, 2),
            "stoch_signal": stoch_signal,
            "cci": round(cci_val, 2),
            "willr": round(willr_val, 2),
            "momentum_direction": "bullish" if rsi_val > 50 else "bearish"
        }
    
    def _analyze_volume(self, close_price, high_price, low_price, volume) -> Dict:
        """成交量分析"""
        obv = talib.OBV(close_price, volume)
        mfi = talib.MFI(high_price, low_price, close_price, volume, timeperiod=14)
        
        obv_val = float(obv[-1]) if not np.isnan(obv[-1]) else 0
        obv_prev = float(obv[-5]) if len(obv) > 5 and not np.isnan(obv[-5]) else obv_val
        mfi_val = float(mfi[-1]) if not np.isnan(mfi[-1]) else 50
        
        obv_trend = "rising" if obv_val > obv_prev else "falling" if obv_val < obv_prev else "flat"
        
        avg_volume = np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)
        current_volume = float(volume[-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        if mfi_val >= 80:
            mfi_signal = "overbought"
        elif mfi_val <= 20:
            mfi_signal = "oversold"
        else:
            mfi_signal = "neutral"
        
        return {
            "obv": round(obv_val, 2),
            "obv_trend": obv_trend,
            "mfi": round(mfi_val, 2),
            "mfi_signal": mfi_signal,
            "current_volume": round(current_volume, 2),
            "avg_volume": round(avg_volume, 2),
            "volume_ratio": round(volume_ratio, 2),
            "volume_trend": "high" if volume_ratio > 1.5 else "low" if volume_ratio < 0.7 else "normal"
        }
    
    def _analyze_volatility(self, high_price, low_price, close_price) -> Dict:
        """波动率分析"""
        atr = talib.ATR(high_price, low_price, close_price, timeperiod=14)
        upper, middle, lower = talib.BBANDS(close_price, timeperiod=20, nbdevup=2, nbdevdn=2)
        
        atr_val = float(atr[-1]) if not np.isnan(atr[-1]) else 0
        bb_upper = float(upper[-1]) if not np.isnan(upper[-1]) else 0
        bb_middle = float(middle[-1]) if not np.isnan(middle[-1]) else 0
        bb_lower = float(lower[-1]) if not np.isnan(lower[-1]) else 0
        current_price = float(close_price[-1])
        
        bb_width = ((bb_upper - bb_lower) / bb_middle * 100) if bb_middle > 0 else 0
        
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        
        if bb_position >= 1:
            bb_signal = "above_upper"
        elif bb_position <= 0:
            bb_signal = "below_lower"
        elif bb_position >= 0.8:
            bb_signal = "near_upper"
        elif bb_position <= 0.2:
            bb_signal = "near_lower"
        else:
            bb_signal = "middle"
        
        atr_pct = (atr_val / current_price * 100) if current_price > 0 else 0
        volatility_level = "high" if atr_pct > 3 else "medium" if atr_pct > 1.5 else "low"
        
        return {
            "atr": round(atr_val, 4),
            "atr_pct": round(atr_pct, 2),
            "volatility_level": volatility_level,
            "bb_upper": round(bb_upper, 4),
            "bb_middle": round(bb_middle, 4),
            "bb_lower": round(bb_lower, 4),
            "bb_width": round(bb_width, 2),
            "bb_position": round(bb_position, 2),
            "bb_signal": bb_signal
        }
    
    def _identify_support_resistance(self, high_price, low_price, close_price, volume) -> Dict:
        """识别支撑阻力位"""
        lookback = min(50, len(close_price))
        
        resistance_levels = []
        support_levels = []
        
        for i in range(2, lookback - 2):
            if high_price[i] > high_price[i-1] and high_price[i] > high_price[i+1] and \
               high_price[i] > high_price[i-2] and high_price[i] > high_price[i+2]:
                resistance_levels.append({
                    "price": float(high_price[i]),
                    "strength": "medium",
                    "touches": 1,
                    "type": "swing_high"
                })
            
            if low_price[i] < low_price[i-1] and low_price[i] < low_price[i+1] and \
               low_price[i] < low_price[i-2] and low_price[i] < low_price[i+2]:
                support_levels.append({
                    "price": float(low_price[i]),
                    "strength": "medium",
                    "touches": 1,
                    "type": "swing_low"
                })
        
        resistance_levels = sorted(resistance_levels, key=lambda x: x['price'], reverse=True)
        support_levels = sorted(support_levels, key=lambda x: x['price'], reverse=True)
        
        resistance_levels = self._merge_levels(resistance_levels)
        support_levels = self._merge_levels(support_levels)
        
        current_price = float(close_price[-1])
        resistance_levels = [r for r in resistance_levels if r['price'] > current_price]
        support_levels = [s for s in support_levels if s['price'] < current_price]
        
        pivot = current_price
        
        return {
            "resistance": resistance_levels[:5],
            "support": support_levels[:5],
            "pivot": round(pivot, 4)
        }
    
    def _merge_levels(self, levels: List[Dict], threshold_pct: float = 0.5) -> List[Dict]:
        """合并相近的价格水平"""
        if not levels:
            return []
        
        merged = []
        current = levels[0]
        
        for level in levels[1:]:
            if abs(level['price'] - current['price']) / current['price'] * 100 < threshold_pct:
                current['touches'] += level['touches']
                current['strength'] = 'strong' if current['touches'] >= 3 else 'medium'
            else:
                merged.append(current)
                current = level
        
        merged.append(current)
        return merged
    
    def _generate_overall_signal(self, trend, momentum, volume, volatility) -> Tuple[str, float, Dict]:
        """生成综合信号"""
        trend_score = 5
        if trend['direction'] == 'bullish':
            trend_score = 8 if trend['strength'] > 50 else 7
        elif trend['direction'] == 'bearish':
            trend_score = 3 if trend['strength'] > 50 else 4
        
        momentum_score = 5
        rsi = momentum['rsi']
        if 40 <= rsi <= 60:
            momentum_score = 5
        elif 30 <= rsi <= 40:
            momentum_score = 7
        elif 60 <= rsi <= 70:
            momentum_score = 4
        elif rsi < 30:
            momentum_score = 8
        elif rsi > 70:
            momentum_score = 2
        
        volume_score = 5
        if volume['obv_trend'] == 'rising' and volume['volume_ratio'] > 1.2:
            volume_score = 7
        elif volume['obv_trend'] == 'falling' and volume['volume_ratio'] > 1.2:
            volume_score = 3
        
        volatility_score = 5
        bb_pos = volatility['bb_position']
        if bb_pos <= 0.2:
            volatility_score = 7
        elif bb_pos >= 0.8:
            volatility_score = 3
        
        total_score = (
            trend_score * 0.30 +
            momentum_score * 0.25 +
            volume_score * 0.20 +
            volatility_score * 0.15 +
            5 * 0.10
        )
        
        if total_score >= 7:
            signal = "strong_buy"
        elif total_score >= 6:
            signal = "buy"
        elif total_score >= 5.5:
            signal = "hold_bullish"
        elif total_score >= 4.5:
            signal = "hold"
        elif total_score >= 4:
            signal = "hold_bearish"
        elif total_score >= 3:
            signal = "sell"
        else:
            signal = "strong_sell"
        
        return signal, round(total_score, 2), {
            "trend": trend_score,
            "momentum": momentum_score,
            "volume": volume_score,
            "volatility": volatility_score,
            "position": 5
        }
    
    def _calculate_risk_management(self, current_price: float, atr: float, 
                                   support_resistance: Dict) -> Dict:
        """计算风险管理参数"""
        stop_loss_atr = current_price - (atr * 2) if atr > 0 else current_price * 0.95
        
        support_levels = support_resistance.get('support', [])
        if support_levels:
            stop_loss_support = support_levels[0]['price'] * 0.99
            stop_loss = max(stop_loss_atr, stop_loss_support)
        else:
            stop_loss = stop_loss_atr
        
        take_profit_1 = current_price + (current_price - stop_loss) * 1.0
        take_profit_2 = current_price + (current_price - stop_loss) * 2.0
        take_profit_3 = current_price + (current_price - stop_loss) * 3.0
        
        risk_reward = (take_profit_2 - current_price) / (current_price - stop_loss) if current_price != stop_loss else 0
        
        return {
            "suggested_stop_loss": round(stop_loss, 4),
            "suggested_take_profit": [
                round(take_profit_1, 4),
                round(take_profit_2, 4),
                round(take_profit_3, 4)
            ],
            "risk_reward_ratio": round(risk_reward, 2),
            "position_size_pct": 2.0,
            "stop_loss_pct": round((current_price - stop_loss) / current_price * 100, 2)
        }
    
    def _generate_warnings(self, trend, momentum, volume, volatility) -> List[str]:
        """生成警告信息"""
        warnings = []
        
        if momentum['rsi'] >= 70:
            warnings.append("RSI 超买区域，注意回调风险")
        elif momentum['rsi'] <= 30:
            warnings.append("RSI 超卖区域，可能存在反弹机会")
        
        if volume['volume_ratio'] < 0.5:
            warnings.append("成交量显著萎缩，趋势可能不持续")
        
        if volatility['bb_position'] >= 0.9:
            warnings.append("价格接近布林带上轨，可能面临阻力")
        elif volatility['bb_position'] <= 0.1:
            warnings.append("价格接近布林带下轨，可能获得支撑")
        
        if trend['direction'] == 'bullish' and volume['obv_trend'] == 'falling':
            warnings.append("价格上涨但OBV下降，存在背离风险")
        elif trend['direction'] == 'bearish' and volume['obv_trend'] == 'rising':
            warnings.append("价格下跌但OBV上升，可能存在反转信号")
        
        if trend['adx'] < 20:
            warnings.append("ADX低于20，市场处于震荡状态，趋势不明确")
        
        return warnings
    
    def _calculate_single_timeframe_signal(self, close_price, high_price, low_price, volume) -> Dict:
        """计算单周期信号"""
        rsi = talib.RSI(close_price, timeperiod=14)
        ema9 = talib.EMA(close_price, timeperiod=9)
        ema21 = talib.EMA(close_price, timeperiod=21)
        adx = talib.ADX(high_price, low_price, close_price, timeperiod=14)
        
        current_price = float(close_price[-1])
        rsi_val = float(rsi[-1]) if not np.isnan(rsi[-1]) else 50
        ema9_val = float(ema9[-1]) if not np.isnan(ema9[-1]) else current_price
        ema21_val = float(ema21[-1]) if not np.isnan(ema21[-1]) else current_price
        adx_val = float(adx[-1]) if not np.isnan(adx[-1]) else 0
        
        if ema9_val > ema21_val and rsi_val > 50:
            trend = "bullish"
            signal = "buy"
        elif ema9_val < ema21_val and rsi_val < 50:
            trend = "bearish"
            signal = "sell"
        else:
            trend = "neutral"
            signal = "hold"
        
        return {
            "trend": trend,
            "signal": signal,
            "rsi": round(rsi_val, 2),
            "adx": round(adx_val, 2),
            "ema9": round(ema9_val, 4),
            "ema21": round(ema21_val, 4)
        }
    
    def _detect_chart_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """检测图表形态"""
        patterns = []
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        if len(close) < 20:
            return patterns
        
        recent_highs = high[-20:]
        recent_lows = low[-20:]
        
        if np.max(recent_highs[-10:]) < np.max(recent_highs[:10]) and \
           np.min(recent_lows[-10:]) > np.min(recent_lows[:10]):
            patterns.append({
                "name": "potential_triangle",
                "status": "forming",
                "type": "consolidation"
            })
        
        if len(close) >= 20:
            highs_idx = []
            for i in range(2, 18):
                if high[-i] > high[-i-1] and high[-i] > high[-i+1]:
                    highs_idx.append(i)
            
            if len(highs_idx) >= 2:
                if high[-highs_idx[0]] > high[-highs_idx[1]]:
                    patterns.append({
                        "name": "lower_highs",
                        "status": "confirmed",
                        "type": "bearish"
                    })
                elif high[-highs_idx[0]] < high[-highs_idx[1]]:
                    patterns.append({
                        "name": "higher_highs",
                        "status": "confirmed",
                        "type": "bullish"
                    })
        
        return patterns
    
    def _calculate_fibonacci_levels(self, high: float, low: float) -> Dict:
        """计算斐波那契回撤位"""
        diff = high - low
        return {
            "0%": round(high, 4),
            "23.6%": round(high - diff * 0.236, 4),
            "38.2%": round(high - diff * 0.382, 4),
            "50%": round(high - diff * 0.5, 4),
            "61.8%": round(high - diff * 0.618, 4),
            "78.6%": round(high - diff * 0.786, 4),
            "100%": round(low, 4)
        }
    
    def _determine_price_zone(self, current_price: float, support_resistance: Dict) -> str:
        """确定当前价格区域"""
        resistance = support_resistance.get('resistance', [])
        support = support_resistance.get('support', [])
        
        if resistance and current_price > resistance[0]['price'] * 0.98:
            return "near_resistance"
        elif support and current_price < support[0]['price'] * 1.02:
            return "near_support"
        else:
            return "between_levels"
    
    def _detect_divergence(self, price, indicator, high_price, low_price, indicator_type: str) -> Optional[Dict]:
        """检测背离"""
        lookback = min(20, len(price) - 1)
        
        price_highs_idx = []
        price_lows_idx = []
        
        for i in range(2, lookback):
            if high_price[-i] > high_price[-i-1] and high_price[-i] > high_price[-i+1]:
                price_highs_idx.append(i)
            if low_price[-i] < low_price[-i-1] and low_price[-i] < low_price[-i+1]:
                price_lows_idx.append(i)
        
        if len(price_highs_idx) >= 2:
            idx1, idx2 = price_highs_idx[0], price_highs_idx[1]
            if high_price[-idx1] > high_price[-idx2]:
                if indicator[-idx1] < indicator[-idx2]:
                    return {
                        "type": "bearish",
                        "indicator": indicator_type,
                        "confidence": 0.7,
                        "description": f"价格创新高，{indicator_type.upper()}未创新高，看跌背离"
                    }
        
        if len(price_lows_idx) >= 2:
            idx1, idx2 = price_lows_idx[0], price_lows_idx[1]
            if low_price[-idx1] < low_price[-idx2]:
                if indicator[-idx1] > indicator[-idx2]:
                    return {
                        "type": "bullish",
                        "indicator": indicator_type,
                        "confidence": 0.7,
                        "description": f"价格创新低，{indicator_type.upper()}未创新低，看涨背离"
                    }
        
        return None
    
    def _interpret_adx(self, adx: float, plus_di: float, minus_di: float) -> str:
        """解释ADX信号"""
        if adx >= 50:
            strength = "非常强"
        elif adx >= 25:
            strength = "强"
        elif adx >= 20:
            strength = "弱"
        else:
            strength = "无趋势"
        
        if plus_di > minus_di:
            direction = "上涨"
        elif minus_di > plus_di:
            direction = "下跌"
        else:
            direction = "中性"
        
        return f"趋势强度：{strength}，方向：{direction}（ADX={adx:.1f}, +DI={plus_di:.1f}, -DI={minus_di:.1f}）"
    
    def _get_mtf_recommendation(self, conclusion: str) -> str:
        """获取多周期分析建议"""
        recommendations = {
            "strong_alignment_bullish": "多周期强烈看涨共振，可考虑顺势做多",
            "strong_alignment_bearish": "多周期强烈看跌共振，可考虑顺势做空或观望",
            "moderate_alignment_bullish": "多周期偏多，建议谨慎做多，注意止损",
            "moderate_alignment_bearish": "多周期偏空，建议谨慎操作或观望",
            "mixed_signals": "多周期信号混乱，建议观望或等待更明确信号"
        }
        return recommendations.get(conclusion, "建议谨慎操作")
    
    def _interpret_divergences(self, divergences: List[Dict]) -> str:
        """解释背离信号"""
        if not divergences:
            return "未检测到明显背离信号"
        
        bullish = [d for d in divergences if d['type'] == 'bullish']
        bearish = [d for d in divergences if d['type'] == 'bearish']
        
        if len(bullish) > len(bearish):
            return f"检测到{len(bullish)}个看涨背离，可能预示上涨反转"
        elif len(bearish) > len(bullish):
            return f"检测到{len(bearish)}个看跌背离，可能预示下跌反转"
        else:
            return "同时存在看涨和看跌背离，信号不明确，建议结合其他指标"
    
    def rolling_vwap(self, symbol: str, timeframe: str = "1d", limit: int = 100, window: int = 20) -> Dict:
        """
        Rolling VWAP（滚动成交量加权平均价）
        
        VWAP = Σ(Price * Volume) / Σ(Volume)
        Rolling VWAP 在指定窗口内计算 VWAP，常用于日内交易
        
        Args:
            symbol: 交易对
            timeframe: 时间周期
            limit: K线数量
            window: 滚动窗口大小
        """
        if not self.binance_service.can_fetch_public_data():
            return {"error": "Binance 未配置"}
        
        try:
            ohlcv_data = self.binance_service.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            if "error" in ohlcv_data:
                return ohlcv_data
            
            ohlcv = ohlcv_data.get('candles', [])
            
            if not ohlcv or len(ohlcv) < window:
                return {"error": f"K线数据不足，需要至少 {window} 根 K 线，当前只有 {len(ohlcv) if ohlcv else 0} 根"}
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            high_price = df['high'].values
            low_price = df['low'].values
            close_price = df['close'].values
            volume = df['volume'].values
            
            typical_price = (high_price + low_price + close_price) / 3
            
            vwap_values = self._calculate_rolling_vwap(typical_price, volume, window)
            
            current_price = float(close_price[-1])
            current_vwap = float(vwap_values[-1]) if not np.isnan(vwap_values[-1]) else current_price
            
            prev_vwap = float(vwap_values[-2]) if len(vwap_values) > 1 and not np.isnan(vwap_values[-2]) else current_vwap
            
            vwap_distance = ((current_price - current_vwap) / current_vwap * 100) if current_vwap != 0 else 0
            
            if current_price > current_vwap:
                price_position = "above_vwap"
                signal = "bullish"
            elif current_price < current_vwap:
                price_position = "below_vwap"
                signal = "bearish"
            else:
                price_position = "at_vwap"
                signal = "neutral"
            
            avg_vwap = np.nanmean(vwap_values[-10:]) if len(vwap_values) >= 10 else current_vwap
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "window": window,
                "timestamp": datetime.now().isoformat(),
                "current_price": round(current_price, 4),
                "rolling_vwap": round(current_vwap, 4),
                "vwap_change": round(current_vwap - prev_vwap, 4),
                "price_vs_vwap": {
                    "position": price_position,
                    "distance_pct": round(vwap_distance, 2),
                    "signal": signal
                },
                "avg_vwap_10": round(float(avg_vwap), 4),
                "vwap_series": self._safe_array(vwap_values),
                "interpretation": self._interpret_vwap(current_price, current_vwap, vwap_distance)
            }
            
        except Exception as e:
            return {"error": f"Rolling VWAP 计算失败：{str(e)}"}
    
    def _calculate_rolling_vwap(self, typical_price: np.ndarray, volume: np.ndarray, window: int) -> np.ndarray:
        """
        计算滚动 VWAP
        
        VWAP = Σ(Typical Price * Volume) / Σ(Volume) within window
        """
        pv = typical_price * volume
        
        rolling_pv = np.convolve(pv, np.ones(window), mode='valid')
        rolling_vol = np.convolve(volume, np.ones(window), mode='valid')
        
        vwap = rolling_pv / rolling_vol
        
        padding = window - 1
        vwap_full = np.concatenate([np.full(padding, np.nan), vwap])
        
        return vwap_full
    
    def _interpret_vwap(self, current_price: float, vwap: float, distance_pct: float) -> str:
        """解释 VWAP 信号"""
        if abs(distance_pct) < 0.1:
            return "价格接近 VWAP，观望等待明确方向"
        elif distance_pct > 0.5:
            return f"价格高于 VWAP {distance_pct:.2f}%，多方占优，可考虑回调做多"
        elif distance_pct < -0.5:
            return f"价格低于 VWAP {abs(distance_pct):.2f}%，空方占优，可考虑反弹做空"
        else:
            return "价格与 VWAP 偏离不大，趋势震荡整理中"
    
    def _safe_array(self, arr):
        """安全处理数组"""
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
        """获取最后N个有效值"""
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
