# failed_node.py
from graph2.graph_state2 import GraphState
from utils.log_utils import log


def failed(state: GraphState):
    """
    当系统无法解决问题时，返回固定的失败响应

    Args:
        state (GraphState): 当前图状态

    Returns:
        GraphState: 更新后的状态，包含失败消息
    """
    log.info("---无法解决问题，返回失败响应---")

    failed_message = (
        "很抱歉，经过多次尝试后我仍然无法找到满意的答案来解决您的问题。"
        "您可以尝试重新表述问题，或者稍后再试。"
    )

    return {
        "generation": failed_message,
        "documents": state.get("documents", []),
        "history": state.get("history", [])
    }
