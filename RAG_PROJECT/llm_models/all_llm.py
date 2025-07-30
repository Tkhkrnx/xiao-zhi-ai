from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI

from utils.env_utils import LLM_API_KEY, TAVILY_API_KEY

llm = ChatOpenAI(
    temperature=0,
    model='qwen-max',  # 或 qwen-turbo, qwen-max
    api_key=LLM_API_KEY,
    base_url="https://www.chataiapi.com/v1"
)

web_search_tool = TavilySearchResults(max_results=2, api_key=TAVILY_API_KEY)

# llm = ChatOpenAI(
#     temperature=0.5,
#     model='deepseek-chat',
#     api_key=DEEPSEEK_API_KEY,
#     base_url="https://api.deepseek.com")