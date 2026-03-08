"""Trade MCP Server - 主服务器模块"""

import asyncio
import json
import logging
import sys
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config.settings import get_settings
from .services.finnhub_service import get_finnhub_service
from .services.ccxt_service import get_ccxt_service
from .services.technical_analysis_service import get_technical_analysis_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trade-mcp-server')


class TradeMCPServer:
    """Trade MCP 服务器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.finnhub = get_finnhub_service()
        self.ccxt = get_ccxt_service()
        self.technical_analysis = get_technical_analysis_service()
        
        self.server = Server("trade-mcp")
        
        self._register_tools()
        
        self._register_tool_handlers()
    
    def _register_tools(self):
        """注册 MCP 工具"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="news",
                    description="获取指定投资标的的新闻信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "股票代码或加密货币符号（如 AAPL, BTCUSD）"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回新闻数量限制",
                                "default": 10
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="market_news",
                    description="获取市场新闻（按类别获取最新市场新闻，支持：general=综合新闻, forex=外汇新闻, crypto=加密货币新闻, merger=并购新闻）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "新闻类别：general（综合）、forex（外汇）、crypto（加密货币）、merger（并购）",
                                "enum": ["general", "forex", "crypto", "merger"],
                                "default": "general"
                            },
                            "min_id": {
                                "type": "integer",
                                "description": "获取此ID之后的新闻，默认为0获取最新新闻",
                                "default": 0
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="technical_analysis",
                    description="计算技术指标数据（使用 TA-Lib，支持 RSI, MACD, MA, BB, ATR 等）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT, ETH/USDT）"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "K 线周期 (1m, 5m, 15m, 1h, 4h, 1d, 1w)",
                                "default": "1d"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "K 线数量",
                                "default": 100
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="place_order",
                    description="在 Binance 下单交易（支持现货和保证金交易）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对（如 BTC/USDT）"
                            },
                            "order_type": {
                                "type": "string",
                                "description": "订单类型",
                                "enum": ["market", "limit"]
                            },
                            "side": {
                                "type": "string",
                                "description": "买卖方向",
                                "enum": ["buy", "sell"]
                            },
                            "amount": {
                                "type": "number",
                                "description": "交易数量"
                            },
                            "price": {
                                "type": "number",
                                "description": "价格（限价订单必需）"
                            },
                            "margin_mode": {
                                "type": "string",
                                "description": "保证金模式（可选）：cross=全仓，isolated=逐仓。不指定则为现货交易",
                                "enum": ["cross", "isolated"]
                            }
                        },
                        "required": ["symbol", "order_type", "side", "amount"]
                    }
                ),
                Tool(
                    name="cancel_order",
                    description="取消 Binance 订单",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "订单 ID"
                            },
                            "symbol": {
                                "type": "string",
                                "description": "交易对"
                            }
                        },
                        "required": ["order_id", "symbol"]
                    }
                ),
                Tool(
                    name="get_balance",
                    description="查询 Binance 账户余额",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_positions",
                    description="查询 Binance 持仓信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "可选，指定交易对"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_orderbook",
                    description="获取 Binance 订单簿数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "深度限制",
                                "default": 20
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="get_tickers",
                    description="获取 Binance 行情数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "可选，指定交易对列表"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_margin_modes",
                    description="获取交易对支持的保证金模式",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对（如 BTC/USDT）"
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="get_cross_borrow_rate",
                    description="获取全仓借贷利率",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "可选，指定币种（如 USDT, BTC）。不指定则返回所有币种"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_isolated_borrow_rate",
                    description="获取逐仓借贷利率",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "可选，指定交易对（如 BTC/USDT）。不指定则返回所有交易对"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_margin_balance",
                    description="获取保证金账户余额",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_margin_positions",
                    description="获取保证金持仓信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "可选，指定交易对列表。不指定则查询所有支持保证金的交易对"
                            }
                        },
                        "required": []
                    }
                )
            ]
    
    def _register_tool_handlers(self):
        """注册工具处理器"""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            try:
                result = await self._handle_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            except Exception as e:
                logger.error(f"工具执行失败：{e}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))]
    
    async def _handle_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        """处理工具调用"""
        
        if name == "news":
            symbol = arguments.get("symbol")
            limit = arguments.get("limit", 10)
            return self.finnhub.get_news(symbol, limit)
        
        elif name == "market_news":
            category = arguments.get("category", "general")
            min_id = arguments.get("min_id", 0)
            return self.finnhub.get_market_news(category, min_id)
        
        elif name == "technical_analysis":
            symbol = arguments.get("symbol")
            timeframe = arguments.get("timeframe", "1d")
            limit = arguments.get("limit", 100)
            return self.technical_analysis.calculate_indicators(symbol, timeframe, limit)
        
        elif name == "place_order":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            order_type = arguments.get("order_type", "market")
            side = arguments.get("side")
            amount = arguments.get("amount")
            price = arguments.get("price")
            margin_mode = arguments.get("margin_mode")
            
            params = {}
            if margin_mode:
                params['marginMode'] = margin_mode
            
            return self.ccxt.place_order(symbol, order_type, side, amount, price, params)
        
        elif name == "cancel_order":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            order_id = arguments.get("order_id")
            symbol = arguments.get("symbol")
            return self.ccxt.cancel_order(order_id, symbol)
        
        elif name == "get_balance":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            return self.ccxt.get_balance()
        
        elif name == "get_positions":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            return self.ccxt.get_positions(symbol)
        
        elif name == "get_orderbook":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            limit = arguments.get("limit", 20)
            return self.ccxt.get_orderbook(symbol, limit)
        
        elif name == "get_tickers":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbols = arguments.get("symbols")
            return self.ccxt.get_tickers(symbols)
        
        elif name == "get_margin_modes":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            return self.ccxt.get_margin_modes(symbol)
        
        elif name == "get_cross_borrow_rate":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            code = arguments.get("code")
            return self.ccxt.get_cross_borrow_rate(code)
        
        elif name == "get_isolated_borrow_rate":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            return self.ccxt.get_isolated_borrow_rate(symbol)
        
        elif name == "get_margin_balance":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            return self.ccxt.get_margin_balance()
        
        elif name == "get_margin_positions":
            if not self.ccxt.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbols = arguments.get("symbols")
            return self.ccxt.get_margin_positions(symbols)
        
        else:
            return {"error": f"未知工具：{name}"}
    
    async def run(self):
        """运行 MCP 服务器"""
        logger.info("启动 Trade MCP Server...")
        logger.info(f"Finnhub 配置状态：{'已配置' if self.finnhub.is_configured() else '未配置'}")
        logger.info(f"Binance 配置状态：{'已配置' if self.ccxt.is_configured() else '未配置'}")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """主函数"""
    server = TradeMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
