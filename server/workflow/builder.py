from langgraph.graph import StateGraph, END
from server.workflow.state import AgentState
from server.workflow.nodes.receive import receive
from server.workflow.nodes.messages import messages
from server.workflow.nodes.fetch import fetch
from server.workflow.nodes.generate import generate
from server.workflow.nodes.execute import execute
from server.workflow.nodes.analyze import analyze

def build_workflow() -> StateGraph:
    """LangGraph 워크플로우 빌더: 노드와 엣지 정의."""
    # 상태 그래프 생성
    workflow = StateGraph(
        AgentState
    )

    # 노드 추가
    workflow.add_node("receive", receive)
    workflow.add_node("fetch", fetch)
    workflow.add_node("generate", generate)
    workflow.add_node("execute", execute)
    workflow.add_node("analyze", analyze)

    # 엣지 추가
    workflow.set_entry_point("receive")

    # receive 조건부 엣지
    workflow.add_conditional_edges(
        "receive",
        lambda state: state.get("next", "generate"),
        {
            "fetch": "fetch",
            "generate": "generate",
            "execute": "execute",
            "end": END
        }
    )

    workflow.add_edge("fetch", END)

    # generate 조건부 엣지
    workflow.add_conditional_edges(
        "generate",
        lambda state: state.get("next", END),
        {
            "execute": "execute",
            "analyze": "analyze",
            "end": END
        }
    )

    # execute 고정 엣지
    workflow.add_edge("execute", "analyze")

    # analyze 고정 엣지
    workflow.add_edge("analyze", END)

    return workflow.compile()