from pprint import pprint
from typing import Dict, Any

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from draw_png import draw_graph
from graph2.failed_node import failed
# from draw_png import draw_graph
from graph2.generate_node2 import generate
from graph2.grade_answer_chain import answer_grader_chain
from graph2.grade_documents_node import grade_documents
from graph2.grade_hallucinations_chain import hallucination_grader_chain
from graph2.graph_state2 import GraphState
from graph2.llm_direct_node import llm_direct
from graph2.query_route_chain import question_router_chain
from graph2.retriever_node import retrieve
from graph2.transform_query_node import transform_query
from graph2.web_search_node import web_search
from utils.log_utils import log


def grade_generation_v_documents_and_question(state):
    """
    评估生成结果是否基于文档并正确回答问题
    Args:
        state (dict): 当前图状态，包含问题、文档和生成结果
    Returns:
        str: 下一节点的名称（useful/not useful/not supported）
    """
    log.info("---检查生成内容是否存在幻觉---")  # 阶段标识
    question = state["question"]  # 获取用户问题
    documents = state["documents"]  # 获取参考文档
    generation = state["generation"]  # 获取生成结果
    generate_retry_count = state.get("generate_retry_count", 0)
    web_search_count = state.get("web_search_count", 0)
    # 检查生成内容是否存在幻觉
    score = hallucination_grader_chain.invoke({"documents": documents, "generation": generation})
    grade = score.binary_score

    if grade == "yes":  # 如果生成基于文档
        log.info("---判定：生成内容基于参考文档---")
        # 检查是否准确回答问题
        log.info("---评估：生成回答与问题的匹配度---")
        score = answer_grader_chain.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == "yes":  # 如果正确回答问题
            log.info("---判定：生成内容准确回答问题---")
            return "useful"  # 返回有用结果
        else:  # 如果没有回答问题
            log.info("---判定：生成内容未能准确回答问题---")
            if web_search_count >= 2:
                log.info("---网络搜索已执行2次仍无法解决问题，直接结束---")
                return "cannot answer"
            if generate_retry_count >= 2:  # 降低重试次数阈值
                log.info("---有相关文档时，已重试2次仍无法解决问题，转为web查询问题---")
                return "web_search"  # 即使不够完美也接受
            return "not useful"  # 返回无用结果
    else:  # 如果生成不基于文档
        log.info("---判定：生成内容未基于参考文档---")
        if web_search_count >= 2:
            log.info("---网络搜索已执行2次仍无法解决问题，直接结束---")
            return "cannot answer"
        # 检查是否达到最大重试次数
        if generate_retry_count >= 2:  # 限制重试次数
            log.info("---已达到最大重试次数2，转为优化查询---")
            return "not useful"  # 转到transform_query而不是继续重试
        else:
            log.info("---将重新尝试生成---")
            return "not supported"  # 返回不支持结果，继续重试


def decide_to_generate(state):
    """
    决定是生成回答还是重新优化问题

    Args:
        state (dict): 当前图状态，包含问题和过滤后的文档

    Returns:
        str: 下一节点的名称（transform_query或generate）
    """
    log.info("---ASSESS GRADED DOCUMENTS---")  # 阶段标识

    filtered_documents = state["documents"]  # 获取已过滤文档
    transform_count = state.get("transform_count", 0)

    if not filtered_documents:  # 如果没有相关文档
        if transform_count >= 2:
            log.info("---决策：所有文档都与问题无关,并且已经循环了2次，转为web查询问题---")
            return "web_search"  # 返回问题优化节点
        log.info("---决策：所有文档都与问题无关，将转换查询问题---")
        return "transform_query"  # 返回问题优化节点
    else:
        # 如果有相关文档
        log.info("---决策：生成最终回答---")
        return "generate"  # 返回回答生成节点

def decide_to_end(state):
    """
    评估是否正确回答问题

    Args:
        state (dict): 当前图状态，包含问题和过滤后的文档

    Returns:
        str: 下一节点的名称（transform_query或generate）
    """
    log.info("---ASSESS LLM---")  # 阶段标识
    question = state["question"]  # 获取用户问题
    generation = state["generation"]  # 获取生成结果

    score = answer_grader_chain.invoke({"question": question, "generation": generation})
    grade = score.binary_score
    if grade == "yes":  # 如果正确回答问题
        log.info("---判定：生成内容准确回答问题---")
        return "useful"  # 返回有用结果
    else:  # 如果没有回答问题
        log.info("---判定：生成内容未能准确回答问题---")
        return "not useful"  # 返回无用结果


