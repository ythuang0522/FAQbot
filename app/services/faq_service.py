import json
from pathlib import Path
from typing import Dict, List
from app.utils.logger import get_logger
from app.models.schemas import FAQFileCategory

logger = get_logger(__name__)


class FAQService:
    def __init__(self, faq_dir: str = "faqs"):
        self.faq_dir = Path(faq_dir)
        self.faq_content: Dict[str, str] = {}
        self.load_faq_files()
    
    def load_faq_files(self) -> None:
        """Load all FAQ files into memory with error handling."""
        try:
            for faq_file in self.faq_dir.glob("*.txt"):
                category = faq_file.stem
                if category in [e.value for e in FAQFileCategory]:
                    content = faq_file.read_text(encoding="utf-8")
                    self.faq_content[category] = content
                    logger.info(f"Loaded FAQ category: {category}")
                else:
                    logger.warning(f"Unknown FAQ category: {category}")
        except Exception as e:
            logger.error(f"Error loading FAQ files: {e}")
            raise
    
    def get_faq_content(self, category: str) -> str:
        """Get FAQ content for a specific category."""
        return self.faq_content.get(category, "")
        
    def build_function_definitions(self) -> List[Dict]:
        """Build OpenAI function definitions with balanced descriptions for speed and accuracy."""
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "get_faq_answer",
                    "description": "Answer business questions about sales, lab services, or reports using company FAQ knowledge base.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["sales", "labs", "reports"],
                                "description": "FAQ category: 'sales' (pricing, contracts), 'labs' (testing, samples), 'reports' (formats, delivery)"
                            },
                            "question": {
                                "type": "string",
                                "description": "The user's exact question"
                            }
                        },
                        "required": ["category", "question"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_organism_statistics",
                    "description": "Get organism counts and statistics from pathogen database. Use for 'how many', 'count', 'percentage' questions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "classification": {
                                "type": "string",
                                "enum": ["bacteria", "fungi", "virus", "parasite"],
                                "description": "Filter by organism type"
                            },
                            "nucleic_acid": {
                                "type": "string",
                                "enum": ["DNA", "RNA"],
                                "description": "For viruses only: filter by nucleic acid type"
                            },
                            "infection_type": {
                                "type": "string",
                                "enum": ["pneumonia", "meningitis", "bloodstream"],
                                "description": "Filter by infection type (use with pathogenic_level)"
                            },
                            "pathogenic_level": {
                                "type": "string",
                                "enum": ["H", "M", "L", "W", "D"],
                                "description": "Pathogenic risk: H=High, M=Medium, L=Low, W=Contaminant, D=Colonizer"
                            }
                        },
                        "required": [],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_and_list_organisms",
                    "description": "Search specific organisms OR list organisms by criteria. Use for organism profiles or listing requests.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "organism_name": {
                                "type": "string",
                                "description": "Specific organism name (e.g., 'Escherichia coli'). Leave empty for listing."
                            },
                            "list_mode": {
                                "type": "boolean",
                                "description": "Set true for 'list all', 'show', 'display' requests"
                            },
                            "classification": {
                                "type": "string",
                                "enum": ["bacteria", "fungi", "virus", "parasite"],
                                "description": "Filter by organism type"
                            },
                            "nucleic_acid": {
                                "type": "string",
                                "enum": ["DNA", "RNA"],
                                "description": "For viruses: DNA or RNA"
                            },
                            "infection_type": {
                                "type": "string",
                                "enum": ["pneumonia", "meningitis", "bloodstream"],
                                "description": "Filter by infection type"
                            },
                            "pathogenic_level": {
                                "type": "string",
                                "enum": ["H", "M", "L", "W", "D"],
                                "description": "Risk level (use with infection_type)"
                            }
                        },
                        "required": [],
                        "additionalProperties": False
                    }
                }
            }
        ]
        return functions 