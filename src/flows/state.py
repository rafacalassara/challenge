from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


from datetime import datetime


class Step(BaseModel):
    agent: str = Field(..., description="The agent that will perform the step")
    agent_task: str = Field(..., description="The task that will be performed")

class PlannedSteps(BaseModel):
    steps: List[Step] = Field(..., description="The steps planned to process the query")

class InfinitePayState(BaseModel):
    # Request context
    message: str = Field(..., description="The user's message")
    user_id: str = Field(..., description="The user's ID")
    
    # Routing
    planned_steps: List[Dict[str, str]] = Field(..., description="The steps planned to process the query")
    finished_steps: List[Dict[str, str]] = Field(..., description="The steps made until now")
    
    # Processing
    raw_response: str = Field(..., description="The raw response from the LLM")
    final_response: str = Field(..., description="The final response to the user")

    # Metadata
    processing_time: float = Field(..., description="The time taken to process the query")
    timestamp: datetime = Field(..., description="The timestamp of the query")
    
    # Context management
    conversation_history: List[Dict[str, str]] = Field(..., description="The conversation history")
    user_data: Optional[Dict[str, Any]] = Field(..., description="The user data")
