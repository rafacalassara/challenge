from datetime import datetime
import warnings

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.models import MessageRequest, MessageResponse
from src.flows.main_flow import InfinitePayFlow


app = FastAPI(
    title="InfinitePay Agent Swarm",
    description="Agent Swarm usando CrewAI para InfinitePay",
    version="1.0.0",
)

# Suppress verbose Pydantic serialization warnings caused by 3rd-party objects (e.g., OpenAI/CrewAI)
warnings.filterwarnings(
    "ignore",
    message=r"Pydantic.*Serialization.*",
    category=UserWarning,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/process", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """Endpoint principal para processar mensagens"""
    # Provide a minimal valid initial_state for the Flow
    initial_state = {
        "message": "",
        "user_id": "",
        "planned_steps": [],
        "finished_steps": [],
        "raw_response": "",
        "final_response": "",
        "processing_time": 0.0,
        "timestamp": datetime.now(),
        "conversation_history": [],
        "user_data": None,
    }
    flow = InfinitePayFlow(initial_state=initial_state)
    inputs = {"message": request.message, "user_id": request.user_id}
    try:
        await flow.kickoff_async(inputs=inputs)
    except Exception as e:
        # Graceful fallback to keep API stable even if LLM or tools are unavailable
        flow.state.final_response = (
            "Desculpe, não consegui processar sua solicitação no momento. "
            "Tente novamente mais tarde."
        )
        flow.state.processing_time = float(flow.state.processing_time or 0.0)
    return MessageResponse(
        response=flow.state.final_response,
        processing_time=flow.state.processing_time,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "framework": "CrewAI"}


@app.get("/flow/plot")
async def plot_flow():
    """Endpoint para visualizar o flow"""
    initial_state = {
        "message": "",
        "user_id": "",
        "planned_steps": [],
        "finished_steps": [],
        "raw_response": "",
        "final_response": "",
        "processing_time": 0.0,
        "timestamp": datetime.now(),
        "conversation_history": [],
        "user_data": None,
    }
    flow = InfinitePayFlow(initial_state=initial_state)
    flow.plot("infinitepay_flow_plot")
    return {"message": "Flow plot generated: infinitepay_flow_plot.html"}


@app.get("/")
def root():
    return {"message": "Welcome to Challenge API"}
