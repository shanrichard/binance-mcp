# 🚀 Binance MCP Server

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

基于ccxt库为Binance交易所开发的MCP（Model Context Protocol）服务，让AI agents（如Claude Code）能够安全、高效地进行数字货币交易操作。专为非技术用户设计的一站式交易解决方案。

## ✨ 功能特性

### 🎯 专为非技术用户设计
- **零编程经验要求** - 通过简单的CLI命令即可完成所有配置
- **AI助手友好** - 完美兼容Claude Code等AI编程助手
- **一键安装部署** - 单条命令完成安装和配置

### 🔧 技术特性
- **内置配置优化** - 自动优化交易参数和连接配置
- **高效执行** - 基于ccxt库的稳定交易执行
- **零额外成本** - 不增加任何交易费用

### 🛡️ 企业级安全
- **本地加密存储** - API密钥使用Fernet对称加密
- **多账户隔离** - 支持现货、期货、沙盒环境分离管理
- **无网络传输** - 密钥仅在本地存储，绝不上传
- **权限最小化** - 仅申请必要的API权限

### 📊 完整交易支持
- **现货交易** - 市价单、限价单、止损单等
- **期货合约** - USD-M、币本位期货，支持杠杆调整
- **期权交易** - Call/Put期权买卖
- **账户管理** - 余额查询、持仓管理、交易历史

### 🔧 丰富的MCP工具
- `create_spot_order` - 创建现货订单
- `cancel_order` - 取消订单
- `get_balance` - 查询余额
- `get_positions` - 查询持仓
- `get_ticker` - 获取实时价格
- `get_open_orders` - 查询开放订单
- `get_server_info` - 服务器状态信息

## 🚀 快速开始

### 1. 安装

```bash
pip install git+https://github.com/shanrichard/binance-mcp.git
```

### 2. 配置账户

```bash
# 交互式配置API密钥
binance-mcp config

# 查看已配置的账户
binance-mcp list
```

### 3. 启动服务

```bash
# 前台运行（显示日志）
binance-mcp start

# 后台运行（推荐）
binance-mcp start -d

# 自定义端口
binance-mcp start --port 9002
```

### 4. 在Claude Code中使用

启动服务后，在Claude Code中直接说：

> "帮我查看BTC的当前价格"
> 
> "用我的现货账户买入0.001个BTC"
> 
> "查看我的账户余额"

Claude Code会自动调用相应的MCP工具完成操作！

## 📋 详细使用指南

### 配置API密钥