def route_question(state):
    """
    路由问题到网络搜索或RAG流程
    Args:
        state (dict): 当前图状态，包含用户问题

    Returns:
        str: 下一节点的名称（web_search或vectorstore）
    """
    log.info("---ROUTE QUESTION---")  # 阶段标识
    question = state["question"]  # 获取用户问题
    chat_history = state.get("chat_history", [])  # 获取对话历史
    # 格式化对话历史
    formatted_history = "\n".join(["{msg['type']}: {msg['content']}" for msg in chat_history])

    # 调用问题路由器，提供所有需要的变量
    source = question_router_chain.invoke({
        "question": question,
        "history": formatted_history  # 提供 history 变量
    })

    # 根据路由结果决定下一个节点
    if source.datasource == "web_search":
        log.info("---路由到web搜索---")
        return "web_search"
    elif source.datasource == "vectorstore":
        log.info("---路由到RAG系统---")
        return "vectorstore"
    elif source.datasource == "llm_direct":
        log.info("---路由到LLM自答---")
        return "llm_direct"

# 初始化工作流图
workflow = StateGraph(GraphState)

# 定义各状态节点
workflow.add_node("llm_direct", llm_direct)  # LLM 自答节点
workflow.add_node("web_search", web_search)  # 网络搜索节点
workflow.add_node("retrieve", retrieve)  # 文档检索节点
workflow.add_node("grade_documents", grade_documents)  # 文档相关性评分节点
workflow.add_node("generate", generate)  # 回答生成节点
workflow.add_node("transform_query", transform_query)  # 查询优化节点
workflow.add_node("failed", failed)

# 起始路由判断
workflow.add_conditional_edges(
    START,
    route_question,
    {
        "web_search": "web_search",
        "vectorstore": "retrieve",
        "llm_direct": "llm_direct"
    }
)

# 添加固定边
workflow.add_edge("web_search", "generate")  # 网络搜索后直接生成回答
workflow.add_edge("retrieve", "grade_documents")
workflow.add_edge("failed", END)# 检索后评估文档相关性
workflow.add_conditional_edges(
    "llm_direct",
    decide_to_end,
    {
        "useful": END,
        "not useful": "web_search"
    }
)

# 文档评估后的条件分支
workflow.add_conditional_edges(
    'grade_documents',
    decide_to_generate,
    {
        "web_search": "web_search",
        "transform_query": "transform_query",
        "generate": "generate"
    }
)

# 生成结果评估后的条件分支
workflow.add_conditional_edges(
    "generate",  # 生成节点
    grade_generation_v_documents_and_question,  # 生成质量评估函数
    {
        "not supported": "generate",  # 生成不符合要求时重试
        "useful": END,  # 生成符合要求时结束
        "not useful": "transform_query",  # 生成无用结果时优化查询
        "web_search": "web_search",  # 添加这行 - 生成无法解决时转向网络搜索
        "cannot answer": "failed"
    },
)

workflow.add_edge("transform_query", "retrieve")  # 查询优化后重新检索

# 编译工作流
graph = workflow.compile()

# draw_graph(graph, '../graph_rag.png')

# 执行工作流

_printed = set()  # set集合，避免重复打印

# 添加会话存储
session_store = {}

def get_or_create_session(session_id: str):
    """获取或创建会话"""
    if session_id not in session_store:
        session_store[session_id] = []
    return session_store[session_id]


# 执行工作流
def run_chat(session_id: str = "default"):
    global _printed  # 声明使用全局变量
    _printed.clear()  # 每次新对话清空已打印记录

    chat_history = get_or_create_session(session_id)

    while True:
        question = input('用户：')
        # 处理空输入
        if not question:  # 空字符串、纯空格等
            print("请输入有效问题（输入 'q'、'exit' 或 'quit' 退出）")
            continue
        if question.lower() in ['q', 'exit', 'quit']:
            print('对话结束，拜拜！')
            break
        else:
            inputs = {
                "question": question,
                "chat_history": chat_history
            }

            # 流式执行工作流
            final_state = None
            for output in graph.stream(inputs, {"recursion_limit": 50}):
                for key, value in output.items():
                    # 打印当前节点名称
                    pprint(f"Node '{key}':")
                    _printed.add(key)
                    # 可选：打印每个节点的完整状态信息
                    # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
                pprint("\n---\n")
                final_state = value  # 保存最终状态

            # 打印最终生成结果
            if final_state and "generation" in final_state:
                pprint(final_state["generation"])
                print()

                # 更新会话历史
                if "chat_history" in final_state:
                    session_store[session_id] = final_state["chat_history"]
                    chat_history = final_state["chat_history"]

# 使用示例
if __name__ == "__main__":
    run_chat("session_1")
