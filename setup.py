"""
Setup script for binance-mcp package
"""

import os
from setuptools import setup, find_packages

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# 读取requirements.txt（如果存在）
def read_requirements():
    requirements = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return requirements

# 包信息
setup(
    name="binance-mcp",
    version="1.0.0",
    author="Binance MCP Team",
    author_email="",
    description="基于ccxt的Binance交易所MCP服务，为AI agents提供数字货币交易功能",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/shanrichard/binance-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        # 核心依赖
        "ccxt>=4.0.0",              # 加密货币交易库
        "fastmcp>=1.0.0",           # MCP协议框架  
        "click>=8.0.0",             # CLI框架
        "cryptography>=3.4.0",      # 加密存储
        
        # 辅助依赖
        "requests>=2.28.0",         # HTTP请求
        "aiohttp>=3.8.0",           # 异步HTTP
        "pydantic>=1.10.0",         # 数据验证
    ],
    extras_require={
        "dev": [
            # 开发依赖
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
            
            # 文档依赖
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0", 
            "pytest-asyncio>=0.21.0",
            "responses>=0.23.0",    # HTTP mock
        ]
    },
    entry_points={
        "console_scripts": [
            "binance-mcp=binance_mcp.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "binance_mcp": [
            "*.json",
            "*.yaml",
            "*.yml",
        ],
    },
    keywords=[
        "binance",
        "cryptocurrency", 
        "trading",
        "mcp",
        "model-context-protocol",
        "ai-agent",
        "ccxt",
        "bitcoin",
        "ethereum",
        "futures",
        "options",
    ],
    project_urls={
        "Documentation": "https://github.com/shanrichard/binance-mcp/docs",
        "Bug Reports": "https://github.com/shanrichard/binance-mcp/issues",
        "Source": "https://github.com/shanrichard/binance-mcp",
        "Changelog": "https://github.com/shanrichard/binance-mcp/blob/main/CHANGELOG.md",
    },
)