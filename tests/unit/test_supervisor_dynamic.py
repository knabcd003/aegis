import pytest
from langgraph.graph import END
from engines.analyst.supervisor import AgenticSupervisor
from engines.analyst.analyst import AnalystNode
from engines.analyst.risk_manager import RiskManagerNode

def test_supervisor_dynamic_linear_build():
    """Verify that a simple linear pipeline build works."""
    pipeline = ["analyst", "risk_manager"]
    supervisor = AgenticSupervisor(model="qwen3:8b", pipeline=pipeline)
    
    # Check that nodes are added
    # supervisor.graph.get_graph().nodes is a dict of node objects
    graph = supervisor.graph.get_graph()
    node_names = [n.id for n in graph.nodes.values()]
    assert "analyst" in node_names
    assert "risk_manager" in node_names
    
    # Check edges
    # __start__ -> analyst -> risk_manager -> __end__
    edges = [(e.source, e.target) for e in graph.edges]
    assert ("__start__", "analyst") in edges
    assert ("analyst", "risk_manager") in edges
    assert ("risk_manager", "__end__") in edges

def test_supervisor_dynamic_conditional_build():
    """Verify that explicit edges with conditional routing for risk_manager works."""
    pipeline = ["analyst", "risk_manager"]
    edges_config = {
        "risk_manager": {
            "veto": "END",
            "approve": "END"
        }
    }
    supervisor = AgenticSupervisor(model="qwen3:8b", pipeline=pipeline, edges=edges_config)
    
    graph = supervisor.graph.get_graph()
    
    # Check edges
    edges = [(e.source, e.target) for e in graph.edges]
    assert ("__start__", "analyst") in edges
    assert ("analyst", "risk_manager") in edges
    
    # risk_manager should have conditional edges to __end__
    # LangGraph represents conditional edges as multiple edges from the source if it can determine targets,
    # or it might have a virtual node/routing logic.
    # In our implementation, we use add_conditional_edges which adds edges from 'risk_manager' to '__end__'
    assert ("risk_manager", "__end__") in edges

def test_supervisor_unknown_agent_error():
    """Verify that an unknown agent name raises a clear error."""
    pipeline = ["analyst", "bogus_agent"]
    with pytest.raises(ValueError) as excinfo:
        AgenticSupervisor(model="qwen3:8b", pipeline=pipeline)
    assert "Unknown agent 'bogus_agent'" in str(excinfo.value)

def test_supervisor_dangling_node_error():
    """Verify that a node without a path to END raises an error."""
    pipeline = ["analyst", "risk_manager"]
    # Force a manual edge that only connects START->analyst but risk_manager is dangling
    edges_config = {
        "analyst": {"next": "END"} # Bypasses risk_manager
    }
    # Although analyst reaches END, risk_manager is in pipeline but has no path to END
    with pytest.raises(ValueError) as excinfo:
         AgenticSupervisor(model="qwen3:8b", pipeline=pipeline, edges=edges_config)
    assert "Dangling node detected: 'risk_manager'" in str(excinfo.value)

def test_supervisor_empty_pipeline_error():
    """Verify that an empty pipeline raises an error."""
    with pytest.raises(ValueError):
        AgenticSupervisor(model="qwen3:8b", pipeline=[])
