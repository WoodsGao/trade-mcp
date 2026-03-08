"""Trade MCP Server - 命令行入口"""

import asyncio
import argparse
import logging
import sys
from typing import Optional

from .server import TradeMCPServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trade-mcp-cli')


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Trade MCP Server - 金融交易 MCP 服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  trade-mcp                    启动 MCP 服务器
  trade-mcp --version          显示版本信息
  trade-mcp --help             显示帮助信息
        """
    )
    
    parser.add_argument(
        '--version', '-v',
        action='store_true',
        help='显示版本信息'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    if args.version:
        from . import __version__
        print(f"trade-mcp version {__version__}")
        return
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")
    
    try:
        server = TradeMCPServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
