from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from llm_models.all_llm import llm
from utils.log_utils import log


def llm_direct(state: dict) -> dict:
    """
    LLM 自答节点：当不走检索或网络搜索时，直接让 LLM 生成回答。

    Args:
        state (dict): 当前图状态，包含用户问题等字段

    Returns:
        dict: 更新后的状态，包含生成的回答 generation 字段和原 question
    """
    log.info("---LLM 自答：直接生成回答---")
    question = state["question"]
    chat_history = state.get("chat_history", [])  # 获取对话历史
    prompt = PromptTemplate(
        template="""你是一个专业的问答助手。请基于你的知识直接回答用户问题。
        
        对话历史：{chat_history}
        
        回答要求：
        1. 基于你已有的知识回答问题
        2. 如果有相关对话历史，请考虑上下文
        3. 回答要准确、简洁、直接
        4. 如果你不确定答案，诚实说明不知道
        5. 不要编造信息或进行推测
        6. 你的回答不能在外面包一个 markdown，因为 pydantic 需要解析纯JSON，但是内容可以有 markdown。
        问题：{question}
    
        回答：""",
        input_variables=["question", "chat_history"],
    )

    # 格式化对话历史
    formatted_history = "\n".join(["{msg['type']}: {msg['content']}" for msg in chat_history])

    llm_chain = (
            prompt |  # 第一步：使用提示模板
            llm |  # 第二步：调用语言模型
            StrOutputParser()  # 第三步：解析模型输出为字符串
    )

    # RAG生成过程
    generation = llm_chain.invoke({"question": question, "chat_history": formatted_history})  # 调用llm链生成回答
    # 更新对话历史
    updated_history = chat_history + [
        HumanMessage(content=question),
        AIMessage(content=generation)
    ]
    return {"question": question, "generation": generation, "chat_history": updated_history}  # 返回更新后的状态
