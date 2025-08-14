# 🔧 Claude Code MCP配置指南

本指南帮助你配置Claude Code来调用Binance MCP工具。

## 📋 前提条件

1. **已安装Binance MCP**：
   ```bash
   pip install git+https://github.com/shanrichard/binance-mcp.git
   ```

2. **已配置API密钥**：
   ```bash
   binance-mcp config
   ```

3. **服务器正在运行**：
   ```bash
   binance-mcp start -d  # 后台运行
   ```

## 🎯 方法1：通过Claude Code的MCP设置

### 步骤1：找到Claude Code配置文件

Claude Code的MCP配置通常在以下位置：

**macOS**:
```bash
~/.config/claude-code/mcp.json
```

**Windows**:
```bash
%APPDATA%\claude-code\mcp.json
```

**Linux**:
```bash
~/.config/claude-code/mcp.json
```

### 步骤2：编辑配置文件

在`mcp.json`中添加Binance MCP服务器配置：

```json
{
  "servers": {
    "binance-mcp": {
      "command": "python",
      "args": ["-m", "binance_mcp.cli", "start"],
      "env": {},
      "description": "Binance cryptocurrency trading MCP server"
    }
  }
}
```

### 步骤3：重启Claude Code

保存配置文件后，重启Claude Code让配置生效。

## 🎯 方法2：通过环境变量

你也可以通过环境变量配置：

```bash
export MCP_SERVER_BINANCE_COMMAND="python -m binance_mcp.cli start"
export MCP_SERVER_BINANCE_ARGS=""
```

## 🎯 方法3：直接启动模式（推荐）

最简单的方法是让Claude Code直接连接到运行中的MCP服务器：

### 步骤1：启动Binance MCP服务器
```bash
binance-mcp start
```

### 步骤2：在Claude Code中测试

服务器启动后，在Claude Code中直接说：

> "帮我查看BTC的当前价格"

如果配置正确，Claude Code会自动发现并使用MCP工具。

## 🔍 验证配置

### 检查MCP工具是否可用

在Claude Code中输入以下测试命令：

1. **查看服务器状态**：
   > "调用get_server_info工具"

2. **查看价格**：
   > "获取BTC/USDT的价格"

3. **查看余额**：
   > "查看我的账户余额"（需要先配置account_id）

### 预期响应

如果配置正确，Claude Code会：
1. 识别到MCP工具可用
2. 调用相应的工具函数
3. 返回Binance API的实际数据

## ⚠️ 常见问题

### Q1: Claude Code找不到MCP工具？

**解决方案**：
1. 确认Binance MCP服务器正在运行：`binance-mcp status`
2. 检查配置文件路径和格式是否正确
3. 重启Claude Code
4. 查看Claude Code的错误日志

### Q2: 工具调用失败？

**可能原因**：
1. **API密钥问题**：检查`binance-mcp test <account_id>`
2. **网络问题**：检查网络连接
3. **参数错误**：确保传递了正确的account_id

### Q3: 如何调试MCP连接？

**调试步骤**：
1. 前台启动服务器查看日志：`binance-mcp start`
2. 检查Claude Code的开发者控制台
3. 使用`get_server_info`工具检查状态

## 📝 配置示例

### 完整的mcp.json示例

```json
{
  "servers": {
    "binance-mcp": {
      "command": "python",
      "args": ["-m", "binance_mcp.cli", "start"],
      "env": {
        "PYTHONPATH": "/path/to/your/python/site-packages"
      },
      "description": "Binance cryptocurrency trading MCP server",
      "disabled": false
    }
  },
  "logging": {
    "level": "info",
    "file": "~/.logs/claude-code-mcp.log"
  }
}
```

### 多环境配置

如果你有多个环境（沙盒/生产），可以配置多个服务器：

```json
{
  "servers": {
    "binance-mcp-sandbox": {
      "command": "python",
      "args": ["-m", "binance_mcp.cli", "start", "--port", "9001"],
      "description": "Binance sandbox environment"
    },
    "binance-mcp-production": {
      "command": "python", 
      "args": ["-m", "binance_mcp.cli", "start", "--port", "9002"],
      "description": "Binance production environment"
    }
  }
}
```

## 🎉 测试成功的标志

配置成功后，你应该能在Claude Code中：

1. **直接用自然语言**：
   - "帮我买0.001个BTC"
   - "查看我的USDT余额"
   - "取消我的待成交订单"

2. **看到实际的API响应**：
   - 真实的价格数据
   - 账户余额信息
   - 交易执行结果

3. **获得智能建议**：
   - Claude会基于实时数据给出交易建议
   - 自动计算仓位大小
   - 风险提醒

恭喜！现在你可以通过Claude Code进行智能化的加密货币交易了！🚀