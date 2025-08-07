from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from llm_models.all_llm import llm


# 数据模型 - 文档相关性评分
class GradeDocuments(BaseModel):
    """对检索到的文档进行相关性评分的二元判断"""

    binary_score: str = Field(
        description="文档是否与问题相关，取值为'yes'或'no'"
    )


# 带函数调用的LLM初始化
structured_llm_grader = llm.with_structured_output(GradeDocuments)  # 绑定结构化输出到评分模型

# 提示词模板
system = system = """你是一个智能文档相关性评分器。

评分任务：判断检索到的文档是否与用户问题相关。

评分标准：
1. 相关性判断应宽松而非严格
2. 文档只要包含与问题主题相关的任何信息就算相关
3. 不要求文档能完整回答问题，只要有帮助即可
4. 避免过度过滤可能有用的文档

输出要求：
- 仅输出'yes'或'no'
- 'yes'表示文档相关，应保留
- 'no'表示文档无关，应过滤

重要说明：
- 必须使用 "binary_score" 作为字段名
- 值只能是 "yes" 或 "no"
- 必须返回严格的JSON格式，不要包含任何 markdown 或代码块格式。
- 不要包含任何解释或其他文本

示例：
问题：什么是Python装饰器？
文档包含Python语法相关内容 → 'yes'
文档讲述Java编程内容 → 'no'"""

grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),  # 系统角色提示
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),  # 用户输入模板
    ]
)

# 构建检索评分器工作流
retrieval_grader_chain = grade_prompt | structured_llm_grader  # 组合提示模板和LLM评分器
