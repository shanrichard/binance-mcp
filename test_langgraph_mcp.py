#!/usr/bin/env python3
"""
LangGraph + Binance MCP 集成测试脚本

测试MCP Adapter是否正确将Binance MCP工具集成到LangGraph中
"""

import asyncio
import os
import sys
from typing import Annotated, Sequence, TypedDict

try:
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
    from langchain_openai import ChatOpenAI
    from langgraph import StateGraph, END
    # 这里需要找到正确的MCP适配器包
    # from mcp_langchain import MCPToolkit  # 可能的包名
    from langchain_community.adapters.mcp import MCPToolkit  # 或者这个
except ImportError as e:
    print(f"❌ 依赖包导入失败: {e}")
    print("请安装必要的包:")
    print("  pip install langgraph langchain-openai langchain-community")
    print("  pip install mcp-langchain  # 或正确的MCP适配器包名")
    sys.exit(1)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]

async def test_mcp_toolkit():
    """测试MCP Toolkit基本功能"""
    print("🔧 测试MCP Toolkit基本功能...")
    
    try:
        # 尝试连接到MCP服务器
        mcp_toolkit = MCPToolkit(
            server_command="python",
            server_args=["-m", "binance_mcp.simple_server"],
            server_env={}
        )
        
        # 获取工具列表
        tools = mcp_toolkit.get_tools()
        print(f"✅ 成功加载 {len(tools)} 个MCP工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        return tools
        
    except Exception as e:
        print(f"❌ MCP Toolkit连接失败: {e}")
        return None

async def test_direct_tool_call(tools):
    """测试直接工具调用"""
    print("\n🔧 测试直接工具调用...")
    
    try:
        # 找到get_server_info工具
        server_info_tool = None
        for tool in tools:
            if tool.name == "get_server_info":
                server_info_tool = tool
                break
        
        if not server_info_tool:
            print("❌ 未找到get_server_info工具")
            return False
            
        # 调用工具
        result = server_info_tool.invoke({})
        print(f"✅ 服务器信息: {result}")
        
        # 测试get_ticker工具
        ticker_tool = None
        for tool in tools:
            if tool.name == "get_ticker":
                ticker_tool = tool
                break
        
        if ticker_tool:
            print("\n🔧 测试价格查询工具...")
            ticker_result = ticker_tool.invoke({"symbol": "BTC/USDT"})
            print(f"✅ BTC价格: {ticker_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具调用失败: {e}")
        return False

async def test_langgraph_integration(tools):
    """测试LangGraph集成"""
    print("\n🔧 测试LangGraph集成...")
    
    # 检查OpenAI API密钥
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("⚠️  未设置OPENAI_API_KEY，跳过LangGraph测试")
        return False
    
    try:
        # 初始化LLM
        llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0
        )
        
        # 将工具绑定到LLM
        llm_with_tools = llm.bind_tools(tools)
        
        def call_model(state: AgentState):
            """调用LLM处理消息"""
            messages = state["messages"]
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        def call_tools(state: AgentState):
            """调用工具"""
            messages = state["messages"]
            last_message = messages[-1]
            
            tool_outputs = []
            for tool_call in last_message.tool_calls:
                # 查找对应的工具
                tool = next(t for t in tools if t.name == tool_call["name"])
                
                try:
                    result = tool.invoke(tool_call["args"])
                    tool_outputs.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"]
                    ))
                except Exception as e:
                    tool_outputs.append(ToolMessage(
                        content=f"工具调用失败: {e}",
                        tool_call_id=tool_call["id"]
                    ))
            
            return {"messages": tool_outputs}
        
        def should_continue(state: AgentState):
            """判断是否需要继续"""
            messages = state["messages"]
            last_message = messages[-1]
            
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            return END
        
        # 构建工作流图
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", call_tools)
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        workflow.add_edge("tools", "agent")
        
        app = workflow.compile()
        
        # 测试对话
        test_input = {
            "messages": [HumanMessage(content="请获取服务器信息")]
        }
        
        result = await app.ainvoke(test_input)
        final_message = result["messages"][-1]
        print(f"✅ LangGraph响应: {final_message.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ LangGraph集成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始Binance MCP + LangGraph集成测试\n")
    
    # 1. 测试MCP服务器连接
    print("📡 检查Binance MCP服务器状态...")
    import subprocess
    try:
        result = subprocess.run(
            ["binance-mcp", "status"], 
            capture_output=True, 
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ MCP服务器运行中")
        else:
            print(f"⚠️  MCP服务器状态异常: {result.stderr}")
            print("请运行: binance-mcp start -d")
    except subprocess.TimeoutExpired:
        print("⚠️  MCP服务器状态检查超时")
    except FileNotFoundError:
        print("❌ binance-mcp命令未找到，请确认已安装")
        return
    
    # 2. 测试MCP Toolkit
    tools = await test_mcp_toolkit()
    if not tools:
        print("\n❌ MCP Toolkit测试失败，无法继续")
        return
    
    # 3. 测试直接工具调用
    tool_success = await test_direct_tool_call(tools)
    if not tool_success:
        print("\n❌ 工具调用测试失败")
        return
    
    # 4. 测试LangGraph集成
    langgraph_success = await test_langgraph_integration(tools)
    
    # 总结
    print("\n" + "="*50)
    print("🎯 测试结果总结:")
    print(f"  - MCP连接: {'✅' if tools else '❌'}")
    print(f"  - 工具调用: {'✅' if tool_success else '❌'}")
    print(f"  - LangGraph集成: {'✅' if langgraph_success else '❌'}")
    
    if tools and tool_success and langgraph_success:
        print("\n🎉 所有测试通过！LangGraph + Binance MCP 集成成功！")
    else:
        print(f"\n⚠️  部分测试失败，请检查相关配置")

if __name__ == "__main__":
    asyncio.run(main())