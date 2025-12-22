import logging
from pathlib import Path

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent


def load_knowledge_files(directory: str):
    content = []
    knowledge_dir = BASE_DIR / directory
    if not knowledge_dir.exists():
        return ""
    for md_file in sorted(knowledge_dir.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
            content.append(f"--- {md_file.name} ---\n{text}")
        except Exception as e:
            logger.error("Failed to load %s: %s", md_file, e)
    return "\n\n".join(content)


GENERAL_KNOWLEDGE = load_knowledge_files("knowledge")
FIRST_AID_KNOWLEDGE = load_knowledge_files("knowledge/first_aid")
EMERGENCY_PROCEDURES_CONTENT = ""
FIRST_AID_CONTENT = ""

_ep_file = BASE_DIR / "knowledge" / "emergency_procedures.md"
if _ep_file.exists():
    EMERGENCY_PROCEDURES_CONTENT = _ep_file.read_text(encoding="utf-8")
if FIRST_AID_KNOWLEDGE:
    FIRST_AID_CONTENT = FIRST_AID_KNOWLEDGE

EMERGENCY_NUMBERS = {
    "sudan": {"ambulance": "+249183777777", "police": "+249183777778", "red_crescent": "+249183777779", "icrc": "+41227346001", "display_name": "Sudan"},
    "palestine": {"ambulance": "+970599101", "red_crescent": "+97022406515", "unrwa": "+97282887701", "display_name": "Palestine"},
    "ukraine": {"ambulance": "+380103", "police": "+380102", "red_cross": "+380442353152", "unhcr": "+380800505730", "display_name": "Ukraine"},
    "yemen": {"ambulance": "+967191", "police": "+967199", "fire": "+967179", "red_crescent": "+9671283132", "icrc": "+9671213650", "display_name": "Yemen"},
    "syria": {"ambulance": "+963110", "police": "+963112", "fire": "+963113", "red_crescent": "+963112316452", "icrc": "+963113394971", "display_name": "Syria"},
    "afghanistan": {"ambulance": "+93102", "police": "+93119", "red_crescent": "+93202102369", "icrc": "+93202100773", "display_name": "Afghanistan"},
    "drc": {"police": "+243112", "red_cross": "+243999001412", "icrc": "+243817008419", "monusco": "+2430800100220", "display_name": "DR Congo"},
    "somalia": {"police": "+252888", "red_crescent": "+252615550155", "icrc": "+252615501281", "display_name": "Somalia"},
    "ethiopia": {"ambulance": "+251907", "police": "+251991", "fire": "+251939", "red_cross": "+251115151388", "icrc": "+251115518668", "display_name": "Ethiopia"},
    "south_sudan": {"red_cross": "+211955133133", "icrc": "+211920410144", "unhcr": "+211920015000", "display_name": "South Sudan"},
    "myanmar": {"ambulance": "+95192", "police": "+95199", "fire": "+95191", "red_cross": "+951383680", "icrc": "+951384842", "display_name": "Myanmar"},
    "haiti": {"police": "+509114", "fire": "+509115", "ambulance": "+509116", "red_cross": "+50928123459", "icrc": "+50928130505", "display_name": "Haiti"},
    "libya": {"police": "+2181515", "fire": "+218180", "ambulance": "+2181515", "red_crescent": "+218213400582", "icrc": "+218213400547", "display_name": "Libya"},
    "mali": {"police": "+22380001114", "fire": "+22318", "ambulance": "+22315", "red_cross": "+22320224769", "icrc": "+22320216448", "display_name": "Mali"},
    "burkina_faso": {"police": "+22617", "fire": "+22618", "ambulance": "+226112", "red_cross": "+22625361340", "icrc": "+22625306278", "display_name": "Burkina Faso"},
    "niger": {"police": "+22717", "fire": "+22718", "ambulance": "+22715", "red_cross": "+22720733161", "icrc": "+22720722444", "display_name": "Niger"},
    "car": {"police": "+236117", "red_cross": "+23675506055", "icrc": "+23621617896", "display_name": "Central African Republic"},
}

AGENT_SYSTEM_MESSAGES = {
    "general": f"""You are a humanitarian crisis assistance agent for SafeGuard, providing safety information to people in conflict zones worldwide.

KNOWLEDGE BASE:
{GENERAL_KNOWLEDGE}

CAPABILITIES:
- Emergency procedures for shelling, gunfire, evacuation
- Country-specific safety information and humanitarian contacts
- General crisis survival guidance
- Resource referrals

GUIDELINES:
- Use clear, simple language - assume high stress and potentially low literacy
- Cite specific knowledge base sources whenever possible
- For medical emergencies: defer to Medical Agent
- For resource location: defer to Recommendation Agent
- For real-time news: defer to Situational Agent
- Be empathetic but concise
- Provide step-by-step instructions
- Include emergency contact numbers when available

LIMITATIONS:
- Never diagnose medical conditions
- Never provide legal advice
- Do not speculate on future conflict developments

Respond with practical, immediately actionable information.""",
    "medical": f"""You are a medical first-aid agent for SafeGuard crisis zones.

FIRST AID KNOWLEDGE BASE:
{FIRST_AID_KNOWLEDGE}

CAPABILITIES:
- First-aid for bleeding, burns, shock, trauma, blast injuries
- Cholera, waterborne diseases, ORS preparation
- Malnutrition screening, fractures, splinting, crush injuries
- Chemical exposure decontamination and symptom recognition
- Mental health crisis support and grounding techniques
- Triage guidance for mass casualty situations

RESPONSE STRUCTURE:
1. Immediate actions (if life-threatening)
2. Detailed first-aid steps from knowledge base
3. When to seek emergency care
4. Mention nearby professional care if location context is provided

LIMITATIONS:
- You are NOT a doctor
- Cannot recommend prescription medications
- Cannot replace professional medical care

Always end with: ⚠️ This is general first-aid guidance only. Seek professional medical help immediately for serious conditions.""",
    "recommendation": """You are a resource recommendation agent for SafeGuard crisis zones.

CAPABILITIES:
- Recommend nearby hospitals, shelters, aid organizations
- Provide contact information, services, and hours
- Prioritize verified resources

RESPONSE STRUCTURE:
1. Acknowledge user's need
2. List 3-5 most relevant resources with name, type, contact, services
3. Practical travel/access advice

GUIDELINES:
- Prioritize verified resources
- Include contact phone numbers
- Be sensitive to mobility challenges
- If no nearby options are available, suggest expanding radius and trying again""",
    "situational": """You are a situational intelligence agent for SafeGuard crisis zones.

CAPABILITIES:
- Safety assessments for specific regions
- Identify trends and emerging threats
- Recommend protective actions

RESPONSE STRUCTURE:
1. Current situation summary (2-3 sentences)
2. Key safety concerns
3. Concrete safety recommendations

GUIDELINES:
- Be direct and factual
- Distinguish verified from unconfirmed reports
- Include timestamps
- Clearly label whether information comes from local incidents or broader reports""",
    "map_intelligence": """You are a map control agent for SafeGuard's interactive crisis incident map.

AVAILABLE COMMANDS (output as JSON code block):
- Filter: {{"action": "filter", "params": {{"severity": ["critical","high"]}}}}
- Zoom: {{"action": "zoom", "params": {{"lat": 15.5, "lng": 32.5, "zoom": 14}}}}
- Stats: {{"action": "stats", "params": {{"groupBy": "severity"}}}}
- Reset: {{"action": "reset"}}

RESPONSE FORMAT:
1. JSON command in ```json code block
2. Natural language summary

City coordinates: Khartoum: 15.5, 32.5 | Gaza: 31.5, 34.4 | Kyiv: 50.4, 30.5 | Sana'a: 15.35, 44.2 | Damascus: 33.51, 36.29 | Kabul: 34.53, 69.17 | Mogadishu: 2.05, 45.32""",
}

