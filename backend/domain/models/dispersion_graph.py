from typing import List

from pydantic import BaseModel, Field

from .graph_edge import GraphEdge
from .graph_node import GraphNode


class DispersionGraph(BaseModel):
    root_tx_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
