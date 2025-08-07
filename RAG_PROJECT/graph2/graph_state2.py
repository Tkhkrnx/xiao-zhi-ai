from typing import TypedDict, List

from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    表示图处理流程的状态信息

    属性说明：
        question: 用户提出的问题文本
        generation: 语言模型生成的回答文本
        transform_count: 传换查询的次数
        documents: 检索到的相关文档列表
        chat_history: 存储历史记录
    """

    question: str  # 存储当前处理的用户问题
    transform_count: int  # 传换查询的次数
    generate_retry_count: int # 生成回答的重试次数
    web_search_count: int  # 搜索尝试次数
    generation: str  # 存储LLM生成的回答内容
    documents: List[Document]  # 存储检索到的文档内容列表
    chat_history: List[str]  # 存储历史记录