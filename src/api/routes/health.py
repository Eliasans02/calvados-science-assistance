from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request):
    container = request.app.state.container
    return {
        "status": "ok",
        "agents": container.agent_registry.list_agents(),
    }
