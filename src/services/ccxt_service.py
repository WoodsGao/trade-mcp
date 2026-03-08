"""CCXT 交易服务模块"""

import ccxt
from typing import Optional
from ..config.settings import get_settings


class CCXTService:
    """CCXT 交易所服务封装"""
    
    def __init__(self, exchange_id: str = "binance"):
        settings = get_settings()
        self.exchange_id = exchange_id
        self.exchange = None
        self._configured = False
        
        if settings.binance_configured and exchange_id == "binance":
            try:
                # 构建交易所配置
                exchange_config = {
                    'apiKey': settings.BINANCE_API_KEY,
                    'secret': settings.BINANCE_API_SECRET,
                }
                
                # 配置 Demo Trading 模式
                if settings.binance_demo:
                    # Demo Trading - Binance 新的统一模拟交易环境（支持现货和合约）
                    exchange_config['options'] = {
                        'defaultType': 'spot',  # 默认现货
                        'demo': True,  # 启用 Demo 模式
                        'fetchCurrencies': False,
                    }
                    print("使用 Binance Demo Trading（模拟交易）")
                    print("注意：Demo 模式需要专用的 API Key，与正式网络和 Testnet 不同")
                else:
                    print("使用 Binance 正式网络")
                
                # 配置交易类型（现货/合约）
                if settings.binance_futures:
                    if 'options' not in exchange_config:
                        exchange_config['options'] = {}
                    exchange_config['options']['defaultType'] = 'future'  # 合约交易
                    print("使用合约交易（期货）")
                else:
                    if 'options' not in exchange_config:
                        exchange_config['options'] = {}
                    exchange_config['options']['defaultType'] = 'spot'  # 现货交易
                    print("使用现货交易")
                
                # 创建交易所实例
                self.exchange = ccxt.binance(exchange_config)
                
                # 启用 Demo Trading（如果配置了）
                if settings.binance_demo:
                    self.exchange.enable_demo_trading(True)
                
                # 加载交易所配置
                self.exchange.load_markets()
                
                self._configured = True
                print(f"Binance 初始化成功")
            except ccxt.AuthenticationError as e:
                print(f"Binance 认证失败：{e}")
                print("请检查：1) API Key 是否正确 2) 是否使用了正确的网络（测试网/正式网）")
                self._configured = False
            except ccxt.NetworkError as e:
                print(f"Binance 网络错误：{e}")
                print("可能原因：地区限制、网络连接问题")
                self._configured = False
            except Exception as e:
                print(f"初始化交易所连接失败：{e}")
                self._configured = False
    
    def is_configured(self) -> bool:
        """检查服务是否已配置"""
        return self._configured
    
    def get_balance(self) -> dict:
        """
        获取账户余额
        
        Returns:
            余额信息字典
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            balance = self.exchange.fetch_balance()
            # 只返回有余额的资产
            available = {}
            total = {}
            
            for currency, amount in balance.get('free', {}).items():
                if amount > 0:
                    available[currency] = amount
            
            for currency, amount in balance.get('total', {}).items():
                if amount > 0:
                    total[currency] = amount
            
            return {
                "available": available,
                "total": total,
                "timestamp": balance.get('timestamp')
            }
            
        except Exception as e:
            return {"error": f"获取余额失败：{str(e)}"}
    
    def get_positions(self, symbol: Optional[str] = None) -> dict:
        """
        获取持仓信息
        
        Args:
            symbol: 可选，指定交易对
            
        Returns:
            持仓信息字典
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            # 获取持仓
            positions = self.exchange.fetch_positions()
            
            # 过滤有持仓的数据
            active_positions = []
            for pos in positions:
                if pos.get('contracts', 0) > 0:
                    active_positions.append({
                        'symbol': pos.get('symbol'),
                        'contracts': pos.get('contracts'),
                        'entryPrice': pos.get('entryPrice'),
                        'markPrice': pos.get('markPrice'),
                        'unrealizedPnl': pos.get('unrealizedPnl'),
                        'side': pos.get('side'),
                        'percentage': pos.get('percentage')
                    })
            
            # 如果指定了 symbol，过滤结果
            if symbol:
                active_positions = [p for p in active_positions if p['symbol'] == symbol]
            
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
        """
        下单交易
        
        Args:
            symbol: 交易对（如 BTC/USDT）
            order_type: 订单类型（market, limit）
            side: 买卖方向（buy, sell）
            amount: 数量
            price: 价格（限价订单必需）
            params: 额外参数（如 marginMode: 'cross'/'isolated' 用于保证金交易）
            
        Returns:
            订单信息
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            if params is None:
                params = {}
            
            if order_type == "limit" and price is None:
                return {"error": "限价订单需要指定价格"}
            
            if order_type == "market":
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=side,
                    amount=amount,
                    params=params
                )
            else:
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=side,
                    amount=amount,
                    price=price,
                    params=params
                )
            
            return {
                "id": order.get('id'),
                "symbol": order.get('symbol'),
                "type": order.get('type'),
                "side": order.get('side'),
                "amount": order.get('amount'),
                "price": order.get('price'),
                "status": order.get('status'),
                "timestamp": order.get('timestamp')
            }
            
        except Exception as e:
            return {"error": f"下单失败：{str(e)}"}
    
    def cancel_order(self, order_id: str, symbol: str) -> dict:
        """
        取消订单
        
        Args:
            order_id: 订单 ID
            symbol: 交易对
            
        Returns:
            取消结果
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            
            return {
                "id": result.get('id'),
                "symbol": result.get('symbol'),
                "status": result.get('status'),
                "cancelled": True
            }
            
        except Exception as e:
            return {"error": f"取消订单失败：{str(e)}"}
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对
            limit: 深度限制
            
        Returns:
            订单簿数据
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit=limit)
            
            return {
                "symbol": symbol,
                "bids": orderbook.get('bids', []),
                "asks": orderbook.get('asks', []),
                "timestamp": orderbook.get('timestamp'),
                "nonce": orderbook.get('nonce')
            }
            
        except Exception as e:
            return {"error": f"获取订单簿失败：{str(e)}"}
    
    def get_tickers(self, symbols: Optional[list] = None) -> dict:
        """
        获取行情数据
        
        Args:
            symbols: 可选，指定交易对列表
            
        Returns:
            行情数据字典
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            tickers = self.exchange.fetch_tickers(symbols)
            
            # 格式化返回
            result = {}
            for symbol, ticker in tickers.items():
                result[symbol] = {
                    'last': ticker.get('last'),
                    'bid': ticker.get('bid'),
                    'ask': ticker.get('ask'),
                    'high': ticker.get('high'),
                    'low': ticker.get('low'),
                    'volume': ticker.get('baseVolume'),
                    'change': ticker.get('percentage'),
                    'timestamp': ticker.get('timestamp')
                }
            
            return result
            
        except Exception as e:
            return {"error": f"获取行情失败：{str(e)}"}
    
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> dict:
        """
        获取 K 线数据
        
        Args:
            symbol: 交易对
            timeframe: K 线周期
            limit: 返回数量
            
        Returns:
            K 线数据
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            # 格式化为易读格式
            candles = []
            for candle in ohlcv:
                candles.append({
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
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
        """
        获取最近的成交记录
        
        Args:
            symbol: 交易对
            limit: 返回数量
            
        Returns:
            成交记录列表
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            trades = self.exchange.fetch_trades(symbol, limit=limit)
            
            result = []
            for trade in trades:
                result.append({
                    'id': trade.get('id'),
                    'timestamp': trade.get('timestamp'),
                    'datetime': trade.get('datetime'),
                    'symbol': trade.get('symbol'),
                    'side': trade.get('side'),
                    'price': trade.get('price'),
                    'amount': trade.get('amount'),
                    'cost': trade.get('cost')
                })
            
            return {
                "symbol": symbol,
                "count": len(result),
                "trades": result
            }
            
        except Exception as e:
            return {"error": f"获取成交记录失败：{str(e)}"}
    
    def get_margin_modes(self, symbol: str) -> dict:
        """
        获取交易对支持的保证金模式
        
        Args:
            symbol: 交易对
            
        Returns:
            保证金模式信息
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            market = self.exchange.market(symbol)
            
            return {
                "symbol": symbol,
                "margin": market.get('margin', False),
                "marginModes": market.get('marginModes', {}),
                "spot": market.get('spot', False),
                "future": market.get('future', False),
                "swap": market.get('swap', False)
            }
            
        except Exception as e:
            return {"error": f"获取保证金模式失败：{str(e)}"}
    
    def get_cross_borrow_rate(self, code: Optional[str] = None) -> dict:
        """
        获取全仓借贷利率
        
        Args:
            code: 可选，指定币种
            
        Returns:
            借贷利率信息
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            if code:
                rate = self.exchange.fetch_cross_borrow_rate(code)
                return {
                    "code": rate.get('currency'),
                    "rate": rate.get('rate'),
                    "period": rate.get('period'),
                    "timestamp": rate.get('timestamp')
                }
            else:
                rates = self.exchange.fetch_cross_borrow_rates()
                result = []
                for rate in rates:
                    result.append({
                        "code": rate.get('currency'),
                        "rate": rate.get('rate'),
                        "period": rate.get('period'),
                        "timestamp": rate.get('timestamp')
                    })
                return {"rates": result, "count": len(result)}
            
        except Exception as e:
            return {"error": f"获取全仓借贷利率失败：{str(e)}"}
    
    def get_isolated_borrow_rate(self, symbol: Optional[str] = None) -> dict:
        """
        获取逐仓借贷利率
        
        Args:
            symbol: 可选，指定交易对
            
        Returns:
            借贷利率信息
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            if symbol:
                rate = self.exchange.fetch_isolated_borrow_rate(symbol)
                return {
                    "symbol": rate.get('symbol'),
                    "baseRate": rate.get('baseRate'),
                    "quoteRate": rate.get('quoteRate'),
                    "period": rate.get('period'),
                    "timestamp": rate.get('timestamp')
                }
            else:
                rates = self.exchange.fetch_isolated_borrow_rates()
                result = []
                for rate in rates:
                    result.append({
                        "symbol": rate.get('symbol'),
                        "baseRate": rate.get('baseRate'),
                        "quoteRate": rate.get('quoteRate'),
                        "period": rate.get('period'),
                        "timestamp": rate.get('timestamp')
                    })
                return {"rates": result, "count": len(result)}
            
        except Exception as e:
            return {"error": f"获取逐仓借贷利率失败：{str(e)}"}
    
    def get_margin_balance(self) -> dict:
        """
        获取保证金账户余额
        
        Returns:
            保证金账户余额信息
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            balance = self.exchange.fetch_balance({'type': 'margin'})
            
            available = {}
            total = {}
            borrowed = {}
            
            for currency, amount in balance.get('free', {}).items():
                if amount > 0:
                    available[currency] = amount
            
            for currency, amount in balance.get('total', {}).items():
                if amount > 0:
                    total[currency] = amount
            
            for currency, amount in balance.get('borrowed', {}).items():
                if amount > 0:
                    borrowed[currency] = amount
            
            return {
                "available": available,
                "total": total,
                "borrowed": borrowed,
                "timestamp": balance.get('timestamp')
            }
            
        except Exception as e:
            return {"error": f"获取保证金余额失败：{str(e)}"}
    
    def get_margin_positions(self, symbols: Optional[list] = None) -> dict:
        """
        获取保证金持仓信息
        
        Args:
            symbols: 可选，指定交易对列表
            
        Returns:
            保证金持仓信息
        """
        if not self._configured:
            return {"error": "交易所未配置或未连接"}
        
        try:
            if symbols is None:
                symbols = []
                for market in self.exchange.markets.values():
                    if market.get('margin', False):
                        symbols.append(market['symbol'])
            
            if not symbols:
                return {"positions": [], "count": 0, "message": "没有找到支持保证金的交易对"}
            
            positions = self.exchange.fetch_positions(symbols, {'type': 'margin'})
            
            result = []
            for pos in positions:
                if pos.get('baseSize', 0) != 0 or pos.get('quoteSize', 0) != 0:
                    result.append({
                        'symbol': pos.get('symbol'),
                        'baseSize': pos.get('baseSize'),
                        'quoteSize': pos.get('quoteSize'),
                        'baseBorrowed': pos.get('baseBorrowed'),
                        'quoteBorrowed': pos.get('quoteBorrowed'),
                        'liquidationPrice': pos.get('liquidationPrice'),
                        'marginMode': pos.get('marginMode')
                    })
            
            return {
                "positions": result,
                "count": len(result)
            }
            
        except Exception as e:
            return {"error": f"获取保证金持仓失败：{str(e)}"}


# 全局服务实例
_ccxt_service: Optional[CCXTService] = None


def get_ccxt_service(exchange_id: str = "binance") -> CCXTService:
    """获取 CCXT 服务单例"""
    global _ccxt_service
    if _ccxt_service is None or _ccxt_service.exchange_id != exchange_id:
        _ccxt_service = CCXTService(exchange_id)
    return _ccxt_service
