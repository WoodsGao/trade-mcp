"""Binance 交易服务模块 - 使用官方 Python SDK"""

from binance.client import Client
from binance.enums import *
from binance.helpers import round_step_size
from typing import Optional, Dict, List
from datetime import datetime
from ..config.settings import get_settings


class BinanceService:
    """Binance 交易所服务封装"""
    
    def __init__(self):
        settings = get_settings()
        self.client = None
        self.futures_client = None
        self._configured = False
        self._public_only = False
        self._futures_mode = False
        
        try:
            if settings.binance_configured:
                # 初始化 Binance 客户端
                # python-binance 支持 demo=True 参数启用 Demo Trading
                self.client = Client(
                    api_key=settings.BINANCE_API_KEY,
                    api_secret=settings.BINANCE_API_SECRET,
                    demo=settings.binance_demo
                )
                
                # 期货客户端 - python-binance 已内置期货支持
                self._futures_mode = settings.binance_futures
                if self._futures_mode:
                    print("期货交易功能已启用（使用 Client 内置方法）")
                
                # 同步服务器时间
                try:
                    server_time = self.client.get_server_time()
                    local_time = int(datetime.now().timestamp() * 1000)
                    time_offset = server_time['serverTime'] - local_time
                    self.client.timestamp_offset = time_offset
                    print(f"已同步服务器时间（偏移: {time_offset}ms）")
                except Exception as e:
                    print(f"警告：无法同步服务器时间：{e}")
                
                if settings.binance_demo:
                    print("使用 Binance Demo Trading（模拟交易）")
                else:
                    print("使用 Binance 正式网络")
                
                # 设置交易类型
                if settings.binance_futures:
                    print("使用合约交易（期货）")
                else:
                    print("使用现货交易")
                
                self._configured = True
                print("Binance 初始化成功（完整模式）")
            else:
                # 公开数据模式
                self.client = Client()
                self._public_only = True
                print("Binance 初始化成功（公开数据模式 - 无需 API Key）")
                print("提示：设置 BINANCE_API_KEY 和 BINANCE_API_SECRET 可启用交易功能")
                
        except Exception as e:
            print(f"初始化 Binance 连接失败：{e}")
            self._init_public_mode()
    
    def _init_public_mode(self):
        """初始化公开数据模式"""
        try:
            self.client = Client()
            self._public_only = True
            self._configured = False
            print("已切换到公开数据模式")
        except Exception as e:
            print(f"公开数据模式初始化失败：{e}")
            self._public_only = False
            self._configured = False
    
    def is_configured(self) -> bool:
        """检查服务是否已配置（完整模式）"""
        return self._configured
    
    def can_fetch_public_data(self) -> bool:
        """检查是否可以获取公开数据"""
        return self._configured or self._public_only
    
    def get_balance(self) -> dict:
        """获取现货账户余额"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            balance = self.client.get_account()
            
            available = {}
            total = {}
            
            for asset in balance['balances']:
                free = float(asset['free'])
                locked = float(asset['locked'])
                total_balance = free + locked
                
                if total_balance > 0:
                    available[asset['asset']] = free
                    total[asset['asset']] = total_balance
            
            return {
                "available": available,
                "total": total,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
            
        except Exception as e:
            return {"error": f"获取余额失败：{str(e)}"}
    
    def get_positions(self, symbol: Optional[str] = None) -> dict:
        """获取合约持仓信息"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            positions = self.client.futures_position_information()
            
            active_positions = []
            for pos in positions:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    pnl = float(pos['unRealizedProfit'])
                    entry = float(pos['entryPrice'])
                    initial_margin = float(pos.get('initialMargin', 1))
                    percentage = (pnl / initial_margin * 100) if initial_margin > 0 else 0
                    
                    active_positions.append({
                        'symbol': pos['symbol'],
                        'contracts': abs(position_amt),
                        'entryPrice': entry,
                        'markPrice': float(pos['markPrice']),
                        'unrealizedPnl': pnl,
                        'side': 'LONG' if position_amt > 0 else 'SHORT',
                        'percentage': percentage
                    })
            
            if symbol:
                symbol_formatted = symbol.replace('/', '')
                active_positions = [p for p in active_positions if p['symbol'] == symbol_formatted]
            
            return {
                "positions": active_positions,
                "count": len(active_positions)
            }
            
        except Exception as e:
            return {"error": f"获取持仓失败：{str(e)}"}
    
    def place_order(
        self, 
        symbol: str, 
        order_type: str, 
        side: str, 
        amount: float, 
        price: Optional[float] = None,
        params: Optional[dict] = None
    ) -> dict:
        """下单交易（支持现货和期货）"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            symbol_formatted = symbol.replace('/', '')
            
            if order_type == "limit" and price is None:
                return {"error": "限价订单需要指定价格"}
            
            # 根据期货模式选择不同的 API
            if self._futures_mode:
                # 期货下单
                if order_type == "market":
                    order = self.client.futures_create_order(
                        symbol=symbol_formatted,
                        side=SIDE_BUY if side == "buy" else SIDE_SELL,
                        type=ORDER_TYPE_MARKET,
                        quantity=amount
                    )
                else:
                    order = self.client.futures_create_order(
                        symbol=symbol_formatted,
                        side=SIDE_BUY if side == "buy" else SIDE_SELL,
                        type=ORDER_TYPE_LIMIT,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=amount,
                        price=str(price)
                    )
                
                return {
                    "id": str(order['orderId']),
                    "symbol": order['symbol'],
                    "type": order['type'],
                    "side": order['side'],
                    "amount": float(order['origQty']),
                    "price": float(order['price']) if order['price'] != '0' else None,
                    "status": order['status'],
                    "timestamp": order['updateTime'],
                    "mode": "futures"
                }
            else:
                # 现货下单
                if order_type == "market":
                    order = self.client.create_order(
                        symbol=symbol_formatted,
                        side=SIDE_BUY if side == "buy" else SIDE_SELL,
                        type=ORDER_TYPE_MARKET,
                        quantity=amount
                    )
                else:
                    order = self.client.create_order(
                        symbol=symbol_formatted,
                        side=SIDE_BUY if side == "buy" else SIDE_SELL,
                        type=ORDER_TYPE_LIMIT,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=amount,
                        price=str(price)
                    )
                
                return {
                    "id": str(order['orderId']),
                    "symbol": order['symbol'],
                    "type": order['type'],
                    "side": order['side'],
                    "amount": float(order['origQty']),
                    "price": float(order['price']) if order['price'] != '0' else None,
                    "status": order['status'],
                    "timestamp": order['transactTime'],
                    "mode": "spot"
                }
            
        except Exception as e:
            return {"error": f"下单失败：{str(e)}"}
    
    def cancel_order(self, order_id: str, symbol: str) -> dict:
        """取消订单"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            symbol_formatted = symbol.replace('/', '')
            result = self.client.cancel_order(
                symbol=symbol_formatted,
                orderId=int(order_id)
            )
            
            return {
                "id": str(result['orderId']),
                "symbol": result['symbol'],
                "status": result['status'],
                "cancelled": True
            }
            
        except Exception as e:
            return {"error": f"取消订单失败：{str(e)}"}
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """获取订单簿数据"""
        if not self.can_fetch_public_data():
            return {"error": "无法获取数据"}
        
        try:
            symbol_formatted = symbol.replace('/', '')
            orderbook = self.client.get_order_book(symbol=symbol_formatted, limit=limit)
            
            return {
                "symbol": symbol,
                "bids": orderbook['bids'],
                "asks": orderbook['asks'],
                "timestamp": int(datetime.now().timestamp() * 1000),
                "nonce": None
            }
            
        except Exception as e:
            return {"error": f"获取订单簿失败：{str(e)}"}
    
    def get_tickers(self, symbols: Optional[list] = None) -> dict:
        """获取行情数据"""
        if not self.can_fetch_public_data():
            return {"error": "无法获取数据"}
        
        try:
            if symbols:
                result = {}
                for symbol in symbols:
                    symbol_formatted = symbol.replace('/', '')
                    ticker = self.client.get_symbol_ticker(symbol=symbol_formatted)
                    ticker_24hr = self.client.get_ticker(symbol=symbol_formatted)
                    
                    result[symbol] = {
                        'last': float(ticker['price']),
                        'bid': None,
                        'ask': None,
                        'high': float(ticker_24hr['highPrice']),
                        'low': float(ticker_24hr['lowPrice']),
                        'volume': float(ticker_24hr['volume']),
                        'change': float(ticker_24hr['priceChangePercent']),
                        'timestamp': int(datetime.now().timestamp() * 1000)
                    }
                return result
            else:
                tickers = self.client.get_all_tickers()
                result = {}
                for ticker in tickers:
                    result[ticker['symbol']] = {
                        'last': float(ticker['price']),
                        'timestamp': int(datetime.now().timestamp() * 1000)
                    }
                return result
            
        except Exception as e:
            return {"error": f"获取行情失败：{str(e)}"}
    
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> dict:
        """获取 K 线数据"""
        if not self.can_fetch_public_data():
            return {"error": "无法获取数据"}
        
        try:
            symbol_formatted = symbol.replace('/', '')
            
            # 转换时间周期格式
            interval_map = {
                '1m': Client.KLINE_INTERVAL_1MINUTE,
                '5m': Client.KLINE_INTERVAL_5MINUTE,
                '15m': Client.KLINE_INTERVAL_15MINUTE,
                '1h': Client.KLINE_INTERVAL_1HOUR,
                '4h': Client.KLINE_INTERVAL_4HOUR,
                '1d': Client.KLINE_INTERVAL_1DAY,
                '1w': Client.KLINE_INTERVAL_1WEEK
            }
            
            interval = interval_map.get(timeframe, Client.KLINE_INTERVAL_1DAY)
            
            klines = self.client.get_klines(
                symbol=symbol_formatted,
                interval=interval,
                limit=limit
            )
            
            candles = []
            for kline in klines:
                candles.append({
                    'timestamp': kline[0],
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "count": len(candles),
                "candles": candles
            }
            
        except Exception as e:
            return {"error": f"获取 K 线数据失败：{str(e)}"}
    
    def get_trades(self, symbol: str, limit: int = 50) -> dict:
        """获取最近的成交记录"""
        if not self.can_fetch_public_data():
            return {"error": "无法获取数据"}
        
        try:
            symbol_formatted = symbol.replace('/', '')
            trades = self.client.get_recent_trades(symbol=symbol_formatted, limit=limit)
            
            result = []
            for trade in trades:
                result.append({
                    'id': trade['id'],
                    'timestamp': trade['time'],
                    'datetime': datetime.fromtimestamp(trade['time'] / 1000).isoformat(),
                    'symbol': symbol,
                    'side': 'buy' if trade['isBuyerMaker'] else 'sell',
                    'price': float(trade['price']),
                    'amount': float(trade['qty']),
                    'cost': float(trade['price']) * float(trade['qty'])
                })
            
            return {
                "symbol": symbol,
                "count": len(result),
                "trades": result
            }
            
        except Exception as e:
            return {"error": f"获取成交记录失败：{str(e)}"}
    
    def get_margin_balance(self) -> dict:
        """获取保证金账户余额"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            balance = self.client.get_margin_account()
            
            available = {}
            total = {}
            borrowed = {}
            
            for asset in balance['userAssets']:
                free = float(asset['free'])
                locked = float(asset['locked'])
                borrowed_amt = float(asset['borrowed'])
                total_balance = free + locked
                
                if total_balance > 0 or borrowed_amt > 0:
                    available[asset['asset']] = free
                    total[asset['asset']] = total_balance
                    if borrowed_amt > 0:
                        borrowed[asset['asset']] = borrowed_amt
            
            return {
                "available": available,
                "total": total,
                "borrowed": borrowed,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
            
        except Exception as e:
            return {"error": f"获取保证金余额失败：{str(e)}"}
    
    def get_margin_positions(self, symbols: Optional[list] = None) -> dict:
        """获取保证金持仓信息"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            balance = self.client.get_margin_account()
            
            result = []
            for asset in balance['userAssets']:
                base_size = float(asset['free']) + float(asset['locked'])
                borrowed = float(asset['borrowed'])
                
                if base_size > 0 or borrowed > 0:
                    result.append({
                        'asset': asset['asset'],
                        'baseSize': base_size,
                        'borrowed': borrowed,
                        'interest': float(asset['interest']),
                        'netAsset': float(asset['netAsset'])
                    })
            
            return {
                "positions": result,
                "count": len(result)
            }
            
        except Exception as e:
            return {"error": f"获取保证金持仓失败：{str(e)}"}
    
    def get_margin_modes(self, symbol: Optional[str] = None) -> dict:
        """获取交易对支持的保证金模式"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            if symbol:
                symbol_formatted = symbol.replace('/', '')
                exchange_info = self.client.get_exchange_info()
                
                for s in exchange_info['symbols']:
                    if s['symbol'] == symbol_formatted:
                        return {
                            "symbol": symbol,
                            "margin_asset": s.get('marginAsset'),
                            "is_margin_capable": s.get('isMarginTradingAllowed', False),
                            "spot_margin_enabled": s.get('isSpotTradingAllowed', False)
                        }
                
                return {"error": f"未找到交易对 {symbol}"}
            else:
                exchange_info = self.client.get_exchange_info()
                margin_symbols = []
                for s in exchange_info['symbols']:
                    if s.get('isMarginTradingAllowed', False):
                        margin_symbols.append({
                            'symbol': s['symbol'],
                            'margin_asset': s.get('marginAsset')
                        })
                
                return {
                    "margin_capable_symbols": margin_symbols[:100],
                    "count": len(margin_symbols)
                }
                
        except Exception as e:
            return {"error": f"获取保证金模式失败：{str(e)}"}
    
    def get_cross_borrow_rate(self, code: Optional[str] = None) -> dict:
        """获取全仓借贷利率"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            if code:
                rate = self.client.get_cross_margin_data(
                    asset=code.upper()
                )
                return {
                    "asset": code.upper(),
                    "borrow_rate": float(rate.get('borrowRate', 0)),
                    "margin_rate": float(rate.get('marginRate', 0)),
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                rates = self.client.get_all_cross_margin_pairs()
                result = []
                for pair in rates[:50]:
                    result.append({
                        'asset': pair['asset'],
                        'borrow_rate': float(pair.get('borrowRate', 0))
                    })
                
                return {
                    "borrow_rates": result,
                    "count": len(result)
                }
                
        except Exception as e:
            return {"error": f"获取全仓借贷利率失败：{str(e)}"}
    
    def get_isolated_borrow_rate(self, symbol: Optional[str] = None) -> dict:
        """获取逐仓借贷利率"""
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            if symbol:
                symbol_formatted = symbol.replace('/', '')
                rate = self.client.get_isolated_margin_data(
                    symbol=symbol_formatted
                )
                return {
                    "symbol": symbol,
                    "base_asset_borrow_rate": float(rate[0].get('baseAsset', {}).get('borrowRate', 0)) if rate else None,
                    "quote_asset_borrow_rate": float(rate[0].get('quoteAsset', {}).get('borrowRate', 0)) if rate else None,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                rates = self.client.get_all_isolated_margin_pairs()
                result = []
                for pair in rates[:50]:
                    result.append({
                        'symbol': pair['symbol'],
                        'base_borrow_rate': float(pair.get('baseAsset', {}).get('borrowRate', 0)),
                        'quote_borrow_rate': float(pair.get('quoteAsset', {}).get('borrowRate', 0))
                    })
                
                return {
                    "borrow_rates": result,
                    "count": len(result)
                }
                
        except Exception as e:
            return {"error": f"获取逐仓借贷利率失败：{str(e)}"}


_service_instance = None

def get_binance_service() -> BinanceService:
    """获取 Binance 服务实例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = BinanceService()
    return _service_instance
