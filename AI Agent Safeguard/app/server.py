from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
from pydantic import BaseModel
import os
import logging
from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime
import json
from ratelimit import limits, sleep_and_retry
import re
from pytz import timezone as pytz_timezone
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, END, START
from dotenv import load_dotenv

# Optional LangSmith integration
try:
    from langsmith import Client as LangSmithClient
    from langchain.callbacks.manager import CallbackManager
    from langsmith import traceable
except ImportError:
    LangSmithClient = None
    CallbackManager = None
    traceable = lambda x: x

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Rate limiting constants
CALLS_PER_MINUTE = 10
PERIOD_SECONDS = 60

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
PDF_PATH = os.getenv("MEDICAL_PDF_PATH", "default_medical_manual.pdf")

# Validate environment variables
if not all([OPENAI_API_KEY, TAVILY_API_KEY]):
    logger.error("Missing required API keys: OPENAI_API_KEY and TAVILY_API_KEY must be set in .env")
    raise ValueError("API keys not configured")

# LangSmith setup
if LANGSMITH_API_KEY and LangSmithClient:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    langsmith_client = LangSmithClient()
    callback_manager = CallbackManager([])
    logger.info("LangSmith tracing enabled")
else:
    callback_manager = None
    logger.info("LangSmith tracing disabled")

# Define the agent state
class AgentState(TypedDict):
    query: str
    agent_type: Optional[str]
    knowledge_info: List[Dict[str, Any]]
    search_results: List[Dict[str, Any]]
    response: str
    sources: Dict[str, Any]
    timestamp: str

# Shared tools
llm = ChatOpenAI(
    temperature=0.7,
    model="gpt-3.5-turbo",
    api_key=OPENAI_API_KEY,
    callbacks=callback_manager,
)
tavily_search = TavilySearchResults(max_results=3, api_key=TAVILY_API_KEY)

