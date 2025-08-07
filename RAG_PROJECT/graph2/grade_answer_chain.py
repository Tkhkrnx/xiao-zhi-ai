from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

from llm_models.all_llm import llm


# 数据模型 - 回答质量评分
class GradeAnswer(BaseModel):
    """评估回答是否解决用户问题的二元评分模型"""

    binary_score: str = Field(
        description="回答是否解决了问题，取值为'yes'或'no'"
    )


# 初始化带函数调用的LLM
structured_llm_grader = llm.with_structured_output(GradeAnswer)  # 绑定结构化输出到评分模型

# 提示词模板
system = """你是一个专业的回答质量评估专家。
请评估生成的回答是否合理地尝试解决了用户问题：

评分标准：
- 评为"yes"：回答合理地尝试解决用户问题，包括以下情况：
  * 直接解决了用户问题，提供了具体信息或解决方案
  * 回答合理地尝试解决用户问题，哪怕不完美；
  * 回答提供了相关信息、建议、解释、思路或解决方案；
  * 回答承认模型限制但仍提供了信息或建议；
  * 回答是礼貌性回应，如“你好”“有什么我可以帮忙的？”这类简单寒暄，也算是合理回应；
  * 闲聊类问题（如“你好”“你是谁”），回答给出相应回应即可评为“yes”。
  * 提供了替代方案或建议

- 评为"no"：回答没有合理地尝试解决用户问题，包括以下情况：
  * 明确表示无法回答或信息不足，无法给出具体信息（如"无法回答"、"信息不足"等）
  * 回答与问题完全无关
  * 回答明显错误、胡言乱语或重复用户问题
  * 回答仅为无意义或无实际内容的通用语句（如“这取决于具体情况”）且未提供任何信息

注意：只要回答合理地尝试解决问题，即使不完美也应评为"yes"。只有当回答明确表示无法回答，或表示信息不足等类似说法，或完全没有尝试解决问题时才评为"no"。

重要说明：
- 必须使用 "binary_score" 作为字段名
- 值只能是 "yes" 或 "no"
- 必须返回严格的JSON格式，不要包含任何 markdown 或代码块格式。
- 不要包含任何解释或其他文本
"""


answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),  # 系统角色设定
        ("human", "用户问题: \n\n {question} \n\n 生成回答: {generation}"),  # 用户输入模板
    ]
)

# 构建回答质量评估工作流
answer_grader_chain = (
        answer_prompt  # 使用回答评估提示模板
        | structured_llm_grader  # 调用结构化评分的LLM
)
