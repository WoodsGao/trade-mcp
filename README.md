# Trade MCP Server

基于 CCXT 和 Finnhub 的 MCP（Model Context Protocol）服务器，提供投资标的新闻、技术面数据和 Binance 交易功能。

## 功能特性

- 📰 **新闻获取** - 通过 Finnhub 获取股票和加密货币的实时新闻
- 📊 **技术分析** - 使用 TA-Lib 计算多种技术指标（RSI, MACD, MA, BB, ATR 等）
- 💱 **Binance 交易** - 支持现货交易下单、撤单、查询余额和持仓
- 📈 **市场数据** - 获取订单簿、行情、K 线等市场数据
- 🔌 **MCP 协议** - 标准化的 MCP 接口，易于与 AI 助手集成

## 快速开始

### 1. 创建虚拟环境

#### Windows

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

复制环境变量模板文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 API 密钥：

```env
# Finnhub API Key (获取：https://finnhub.io/dashboard)
FINNHUB_API_KEY=your_finnhub_api_key_here

# Binance API Key (获取：https://www.binance.com/en/my/settings/api-management)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Binance 交易选项
BINANCE_TESTNET=false          # 是否使用 Testnet（需要单独的 API Key）: true/false
BINANCE_FUTURES=false          # 是否使用合约交易：true=合约，false=现货

# MCP 服务器配置
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000

# 日志级别
LOG_LEVEL=INFO
```

### 4. 检查配置

```bash
# 检查配置状态
python -m src.cli --check-config
```

### 5. 启动 MCP 服务器

```bash
# 启动服务器
python -m src.cli
```

## MCP 工具列表

### 数据查询工具

#### 1. `news` - 获取新闻
获取指定标的的新闻信息。

**参数:**
- `symbol` (必需): 股票代码或加密货币符号（如 AAPL, BTCUSD）
- `limit` (可选): 返回新闻数量限制，默认 10

**示例:**
```json
{
  "name": "news",
  "arguments": {
    "symbol": "AAPL",
    "limit": 5
  }
}
```

#### 2. `technical_analysis` - 技术指标
获取技术指标数据（MACD、RSI 等）。

**参数:**
- `symbol` (必需): 股票代码或加密货币符号
- `resolution` (可选): K 线周期 (D=日，W=周，M=月)，默认 D

**示例:**
```json
{
  "name": "technical_analysis",
  "arguments": {
    "symbol": "TSLA",
    "resolution": "D"
  }
}
```

### 交易工具

#### 3. `place_order` - 下单交易
在 Binance 下单交易。

**参数:**
- `symbol` (必需): 交易对（如 BTC/USDT）
- `order_type` (必需): 订单类型 (market, limit)
- `side` (必需): 买卖方向 (buy, sell)
- `amount` (必需): 交易数量
- `price` (可选): 价格（限价订单必需）

**示例:**
```json
{
  "name": "place_order",
  "arguments": {
    "symbol": "BTC/USDT",
    "order_type": "market",
    "side": "buy",
    "amount": 0.001
  }
}
```

#### 4. `cancel_order` - 取消订单
取消 Binance 订单。

**参数:**
- `order_id` (必需): 订单 ID
- `symbol` (必需): 交易对

**示例:**
```json
{
  "name": "cancel_order",
  "arguments": {
    "order_id": "12345678",
    "symbol": "BTC/USDT"
  }
}
```

#### 5. `get_balance` - 查询余额
查询 Binance 账户余额。

**参数:** 无

**示例:**
```json
{
  "name": "get_balance",
  "arguments": {}
}
```

#### 6. `get_positions` - 查询持仓
查询 Binance 持仓信息。

**参数:**
- `symbol` (可选): 指定交易对

**示例:**
```json
{
  "name": "get_positions",
  "arguments": {
    "symbol": "BTC/USDT"
  }
}
```

#### 7. `get_orderbook` - 订单簿
获取 Binance 订单簿数据。

**参数:**
- `symbol` (必需): 交易对
- `limit` (可选): 深度限制，默认 20

**示例:**
```json
{
  "name": "get_orderbook",
  "arguments": {
    "symbol": "BTC/USDT",
    "limit": 20
  }
}
```

#### 8. `get_tickers` - 行情数据
获取 Binance 行情数据。

**参数:**
- `symbols` (可选): 指定交易对列表

**示例:**
```json
{
  "name": "get_tickers",
  "arguments": {
    "symbols": ["BTC/USDT", "ETH/USDT"]
  }
}
```

## 与 AI 助手集成

### Claude Desktop 配置

#### 方法 1：使用虚拟环境（推荐）

**Windows:**
```json
{
  "mcpServers": {
    "trade-mcp": {
      "command": "C:\\Projects\\trade-mcp\\venv\\Scripts\\python.exe",
      "args": ["-m", "src.cli"],
      "cwd": "C:\\Projects\\trade-mcp",
      "env": {
        "FINNHUB_API_KEY": "your_finnhub_api_key",
        "BINANCE_API_KEY": "your_binance_api_key",
        "BINANCE_API_SECRET": "your_binance_api_secret",
        "BINANCE_TESTNET": "true",
        "BINANCE_FUTURES": "false"
      }
    }
  }
}
```

**macOS / Linux:**
```json
{
  "mcpServers": {
    "trade-mcp": {
      "command": "/path/to/trade-mcp/venv/bin/python",
      "args": ["-m", "src.cli"],
      "cwd": "/path/to/trade-mcp",
      "env": {
        "FINNHUB_API_KEY": "your_finnhub_api_key",
        "BINANCE_API_KEY": "your_binance_api_key",
        "BINANCE_API_SECRET": "your_binance_api_secret",
        "BINANCE_TESTNET": "true",
        "BINANCE_FUTURES": "false"
      }
    }
  }
}
```