# Knowledge Base Manager
class KnowledgeBaseManager:
    """Manages a PDF-based knowledge base for medical queries."""

    def __init__(self, pdf_path: str):
        self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        self.vector_stores: Dict[str, FAISS] = {}
        self.initialized = False
        self._initialize_knowledge_base(pdf_path)

    def _initialize_knowledge_base(self, pdf_path: str) -> None:
        """Initialize the knowledge base from a PDF file."""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            if not documents:
                raise ValueError("No content loaded from PDF")
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            split_docs = text_splitter.split_documents(documents)
            self.vector_stores["medical"] = FAISS.from_documents(split_docs, self.embeddings)
            self.initialized = True
            logger.info("Knowledge base initialized successfully from %s", pdf_path)
        except Exception as e:
            logger.error("Failed to initialize knowledge base: %s", str(e))
            self.initialized = False

    def query_knowledge_base(self, category: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Query the knowledge base synchronously."""
        if not self.initialized:
            logger.warning("Knowledge base not initialized")
            return [{"content": "Knowledge base not initialized", "metadata": {}}]
        if category not in self.vector_stores:
            logger.warning("Category '%s' not found in knowledge base", category)
            return [{"content": f"No knowledge base for category '{category}'", "metadata": {}}]
        try:
            docs = self.vector_stores[category].similarity_search(query, k=k)
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        except Exception as e:
            logger.error("Error querying knowledge base for category '%s': %s", category, str(e))
            return [{"content": "Error querying knowledge base", "metadata": {}}]

knowledge_base = KnowledgeBaseManager(PDF_PATH)

# Agent Nodes
@traceable
def route_query(state: AgentState, config: Optional[Dict[str, Any]] = None) -> AgentState:
    """Route the query to the appropriate agent."""
    query_lower = state["query"].lower()
    logger.debug("Routing query: %s", state["query"])
    if "time is it" in query_lower:
        state["agent_type"] = "time_check"
    else:
        try:
            router_prompt = PromptTemplate(
                template="""Determine which agent should handle this query:
                1. general_help - General information
                2. medical - Medical advice
                3. recommendation - Resource recommendations
                Query: {query}
                Respond with ONE option (e.g., 'general_help', 'medical', 'recommendation').""",
                input_variables=["query"],
            )
            response = llm.invoke(router_prompt.format(query=state["query"]))
            agent_type = response.content.strip().lower()
            match = re.search(r"(general_help|medical|recommendation)", agent_type)
            if match:
                state["agent_type"] = match.group(0)
            else:
                logger.warning("Invalid agent type from LLM: %s, defaulting to general_help", agent_type)
                state["agent_type"] = "general_help"
        except Exception as e:
            logger.error("Error routing query '%s': %s, defaulting to general_help", state["query"], str(e))
            state["agent_type"] = "general_help"
    logger.info("Routed query '%s' to %s", state["query"], state["agent_type"])
    return state

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=PERIOD_SECONDS)
@traceable
def time_check(state: AgentState, config: Optional[Dict[str, Any]] = None) -> AgentState:
    """Fetch the current time for a location in the query."""
    try:
        query_lower = state["query"].lower()
        location = "London"
        if " in " in query_lower:
            location = query_lower.split(" in ")[-1].strip().capitalize()
        tz = pytz_timezone("Europe/London") if location.lower() == "london" else pytz_timezone("UTC")
        current_time = datetime.now(tz)
        state["response"] = (
            f"The current time in {location} is {current_time.strftime('%I:%M %p')} "
            f"on {current_time.strftime('%A, %B %d, %Y')}."
        )
        state["search_results"] = []
        state["sources"] = {"local": f"Calculated using {tz.zone} timezone"}
        logger.info("Time calculated for %s: %s", location, state["response"])
    except Exception as e:
        logger.error("Error in time_check for query '%s': %s", state["query"], str(e))
        state["response"] = "Error fetching time"
        state["sources"] = {}
    return state

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=PERIOD_SECONDS)
@traceable
def general_help(state: AgentState, config: Optional[Dict[str, Any]] = None) -> AgentState:
    """Handle general-purpose queries."""
    prompt = PromptTemplate(
        template="""You are a helpful assistant.
        Knowledge base: {knowledge_info}
        Search results: {search_results}
        Query: {query}
        Provide a concise, accurate answer combining both sources. If no relevant info is found, say so.""",
        input_variables=["knowledge_info", "search_results", "query"],
    )
    try:
        knowledge_info = knowledge_base.query_knowledge_base("medical", state["query"])
        tavily_response = tavily_search.invoke(state["query"])
        knowledge_text = "\n".join([doc["content"] for doc in knowledge_info]) or "No relevant knowledge base info."
        search_text = "\n".join([result["content"] for result in tavily_response]) or "No relevant search results."
        response = llm.invoke(prompt.format(
            knowledge_info=knowledge_text,
            search_results=search_text,
            query=state["query"]
        ))
        state["response"] = response.content
        state["search_results"] = tavily_response
        state["sources"] = {"knowledge_base": knowledge_info, "tavily": tavily_response}
        logger.info("General help processed for query '%s'", state["query"])
    except Exception as e:
        logger.error("Error in general_help for query '%s': %s", state["query"], str(e))
        state["response"] = "Error processing query"
        state["sources"] = {}
    return state

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=PERIOD_SECONDS)
@traceable
def medical_assist(state: AgentState, config: Optional[Dict[str, Any]] = None) -> AgentState:
    """Handle medical queries with a disclaimer."""
    prompt = PromptTemplate(
        template="""You are a medical assistant using a medical knowledge base.
        IMPORTANT: Include this disclaimer: "This is not a substitute for professional medical advice. Consult a healthcare provider for serious conditions."
        Medical info with pages: {medical_info}
        Search results: {search_results}
        Query: {query}
        Provide accurate medical info with page references and emphasize safety. If no relevant info, say so.""",
        input_variables=["medical_info", "search_results", "query"],
    )
    try:
        medical_info = knowledge_base.query_knowledge_base("medical", state["query"])
        tavily_response = tavily_search.invoke(state["query"])
        medical_info_formatted = "\n".join([
            f"Content: {doc['content']}\nPage: {doc['metadata'].get('page', 'unknown')}"
            for doc in medical_info
        ]) or "No relevant medical info found."
        search_text = "\n".join([result["content"] for result in tavily_response]) or "No relevant search results."
        response = llm.invoke(prompt.format(
            medical_info=medical_info_formatted,
            search_results=search_text,
            query=state["query"]
        ))
        state["response"] = response.content
        state["search_results"] = tavily_response
        state["sources"] = {
            "knowledge_base": [
                {"content": doc["content"], "page": doc["metadata"].get("page", "unknown")}
                for doc in medical_info
            ],
            "tavily": tavily_response,
        }
        logger.info("Medical assist processed for query '%s'", state["query"])
    except Exception as e:
        logger.error("Error in medical_assist for query '%s': %s", state["query"], str(e))
        state["response"] = "Error processing medical query"
        state["sources"] = {}
    return state

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=PERIOD_SECONDS)
@traceable
def recommend_resources(state: AgentState, config: Optional[Dict[str, Any]] = None) -> AgentState:
    """Provide resource recommendations."""
    prompt = PromptTemplate(
        template="""You are a recommendation agent.
        Knowledge base info: {resource_info}
        Search results: {search_results}
        Query: {query}
        Provide actionable recommendations. If no relevant info, suggest consulting a professional.""",
        input_variables=["resource_info", "search_results", "query"],
    )
    try:
        resource_info = knowledge_base.query_knowledge_base("medical", state["query"])
        tavily_response = tavily_search.invoke(state["query"])
        resource_text = "\n".join([doc["content"] for doc in resource_info]) or "No relevant knowledge base info."
        search_text = "\n".join([result["content"] for result in tavily_response]) or "No relevant search results."
        response = llm.invoke(prompt.format(
            resource_info=resource_text,
            search_results=search_text,
            query=state["query"]
        ))
        state["response"] = response.content
        state["search_results"] = tavily_response
        state["sources"] = {"knowledge_base": resource_info, "tavily": tavily_response}
        logger.info("Recommendations processed for query '%s'", state["query"])
    except Exception as e:
        logger.error("Error in recommend_resources for query '%s': %s", state["query"], str(e))
        state["response"] = "Error processing recommendation query"
        state["sources"] = {}
    return state

@traceable
def finalize(state: AgentState, config: Optional[Dict[str, Any]] = None) -> AgentState:
    """Finalize the response with a timestamp."""
    try:
        state["timestamp"] = datetime.now(pytz_timezone("UTC")).isoformat()
        logger.debug("Finalized state with timestamp: %s", state["timestamp"])
    except Exception as e:
        logger.error("Error in finalize: %s", str(e))
    return state

# Workflow setup
workflow = StateGraph(AgentState)
workflow.add_node("route", route_query)
workflow.add_node("time_check", time_check)
workflow.add_node("general_help", general_help)
workflow.add_node("medical", medical_assist)
workflow.add_node("recommendation", recommend_resources)
workflow.add_node("finalize", finalize)

workflow.set_entry_point("route")
workflow.add_conditional_edges(
    "route",
    lambda state: state["agent_type"] or "general_help",
    {
        "time_check": "time_check",
        "general_help": "general_help",
        "medical": "medical",
        "recommendation": "recommendation",
    },
)
for node in ["time_check", "general_help", "medical", "recommendation"]:
    workflow.add_edge(node, "finalize")
workflow.set_finish_point("finalize")

# Compile the graph
graph = workflow.compile()

# FastAPI app setup
app = FastAPI(
    title="AI Agent Safeguard",
    description="An AI agent for time, medical, and general queries",
    version="0.1.0",
)

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

# Pydantic model for API request
class QueryRequest(BaseModel):
    query: str

# Add LangServe route
add_routes(
    app,
    graph,
    path="/agent",
    input_type=QueryRequest,
    output_type=Dict[str, Any],
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)