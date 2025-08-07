from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from llm_models.all_llm import web_search_tool, llm
from utils.log_utils import log


def web_search(state):
    """
    基于优化后的问题进行网络搜索

    Args:
        state (dict): 当前图状态，包含优化后的问题

    Returns:
        state (dict): 更新后的状态，documents字段替换为网络搜索结果
    """
    log.info("---WEB SEARCH---")  # 阶段标识
    question = state["question"]  # 获取优化后的问题
    web_search_count = state.get("web_search_count", 0)
    chat_history = state.get("chat_history", [])  # 获取对话历史

    # 格式化对话历史
    formatted_history = "\n".join([f"{msg['type']}: {msg['content']}" for msg in chat_history])

    # 使用LLM优化搜索查询，考虑对话历史
    search_prompt = PromptTemplate(
        template="""你是一个专业的搜索查询优化助手。请根据当前问题和对话历史优化搜索查询，
        使得搜索查询更加完整和准确，以便获取更好的搜索结果。

        对话历史：
        {chat_history}

        当前问题：{question}

        请直接输出优化后的搜索查询，不要包含任何其他内容：
        """,
        input_variables=["question", "chat_history"],
    )

    # 创建优化查询链
    search_query_chain = (
            search_prompt |
            llm |
            StrOutputParser()
    )

    # 生成优化后的搜索查询
    optimized_query = search_query_chain.invoke({
        "question": question,
        "chat_history": formatted_history if formatted_history else "无对话历史"
    })

    log.info(f"原始查询: {question}")
    log.info(f"优化后查询: {optimized_query}")

    # 执行网络搜索
    docs = web_search_tool.invoke({"query": optimized_query})  # 调用网络搜索工具
    web_results = "\n".join([d["content"] for d in docs])  # 合并搜索结果
    web_results = Document(page_content=web_results)  # 转换为文档格式

    # 更新对话历史，添加网络搜索结果
    updated_history = chat_history + [
        {"type": "human", "content": question},
        {"type": "ai", "content": f"通过网络搜索获取到以下信息:\n{web_results.page_content}"}
    ]

    return {"documents": web_results, "question": question, "web_search_count": web_search_count + 1,
            "chat_history": updated_history}  # 返回更新状态