#### 方法 2：使用系统 Python

如果您已在全局环境安装了依赖：

```json
{
  "mcpServers": {
    "trade-mcp": {
      "command": "python",
      "args": ["-m", "src.cli"],
      "cwd": "C:\\Projects\\trade-mcp",
      "env": {
        "FINNHUB_API_KEY": "your_finnhub_api_key",
        "BINANCE_API_KEY": "your_binance_api_key",
        "BINANCE_API_SECRET": "your_binance_api_secret",
        "BINANCE_TESTNET": "true",
        "BINANCE_FUTURES": "false"
      }
    }
  }
}
```

**配置文件位置:**
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/claude/claude_desktop_config.json`

**提示:** 项目提供了示例配置文件 `claude_desktop_config.example.json`，您可以复制并根据实际情况修改。

### 使用示例

配置完成后，您可以在与 Claude 的对话中直接使用：

- "获取 Apple 的最新新闻"
- "查看 BTC/USDT 的技术指标"
- "查询我的 Binance 余额"
- "以市价买入 0.001 BTC"

## 项目结构

```
trade-mcp/
├── src/
│   ├── __init__.py
│   ├── cli.py              # CLI 入口
│   ├── server.py           # MCP 服务器主程序
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py     # 配置管理
│   └── services/
│       ├── __init__.py
│       ├── finnhub_service.py  # Finnhub 数据服务
│       └── ccxt_service.py     # CCXT 交易服务
├── .env.example            # 环境变量模板
├── .gitignore
├── requirements.txt        # Python 依赖
└── README.md
```

## 获取 API 密钥

### Finnhub API Key
1. 访问 [Finnhub](https://finnhub.io/)
2. 注册免费账户
3. 在 [Dashboard](https://finnhub.io/dashboard) 获取 API Key

### Binance API Key
1. 登录 [Binance](https://www.binance.com/)
2. 进入 [API 管理页面](https://www.binance.com/en/my/settings/api-management)
3. 创建新的 API Key
4. 启用现货交易权限（如果是合约交易，也需要启用期货交易权限）
5. **重要**: 妥善保管 API Secret，只显示一次

### Binance Demo Trading（模拟交易）

Binance 提供 Demo Trading 功能用于开发和测试（CCXT v4.5.6+ 支持）：

**申请 Demo Trading API Key：**
1. 访问 [Binance API 管理](https://www.binance.com/en/my/settings/api-management)
2. 创建新的 API Key
3. 启用现货交易和/或期货交易权限
4. 在 `.env` 文件中设置 `BINANCE_DEMO=true`

**优势**: 
- 支持现货和合约交易
- 使用模拟资金，安全无风险
- 不受地区限制
- 支持所有 API 端点

**注意**: 
- Demo Trading 需要**专用的 API Key**，与正式网络和旧 Testnet 的 API Key 不通用
- 需要在 Binance 官网重新申请 Demo Trading 专用的 API Key

### 现货 vs 合约交易
通过 `BINANCE_FUTURES` 参数控制交易类型：

- **现货交易** (`BINANCE_FUTURES=false`): 
  - 交易实际的加密货币资产
  - 无杠杆或低杠杆
  - 风险相对较低

- **合约交易** (`BINANCE_FUTURES=true`):
  - 交易期货合约
  - 支持高杠杆（最高 125x）
  - 可以做多或做空
  - 风险较高，适合有经验的用户

**注意**: 合约交易需要额外的期货交易权限，请确保您的 API Key 已启用该权限。

### 技术指标计算

本项目使用 **TA-Lib** 库计算多种技术指标，支持以下指标：

**移动平均线:**
- SMA (Simple Moving Average) - 简单移动平均
- EMA (Exponential Moving Average) - 指数移动平均

**动量指标:**
- RSI (Relative Strength Index) - 相对强弱指标
- MACD (Moving Average Convergence Divergence) - 指数平滑异同移动平均线
- MOM (Momentum) - 动量指标
- Stochastic - 随机指标

**波动率指标:**
- BB (Bollinger Bands) - 布林带
- ATR (Average True Range) - 平均真实波幅

**成交量指标:**
- OBV (On Balance Volume) - 能量潮指标

**其他指标:**
- CCI (Commodity Channel Index) - 商品通道指标
- Williams %R - 威廉指标

**使用方法:**
```
# 通过 MCP 工具调用
technical_analysis(symbol="BTC/USDT", timeframe="1d", limit=100)
```

**参数说明:**
- `symbol`: 交易对符号（如 BTC/USDT）
- `timeframe`: K 线周期（1m, 5m, 15m, 1h, 4h, 1d, 1w）
- `limit`: K 线数量（建议 50-500）

## 安全提示

⚠️ **重要安全注意事项:**

- 永远不要将 `.env` 文件提交到版本控制系统
- 定期更换 API 密钥
- 为 API Key 设置适当的权限限制（如 IP 白名单）
- 不要与任何人分享您的 API 密钥

## 故障排除

### 常见问题

**1. 模块导入错误**
```bash
# 确保已激活虚拟环境
# Windows
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

**2. API 未配置错误**
```bash
# 检查 .env 文件是否存在
# 运行配置检查
python -m src.cli --check-config
```

**3. Binance 连接失败**
- 检查 API Key 是否正确
- 确认 API Key 已启用现货交易权限
- 检查网络连接

## 开发

### 添加新功能

1. 在 `src/services/` 目录创建新的服务模块
2. 在 `src/server.py` 中注册新的 MCP 工具
3. 更新本文档

### 测试

```bash
# 安装测试依赖
pip install pytest

# 运行测试
pytest
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 支持

如有问题，请提交 Issue 或联系开发者。