1. **获取API密钥**：
   - 登录[Binance](https://www.binance.com/)
   - 前往 **API管理** 页面
   - 创建新的API密钥
   - **权限设置**：勾选"现货与杠杆交易"和"期货交易"
   - **重要**：启用IP白名单限制

2. **配置密钥**：
   ```bash
   binance-mcp config
   ```
   按提示输入：
   - 账户ID（自定义名称）
   - API Key
   - Secret Key
   - 是否为沙盒环境
   - 账户描述

### 服务管理命令

```bash
# 查看帮助
binance-mcp --help

# 查看服务状态
binance-mcp status

# 停止服务
binance-mcp stop

# 测试连接
binance-mcp test <account_id>

# 备份配置
binance-mcp backup
```

### 高级配置

**多账户管理**：
```bash
# 添加现货账户
binance-mcp config --account-id spot_main

# 添加期货账户  
binance-mcp config --account-id futures_main

# 添加沙盒测试账户
binance-mcp config --account-id sandbox_test --sandbox
```

**自定义服务器设置**：
```bash
# 监听所有网卡
binance-mcp start --host 0.0.0.0

# 使用自定义端口
binance-mcp start --port 8888
```

## 🔧 故障排除

### 常见问题

**Q: 出现"Functions with **kwargs are not supported as tools"错误？**

A: 这是旧版本的问题，请更新：
```bash
pip uninstall binance-mcp -y && pip install git+https://github.com/shanrichard/binance-mcp.git
```

**Q: API密钥认证失败？**

A: 检查以下几点：
1. API密钥是否正确复制（注意空格）
2. 是否启用了必要的权限（现货/期货交易）
3. 是否设置了IP白名单限制
4. 沙盒/生产环境是否匹配

**Q: 服务无法启动？**

A: 检查端口是否被占用：
```bash
# 查看端口占用
lsof -i :9001

# 使用其他端口
binance-mcp start --port 9002
```

**Q: Claude Code找不到MCP工具？**

A: 确保：
1. 服务正在运行：`binance-mcp status`
2. 重启Claude Code
3. 检查MCP配置文件

### 日志查看

```bash
# 前台运行查看实时日志
binance-mcp start

# 后台运行的日志位置
~/.config/binance-mcp/logs/
```

## 🔄 更新指南

### 检查更新

```bash
# 查看当前版本
binance-mcp --version

# 查看最新版本
curl -s https://api.github.com/repos/shanrichard/binance-mcp/releases/latest | grep '"tag_name"'
```

### 更新到最新版本

**方法1：重新安装（推荐）**
```bash
pip uninstall binance-mcp -y && pip install git+https://github.com/shanrichard/binance-mcp.git
```

**方法2：强制重装**
```bash
pip install --force-reinstall git+https://github.com/shanrichard/binance-mcp.git
```

**方法3：指定版本**
```bash
pip install git+https://github.com/shanrichard/binance-mcp.git@v1.0.1
```

### 更新说明

- ✅ **配置保持不变** - 更新不会影响已配置的账户
- ✅ **向后兼容** - 新版本兼容旧配置
- ✅ **热更新支持** - 无需重新配置API密钥

## 🏗️ 开发者指南

### 本地开发

```bash
# 克隆代码
git clone https://github.com/shanrichard/binance-mcp.git
cd binance-mcp

# 安装开发依赖
pip install -e .[dev]

# 运行测试
pytest

# 运行集成测试
python integration_test.py
```

### 测试覆盖

```bash
# 单元测试
pytest tests/unit/ -v

# 测试覆盖率
pytest --cov=binance_mcp --cov-report=html
```

### 代码结构

```
binance_mcp/
├── __init__.py          # 包初始化
├── config.py           # 配置管理（加密存储）
├── broker.py           # Broker ID注入工厂
├── tools.py            # MCP工具实现
├── server.py           # FastMCP服务器
├── simple_server.py    # 简化服务器（避免**kwargs问题）
├── cli.py              # 命令行接口
tests/
├── unit/               # 单元测试
├── integration/        # 集成测试
└── conftest.py         # 测试配置
```

## 🤝 贡献指南

### 提交Issue

遇到问题请提交Issue，包含：
- 操作系统版本
- Python版本
- 完整错误信息
- 复现步骤

### 贡献代码

1. Fork项目
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add some amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

## ⚠️ 风险提醒

### 交易风险
- **数字货币交易具有高风险，可能导致资金损失**
- 建议先在沙盒环境充分测试
- 设置合理的止损和仓位管理
- 不要投入超过承受能力的资金

### 技术风险
- 确保API密钥安全，不要分享给他人
- 定期备份配置文件
- 在受信任的网络环境中使用
- 保持软件更新到最新版本

### 合规提醒
- 遵守当地法律法规
- 了解税务申报义务
- 符合反洗钱要求

## 📞 支持与反馈

- **GitHub Issues**: [提交问题](https://github.com/shanrichard/binance-mcp/issues)
- **讨论区**: [GitHub Discussions](https://github.com/shanrichard/binance-mcp/discussions)
- **文档**: [项目Wiki](https://github.com/shanrichard/binance-mcp/wiki)

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- **ccxt团队** - 提供优秀的交易所API统一库
- **FastMCP团队** - 提供高性能的MCP服务器框架
- **开源社区** - 感谢每一位贡献代码和反馈的开发者

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个Star！⭐**

[🏠 首页](https://github.com/shanrichard/binance-mcp) • 
[📖 文档](https://github.com/shanrichard/binance-mcp#readme) • 
[🐛 问题反馈](https://github.com/shanrichard/binance-mcp/issues) • 
[💡 功能建议](https://github.com/shanrichard/binance-mcp/discussions)

</div>