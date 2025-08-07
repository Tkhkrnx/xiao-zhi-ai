from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

from llm_models.all_llm import llm


# 数据模型 - 生成内容幻觉评分
class GradeHallucinations(BaseModel):
    """对生成回答中是否存在幻觉进行二元评分"""

    binary_score: str = Field(
        description="回答是否基于事实，取值为'yes'或'no'"
    )


# 带函数调用的LLM初始化
structured_llm_grader = llm.with_structured_output(GradeHallucinations)  # 绑定结构化输出到评分模型

# 提示词模板
system = """你是一个专业的幻觉检测评分器。

任务：判断生成内容是否完全基于提供的事实集，避免幻觉（编造信息）。

检测要点：
1. 事实一致性：回答中的所有关键事实必须在事实集中有对应支撑
2. 信息范围：不允许出现事实集中未提及的新信息
3. 合理推论：基于事实的合理总结可以接受，但不能编造细节
4. 具体数据：时间、数字、名称等必须与事实集一致或为概括性描述

评分标准：
- 'yes'：回答完全基于事实集，无幻觉内容
- 'no'：回答包含事实集中未提及、矛盾或编造的信息

输出要求：
仅输出'yes'或'no'，不要添加解释。

重要说明：
- 必须使用 "binary_score" 作为字段名
- 值只能是 "yes" 或 "no"
- 必须返回严格的JSON格式，不要包含任何 markdown 或代码块格式。
- 不要包含任何解释或其他文本

示例：
事实集：机器学习是人工智能的一个分支领域
回答：机器学习是人工智能的一个重要分支 → 'yes'
回答：机器学习是人工智能分支，起源于1950年代 → 'no'（起源于1950年代未提及）"""

hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),  # 系统角色设定
        ("human", "事实集: \n\n {documents} \n\n 生成内容: {generation}"),  # 用户输入模板
    ]
)

# 构建幻觉检测工作流
hallucination_grader_chain = (
        hallucination_prompt  # 使用幻觉检测提示模板
        | structured_llm_grader  # 调用结构化评分的LLM
)
