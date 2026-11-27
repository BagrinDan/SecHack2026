from fastapi import APIRouter

import state

router = APIRouter()


@router.get("/")
async def root():
    return {"status": "ok", "service": "MuleTrace MD"}


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "nodes": state.graph.number_of_nodes(),
        "edges": state.graph.number_of_edges(),
    }
