from langchain_core.tools import create_retriever_tool
from documents.milvus_db import MilvusVectorSave

mv = MilvusVectorSave()
mv.create_connection()
retriever = mv.vector_store_saved.as_retriever(
    search_type='similarity',  # 仅返回相似度超过阈值的文档
    search_kwargs={
        "k": 6,
        "score_threshold": 0.2,
        "ranker_type": "rrf",
        "ranker_params": {"k": 60},
        'filter': {"category": "content"}
    }
)


retriever_tool = create_retriever_tool(
    retriever,
    'rag_retriever',
    '搜索并返回关于机器学习、深度学习、自然语言处理等相关领域的技术文档和学术资料，'
    '内容涵盖: transformer模型、BERT、GPT、LLM、RAG技术、强化学习、计算机视觉等前沿研究、技术实现细节和学术论文。'
    '适用于查询相关技术概念、算法原理、实现方法、研究成果、学术论文、技术对比等各类技术问题。'
)
