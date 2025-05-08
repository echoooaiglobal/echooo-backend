from pydantic import BaseModel
from typing import List, Optional

class SimulationRequest(BaseModel):
    target_usernames: Optional[List[str]] = []
    session_duration_minutes: int = 30
    behavior_type: str = "casual_browser"
