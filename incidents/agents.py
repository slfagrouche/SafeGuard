from llama_index.core.agent.workflow import (
    AgentWorkflow,
    FunctionAgent,
)
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from typing import Dict, List
from datetime import datetime
from django.conf import settings
from .dynamodb import dynamodb_manager
from .geocoding import geocoding_manager

# Initialize LlamaIndex OpenAI LLM
llm = OpenAI(model="gpt-4", api_key=settings.OPENAI_API_KEY)

# Define the tools for each agent
def search_knowledge_base(query: str) -> str:
    """Search SafeGuard's knowledge base for relevant information."""
    # In the future, this could search through a Django model containing knowledge base entries
    return f"Knowledge base search results for: {query}"

def get_emergency_contacts() -> Dict:
    """Retrieve relevant emergency contact information."""
    return {
        "emergency": "911",
        "poison_control": "1-800-222-1222",
        "crisis_hotline": "988"
    }

def check_incident_map(location: str) -> List[Dict]:
    """Check the incident map for nearby emergencies."""
    try:
        # Get coordinates from location string
        lat, lng = geocoding_manager.geocode_address(location)
        if lat and lng:
            # Get incidents from DynamoDB
            incidents = dynamodb_manager.get_all_incidents()
            # Filter and format incidents
            nearby_incidents = []
            for incident in incidents:
                if incident.get('latitude') and incident.get('longitude'):
                    nearby_incidents.append({
                        "type": "incident",
                        "location": incident.get('address', f"{incident['latitude']}, {incident['longitude']}"),
                        "description": incident['description'],
                        "datetime": incident['datetime'].isoformat(),
                        "verified": incident['verified']
                    })
            return nearby_incidents
    except Exception as e:
        print(f"Error checking incident map: {e}")
    return []

def find_nearby_hospitals(location: str) -> List[Dict]:
    """Find hospitals near the specified location."""
    # This could be integrated with a real hospital database or API
    return [{"name": "City Hospital", "distance": "2.5 miles", "emergency": True}]

def provide_first_aid_guidance(situation: str) -> str:
    """Provide basic first aid guidance for common situations."""
    # This could be integrated with a Django model containing first aid information
    return f"First aid instructions for: {situation}"

def check_symptoms(symptoms: List[str]) -> Dict:
    """Analyze symptoms and provide general guidance."""
    return {
        "possible_conditions": ["..."],
        "severity": "moderate",
        "seek_medical_attention": True
    }

def find_shelters(criteria: Dict) -> List[Dict]:
    """Find appropriate shelters based on user criteria."""
    return [{"name": "Community Center", "capacity": "Available", "services": ["..."]}]

def suggest_resources(situation: str) -> List[Dict]:
    """Suggest relevant resources for the user's situation."""
    return [{"type": "financial_aid", "provider": "Red Cross", "contact": "..."}]

def create_safety_plan(risk_factors: List[str]) -> Dict:
    """Create a personalized safety plan."""
    return {
        "immediate_steps": ["..."],
        "long_term_actions": ["..."],
        "emergency_contacts": ["..."]
    }

# Create a single multimodal agent with all capabilities
multimodal_agent = FunctionAgent(
    name="multimodal_assistant",
    description="A comprehensive emergency assistance AI that handles all types of queries",
    system_prompt="""You are an advanced AI assistant specializing in emergency situations and safety. 
    You can provide general information, medical guidance, and personalized recommendations. 
    Always prioritize user safety and provide clear, accurate information. For medical situations, 
    advise seeking professional help when appropriate.""",
    tools=[
        FunctionTool.from_defaults(fn=search_knowledge_base),
        FunctionTool.from_defaults(fn=get_emergency_contacts),
        FunctionTool.from_defaults(fn=check_incident_map),
        FunctionTool.from_defaults(fn=find_nearby_hospitals),
        FunctionTool.from_defaults(fn=provide_first_aid_guidance),
        FunctionTool.from_defaults(fn=check_symptoms),
        FunctionTool.from_defaults(fn=find_shelters),
        FunctionTool.from_defaults(fn=suggest_resources),
        FunctionTool.from_defaults(fn=create_safety_plan),
    ],
    llm=llm,
)

# Create the workflow with initial state
workflow = AgentWorkflow(
    agents=[multimodal_agent],
    root_agent="multimodal_assistant",
    initial_state={
        "conversation_history": [],
        "current_emergency": None,
        "user_location": None,
        "risk_level": "low",
        "last_update": datetime.now().isoformat()
    }
)

async def chat(message: str, context: Dict = None) -> str:
    """Handle chat messages and return AI responses."""
    try:
        # Update workflow state with context if provided
        if context:
            workflow.state.update(context)
        
        # Run the workflow and ensure response is properly handled
        response = await workflow.run(user_msg=message)
        if isinstance(response, str):
            return response
        # Handle case where response might be a more complex object
        return str(response)
    except Exception as e:
        print(f"Error in chat: {e}")
        return "I apologize, but I encountered an error processing your request. Please try again."
