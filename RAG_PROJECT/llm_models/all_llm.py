from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI

from utils.env_utils import LLM_API_KEY, TAVILY_API_KEY

llm = ChatOpenAI(
    temperature=0,
    model='claude-3-5-haiku-20241022',  # 用不起sonnet...
    api_key=LLM_API_KEY,
    base_url="https://www.chataiapi.com/v1"
)

web_search_tool = TavilySearchResults(max_results=2, api_key=TAVILY_API_KEY)

# llm = ChatOpenAI(
#     temperature=0.5,
#     model='deepseek-chat',
#     api_key=DEEPSEEK_API_KEY,
#     base_url="https://api.deepseek.com")

def main():
    """
    测试LLM是否可以正常访问
    """
    try:
        # 简单的测试问题
        test_question = "你好，请简单介绍一下自己。"
        response = llm.invoke(test_question)
        print("LLM连接成功！")
        print("测试问题:", test_question)
        print("LLM回答:", response.content)
        return True
    except Exception as e:
        print("LLM连接失败:", str(e))
        return False

if __name__ == "__main__":
    main()