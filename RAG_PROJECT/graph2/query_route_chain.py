from typing import Literal, List, Dict, Any
from pydantic import BaseModel, Field
from utils.log_utils import log
from langchain_core.prompts import ChatPromptTemplate
from llm_models.all_llm import llm
from graph2.retriever_node import retrieve  # 向量召回
from graph2.web_search_node import web_search

# —— 1. 定义路由输出模型，引入置信度和推荐数据源 ——
class RouteQuery(BaseModel):
    datasource: Literal["vectorstore", "web_search", "llm_direct"] = Field(
        ...,
        description="路由到 向量知识库 / 网络搜索 / LLM 自答",
    )

# 带函数调用的 LLM Router
structured_llm_router = llm.with_structured_output(RouteQuery)

# —— 2. 扩充 Prompt 模板，加入上下文历史 ——
system = """
你是一个智能查询路由专家，请将用户问题路由到三种数据源之一：
  • vectorstore：本地学术论文向量库，包含以下领域的学术论文PDF文档：
   - 机器学习（Machine Learning）
   - 深度学习（Deep Learning）
   - 神经网络（Neural Network）
   - 人工智能（Artificial Intelligence）
   - 自然语言处理（NLP）
   - 计算机视觉（Computer Vision）
   - Transformer架构相关技术
   - BERT、GPT、LLaMA、Mistral等大语言模型
   - 检索增强生成（RAG）
   - 强化学习（Reinforcement Learning）
   - 图神经网络（Graph Neural Network）  
  • web_search：网络搜索，适合实时/新闻/天气/股市/汇率等动态信息  
  • llm_direct：当上述两者都不合适、且属于一般性咨询或闲聊时，让 LLM 自行回答  

决策规则：
  1. 如果问题中出现“今天”、“现在”、“实时”、“新闻”、“天气”、“股市”、“汇率”等词，应路由到 web_search。  
  2. 如果问题询问技术细节、算法原理、模型架构、学术研究（如深度学习、注意力机制、Transformer、RAG、强化学习、图神经网络等），应路由到 vectorstore。  
  3. 其它情况（例如日常问答、闲聊、常识性问题等），应路由到 llm_direct。  

请结合最近 3 条对话历史 `{history}`（如果没有可写“无”）和当前问题 `{question}`，输出 `datasource` 

重要说明：
- 必须使用 "datasource" 作为字段名
- 值只能是 "vectorstore", "web_search", "llm_direct"三者之一
- 必须返回严格的JSON格式
- 不要包含任何解释或其他文本
"""
route_prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "历史对话：\n{history}\n\n当前问题：\n{question}")
])

question_router_chain = route_prompt | structured_llm_router


# 测试路由器
# print(  # 测试非技术问题（应路由到网络搜索）
#     question_router_chain.invoke(
#         {"question": "什么是EUV光刻技术?"}
#     )
# )
# print(  # 测试技术问题（应路由到向量数据库）
#     question_router_chain.invoke({"question": "今天，长沙的天气怎么样?"})
# )