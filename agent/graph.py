"""
Assemble the LangGraph StateGraph for the onboarding pipeline.
"""
from langgraph.graph import StateGraph, END
from .state import AgentState
from . import nodes


def build_graph():
    """
    Returns a compiled LangGraph runnable.
    The api_key is passed through the state dict, so no closures needed.
    """
    wf = StateGraph(AgentState)

    # ── register nodes ───────────────────────────────────────────────────
    wf.add_node("parse_structure",     nodes.parse_structure)
    wf.add_node("identify_tech_stack", nodes.identify_tech_stack)
    wf.add_node("find_entry_points",   nodes.find_entry_points)
    wf.add_node("summarize_modules",   nodes.summarize_modules)
    wf.add_node("trace_data_flow",     nodes.trace_data_flow)
    wf.add_node("extract_gotchas",     nodes.extract_gotchas)
    wf.add_node("compile_report",      nodes.compile_report)

    # ── linear pipeline ─────────────────────────────────────────────────
    wf.set_entry_point("parse_structure")
    wf.add_edge("parse_structure",     "identify_tech_stack")
    wf.add_edge("identify_tech_stack", "find_entry_points")
    wf.add_edge("find_entry_points",   "summarize_modules")
    wf.add_edge("summarize_modules",   "trace_data_flow")
    wf.add_edge("trace_data_flow",     "extract_gotchas")
    wf.add_edge("extract_gotchas",     "compile_report")
    wf.add_edge("compile_report",      END)

    return wf.compile()
