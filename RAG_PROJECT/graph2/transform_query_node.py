from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from llm_models.all_llm import llm
from utils.log_utils import log


def transform_query(state):
    """
    优化用户问题，生成更合适的查询语句
    """
    log.info("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]
    transform_count = state.get("transform_count", 0)
    chat_history = state.get("chat_history", [])  # 获取对话历史

    # 提示词模板 - 问题重写优化
    system = """你是一个专业的问题重写专家，负责将用户问题转换为更适合向量数据库检索的优化版本。

    重写原则：
    1. 保持原问题的核心语义和意图
    2. 使用更专业、准确的术语表达
    3. 增加上下文相关的关键词
    4. 将模糊表述转换为具体的技术概念
    5. 保持问题的完整性和清晰度
    6. 考虑对话历史中的上下文信息

    重写要求：
    - 输出必须是一个完整、清晰的问题
    - 不要添加解释或额外信息
    - 不要改变问题的根本意图
    - 使问题更适合在技术文档中检索答案
    - 仅输出有效的纯 JSON，不要包含任何 markdown 或代码块格式
    示例：
    原始问题：GPT怎么工作的？
    优化问题：GPT语言模型的架构原理和工作机制是什么？"""

    re_write_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "对话历史:\n{chat_history}\n\n这是初始问题: \n\n {question} \n 请生成一个优化后的问题。",
            ),
        ]
    )

    # 构建问题重写处理链
    question_rewriter = (
            re_write_prompt  # 使用优化提示模板
            | llm  # 调用语言模型
            | StrOutputParser()  # 将输出解析为字符串
    )

    # 格式化对话历史
    formatted_history = "\n".join(["{msg['type']}: {msg['content']}" for msg in chat_history])
    # 问题重写
    better_question = question_rewriter.invoke({
        "question": question,
        "chat_history": formatted_history
    })

    return {
        "documents": documents,
        "question": better_question,
        "transform_count": transform_count + 1,
        "chat_history": chat_history
    }