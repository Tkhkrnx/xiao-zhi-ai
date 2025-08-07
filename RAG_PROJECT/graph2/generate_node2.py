from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from llm_models.all_llm import llm


def generate(state):
    """
    生成回答
    Args:
        state (dict): 当前图状态，包含问题和检索结果
    Returns:
        state (dict): 更新后的状态，新增包含生成结果的generation字段
    """
    question = state["question"]  # 获取用户问题
    documents = state["documents"]  # 获取检索到的文档
    chat_history = state.get("chat_history", [])  # 获取对话历史
    generate_retry_count = state.get("generate_retry_count", 0)
    prompt = PromptTemplate(
        template="""你是一个专业的问答助手。请基于提供的参考内容和对话历史准确回答问题：

        【回答要求】
        1. 基于参考内容中的具体信息回答问题
        2. 如果参考内容中有相关信息，直接给出详细回答
        3. 如果参考内容信息有限但有一定相关性，基于现有信息进行合理回答
        4. 回答要具体、准确，引用参考内容支持你的观点
        5. 结合对话历史，确保回答连贯一致
    
        【格式要求】
        - 回答应简洁明了，直接针对问题核心
        - 将信息来源融入你的回答中，不要直接引用原文
        - 不要编造或推测未在参考内容中提及的信息
        - 你的回答不要包含任何 markdown 或代码块格式。
    
        对话历史：
        {chat_history}
    
        问题：
        {question}
    
        参考内容：
        {context}
    
        回答：""",
        input_variables=["question", "context", "chat_history"],
    )

    # 后处理函数 - 格式化检索到的文档
    def format_docs(docs):
        """将多个文档内容合并为一个字符串，用两个换行符分隔每个文档"""
        if isinstance(docs, list):
            return "\n\n".join(doc.page_content for doc in docs)  # 拼接所有文档内容
        else:
            return "\n\n" + docs.page_content

    formatted_history = "\n".join(["{msg['type']}: {msg['content']}" for msg in chat_history])
    # 构建RAG处理链
    rag_chain = (
            prompt |  # 第一步：使用提示模板
            llm |  # 第二步：调用语言模型
            StrOutputParser()  # 第三步：解析模型输出为字符串
    )

    # RAG生成过程
    generation = rag_chain.invoke({"context": format_docs(documents), "question": question, "chat_history": formatted_history})
    # 更新对话历史
    updated_history = chat_history + [
        HumanMessage(content=question),
        AIMessage(content=generation)
    ]
    # 调用RAG链生成回答
    return {"documents": documents, "question": question, "generation": generation, "chat_history": updated_history, "generate_retry_count": generate_retry_count + 1}  # 返回更新后的状态