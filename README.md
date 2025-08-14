# Binance MCP Server

基于ccxt库为Binance交易所开发的MCP（Model Context Protocol）服务，让AI agents能够直接进行数字货币交易操作。

## 功能特性

### 交易功能
- 现货交易（市价单、限价单、止损单等）
- USD-M期货合约（开仓、平仓、调整杠杆）
- 币本位期货合约
- 期权交易（Call/Put期权买卖）

### 账户管理
- 多账户支持（现货、期货、期权账户）
- 账户余额查询
- 持仓信息查询
- 交易历史记录

### 市场数据
- 实时价格数据
- 订单簿深度
- K线图数据
- 交易手续费查询

### 安全特性
- API密钥本地加密存储
- 多账户隔离管理
- 自动broker ID注入
- 错误信息透明传递

## 快速开始

### 安装

```bash
pip install binance-mcp
```

### 配置

```bash
# 配置API密钥和账户
binance-mcp config

# 启动MCP服务
binance-mcp start

# 查看服务状态
binance-mcp status

# 列出配置的账户
binance-mcp list
```

### 使用

服务启动后，Claude Code等支持MCP的AI agent可以自动发现并使用以下工具：

- `create_spot_order` - 创建现货订单
- `create_futures_order` - 创建期货订单
- `get_balance` - 查询账户余额
- `get_positions` - 查询持仓信息
- `get_ticker` - 获取实时价格
- `set_leverage` - 设置杠杆倍数

## 技术架构

```
Claude Agent
    ↓ (MCP协议)
binance-mcp服务
    ↓ (Python API)
ccxt.binance实例
    ↓ (REST API)
Binance交易所API
```

## 开发

### 环境设置

```bash
git clone <repository>
cd binance-mcp
pip install -e .[dev]
```

### 运行测试

```bash
# 单元测试
pytest tests/unit

# 集成测试（需要沙盒API密钥）
pytest tests/integration

# 所有测试
pytest
```

## 许可证

MIT License - 详见 LICENSE 文件。

## 安全提醒

- 仅在受信任的环境中使用
- API密钥会加密存储在本地
- 建议先在沙盒环境测试
- 谨慎进行真实交易操作