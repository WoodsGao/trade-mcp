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
from .services.binance_service import get_binance_service
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
        self.binance = get_binance_service()
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
                    name="comprehensive_analysis",
                    description="综合技术分析报告，包含趋势判断、买卖信号、关键价位、风险管理建议",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT）"
                            },
                            "timeframes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "时间周期列表，默认 ['4h', '1d']"
                            },
                            "analysis_type": {
                                "type": "string",
                                "description": "分析类型",
                                "enum": ["full", "quick", "custom"],
                                "default": "full"
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="trend_strength",
                    description="趋势强度分析（ADX/DMI系统），判断趋势方向和强度",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT）"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "K 线周期",
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
                    name="rolling_vwap",
                    description="Rolling VWAP（滚动成交量加权平均价），用于判断日内趋势方向和支撑阻力",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT）"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "K 线周期",
                                "default": "1d"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "K 线数量",
                                "default": 100
                            },
                            "window": {
                                "type": "integer",
                                "description": "滚动窗口大小",
                                "default": 20
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="multi_timeframe_analysis",
                    description="多周期共振分析，确认趋势一致性",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT）"
                            },
                            "timeframes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "时间周期列表，默认 ['1h', '4h', '1d', '1w']"
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="pattern_recognition",
                    description="K线形态识别，检测蜡烛图形态和图表形态",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT）"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "K 线周期",
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
                    name="support_resistance",
                    description="支撑阻力分析，识别关键价格位、Pivot Points、斐波那契回撤位",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT）"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "K 线周期",
                                "default": "1d"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "K 线数量",
                                "default": 200
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="risk_calculator",
                    description="风险管理计算器，计算止损位、仓位大小、风险回报比",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT）"
                            },
                            "entry_price": {
                                "type": "number",
                                "description": "入场价格"
                            },
                            "account_balance": {
                                "type": "number",
                                "description": "账户余额"
                            },
                            "risk_per_trade": {
                                "type": "number",
                                "description": "每笔交易风险比例（%）",
                                "default": 1.0
                            },
                            "target_type": {
                                "type": "string",
                                "description": "止损目标类型",
                                "enum": ["atr", "support"],
                                "default": "atr"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "K 线周期",
                                "default": "1d"
                            }
                        },
                        "required": ["symbol", "entry_price", "account_balance"]
                    }
                ),
                Tool(
                    name="divergence_detector",
                    description="背离检测，检测价格与指标之间的背离信号",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "交易对符号（如 BTC/USDT）"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "K 线周期",
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
        
        elif name == "comprehensive_analysis":
            symbol = arguments.get("symbol")
            timeframes = arguments.get("timeframes")
            analysis_type = arguments.get("analysis_type", "full")
            return self.technical_analysis.comprehensive_analysis(symbol, timeframes, analysis_type)
        
        elif name == "rolling_vwap":
            symbol = arguments.get("symbol")
            timeframe = arguments.get("timeframe", "1d")
            limit = arguments.get("limit", 100)
            window = arguments.get("window", 20)
            return self.technical_analysis.rolling_vwap(symbol, timeframe, limit, window)
        
        elif name == "trend_strength":
            symbol = arguments.get("symbol")
            timeframe = arguments.get("timeframe", "1d")
            limit = arguments.get("limit", 100)
            return self.technical_analysis.trend_strength(symbol, timeframe, limit)
        
        elif name == "multi_timeframe_analysis":
            symbol = arguments.get("symbol")
            timeframes = arguments.get("timeframes")
            return self.technical_analysis.multi_timeframe_analysis(symbol, timeframes)
        
        elif name == "pattern_recognition":
            symbol = arguments.get("symbol")
            timeframe = arguments.get("timeframe", "1d")
            limit = arguments.get("limit", 100)
            return self.technical_analysis.pattern_recognition(symbol, timeframe, limit)
        
        elif name == "support_resistance":
            symbol = arguments.get("symbol")
            timeframe = arguments.get("timeframe", "1d")
            limit = arguments.get("limit", 200)
            return self.technical_analysis.support_resistance(symbol, timeframe, limit)
        
        elif name == "risk_calculator":
            symbol = arguments.get("symbol")
            entry_price = arguments.get("entry_price")
            account_balance = arguments.get("account_balance")
            risk_per_trade = arguments.get("risk_per_trade", 1.0)
            target_type = arguments.get("target_type", "atr")
            timeframe = arguments.get("timeframe", "1d")
            return self.technical_analysis.risk_calculator(
                symbol, entry_price, account_balance, risk_per_trade, target_type, timeframe
            )
        
        elif name == "divergence_detector":
            symbol = arguments.get("symbol")
            timeframe = arguments.get("timeframe", "1d")
            limit = arguments.get("limit", 100)
            return self.technical_analysis.divergence_detector(symbol, timeframe, limit)
        
        elif name == "place_order":
            if not self.binance.is_configured():
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
            
            return self.binance.place_order(symbol, order_type, side, amount, price, params)
        
        elif name == "cancel_order":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            order_id = arguments.get("order_id")
            symbol = arguments.get("symbol")
            return self.binance.cancel_order(order_id, symbol)
        
        elif name == "get_balance":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            return self.binance.get_balance()
        
        elif name == "get_positions":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            return self.binance.get_positions(symbol)
        
        elif name == "get_orderbook":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            limit = arguments.get("limit", 20)
            return self.binance.get_orderbook(symbol, limit)
        
        elif name == "get_tickers":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbols = arguments.get("symbols")
            return self.binance.get_tickers(symbols)
        
        elif name == "get_margin_modes":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            return self.binance.get_margin_modes(symbol)
        
        elif name == "get_cross_borrow_rate":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            code = arguments.get("code")
            return self.binance.get_cross_borrow_rate(code)
        
        elif name == "get_isolated_borrow_rate":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbol = arguments.get("symbol")
            return self.binance.get_isolated_borrow_rate(symbol)
        
        elif name == "get_margin_balance":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            return self.binance.get_margin_balance()
        
        elif name == "get_margin_positions":
            if not self.binance.is_configured():
                return {"error": "Binance 未配置，请设置 API 密钥"}
            
            symbols = arguments.get("symbols")
            return self.binance.get_margin_positions(symbols)
        
        else:
            return {"error": f"未知工具：{name}"}
    
    async def run(self):
        """运行 MCP 服务器"""
        logger.info("启动 Trade MCP Server...")
        logger.info(f"Finnhub 配置状态：{'已配置' if self.finnhub.is_configured() else '未配置'}")
        logger.info(f"Binance 配置状态：{'已配置' if self.binance.is_configured() else '未配置'}")
        
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
