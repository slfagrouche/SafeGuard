# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn
import asyncio
from datetime import datetime

class ChatRequest(BaseModel):
    content: str
    user_id: Optional[str] = None
    location: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    agent_name: str
    next_steps: list
    emergency_status: str

app = FastAPI(
    title="SafeGuard AI Help Hub",
    description="Emergency and Safety Assistance AI System",
    version="1.0.0"
)

class EnhancedAgent:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def process_message(self, message: str, context: Dict) -> Dict:
        if self.name == "GeneralHelpAgent":
            if "tornado" in message.lower():
                return {
                    "response": "If you hear a tornado siren:\n1. Immediately seek shelter in a basement or interior room\n2. Stay away from windows\n3. Keep monitoring local weather updates\n4. Have an emergency kit ready",
                    "next_steps": [
                        "Move to a safe location",
                        "Monitor weather updates",
                        "Contact emergency services if needed"
                    ],
                    "emergency_status": "high"
                }
            elif "fire" in message.lower():
                return {
                    "response": "In case of fire:\n1. Get out immediately\n2. Call 911\n3. Don't go back inside\n4. Meet at your designated meeting spot",
                    "next_steps": [
                        "Evacuate the building",
                        "Call emergency services",
                        "Wait for firefighters"
                    ],
                    "emergency_status": "high"
                }
            else:
                return {
                    "response": "How can I help you with your emergency situation? Please provide more details about what's happening.",
                    "next_steps": [
                        "Describe your situation",
                        "Share your location if relevant",
                        "Specify any immediate needs"
                    ],
                    "emergency_status": "unknown"
                }

        elif self.name == "MedicalAgent":
            if "chest pain" in message.lower():
                return {
                    "response": "Chest pain can be serious. Call 911 immediately. While waiting:\n1. Sit down and rest\n2. Take aspirin if recommended by doctor\n3. Stay calm and wait for help",
                    "next_steps": [
                        "Call 911 immediately",
                        "Find someone to stay with you",
                        "Have your medications list ready"
                    ],
                    "emergency_status": "critical"
                }
            elif "hospital" in message.lower():
                return {
                    "response": "I can help you locate the nearest hospital. Please share your location. In an emergency, always call 911 first.",
                    "next_steps": [
                        "Share your location",
                        "Specify emergency level",
                        "Call 911 if urgent"
                    ],
                    "emergency_status": "medium"
                }
            else:
                return {
                    "response": "What medical assistance do you need? Please describe your symptoms or situation.",
                    "next_steps": [
                        "Describe symptoms",
                        "Specify duration",
                        "Mention any existing conditions"
                    ],
                    "emergency_status": "unknown"
                }

        elif self.name == "RecommendationAgent":
            if "shelter" in message.lower():
                return {
                    "response": "I can help you find nearby shelters. Most community centers and schools serve as emergency shelters. Please share your location for specific recommendations.",
                    "next_steps": [
                        "Share your location",
                        "Specify any special needs",
                        "Indicate transportation needs"
                    ],
                    "emergency_status": "medium"
                }
            else:
                return {
                    "response": "I can provide personalized safety recommendations. What specific resources are you looking for?",
                    "next_steps": [
                        "Specify resource needs",
                        "Share current situation",
                        "Indicate urgency level"
                    ],
                    "emergency_status": "low"
                }

# Initialize agents
agents = {
    "general": EnhancedAgent("GeneralHelpAgent", "General emergency assistance"),
    "medical": EnhancedAgent("MedicalAgent", "Medical emergency assistance"),
    "recommendation": EnhancedAgent("RecommendationAgent", "Safety recommendations")
}

@app.get("/")
async def root():
    return {
        "message": "Welcome to SafeGuard AI Help Hub",
        "endpoints": [
            "/chat/general - General emergency assistance",
            "/chat/medical - Medical emergency assistance",
            "/chat/recommendation - Safety recommendations"
        ]
    }

@app.post("/chat/{agent_type}", response_model=ChatResponse)
async def chat(agent_type: str, request: ChatRequest):
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail="Agent type not found")
    
    # Process message with appropriate agent
    context = {
        "user_id": request.user_id,
        "location": request.location,
        "timestamp": datetime.now().isoformat()
    }
    
    result = await agents[agent_type].process_message(request.content, context)
    
    return ChatResponse(
        response=result["response"],
        agent_name=agents[agent_type].name,
        next_steps=result["next_steps"],
        emergency_status=result["emergency_status"]
    )

# Example test function
async def test_agents():
    """Test different agent scenarios"""
    test_cases = [
        ("general", "What should I do if I hear a tornado siren?"),
        ("medical", "I have chest pain and shortness of breath"),
        ("recommendation", "I need to find a shelter near downtown")
    ]
    
    for agent_type, message in test_cases:
        print(f"\nTesting {agent_type.title()} Agent...")
        request = ChatRequest(content=message)
        response = await chat(agent_type, request)
        print(f"Query: {message}")
        print(f"Response: {response.dict()}")

if __name__ == "__main__":
    # For testing
    asyncio.run(test_agents())