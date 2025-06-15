import json
from pathlib import Path
from typing import Dict, List, Optional
from app.utils.logger import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class FAQService:
    def __init__(self, faq_dir: Optional[str] = None):
        self.faq_dir = Path(faq_dir or settings.faq_directory_path)
        self.faq_content: Dict[str, str] = {}
        self.category_metadata: Dict[str, str] = {}
        self.load_category_metadata()
        self.load_faq_files()
    
    def load_category_metadata(self) -> None:
        """Load optional category metadata for descriptions."""
        metadata_file = self.faq_dir / "categories.json"
        try:
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.category_metadata = json.load(f)
                logger.info(f"Loaded category metadata for {len(self.category_metadata)} categories")
            else:
                logger.info("No category metadata file found, using default descriptions")
        except Exception as e:
            logger.warning(f"Error loading category metadata: {e}")
            self.category_metadata = {}
    
    def load_faq_files(self) -> None:
        """Load all FAQ files into memory with dynamic category discovery."""
        try:
            pattern = f"*{settings.faq_file_extension}"
            for faq_file in self.faq_dir.glob(pattern):
                # Skip the metadata file
                if faq_file.name == "categories.json":
                    continue
                    
                category = faq_file.stem
                content = faq_file.read_text(encoding="utf-8")
                self.faq_content[category] = content
                logger.info(f"Loaded FAQ category: {category}")
                
            if not self.faq_content:
                logger.warning(f"No FAQ files found in {self.faq_dir}")
        except Exception as e:
            logger.error(f"Error loading FAQ files: {e}")
            raise
    
    def get_available_categories(self) -> List[str]:
        """Get list of all available FAQ categories."""
        return list(self.faq_content.keys())
    
    def get_faq_content(self, category: str) -> str:
        """Get FAQ content for a specific category."""
        return self.faq_content.get(category, "")
    
    def is_valid_category(self, category: str) -> bool:
        """Check if a category is valid (has corresponding FAQ file)."""
        return category in self.faq_content
    
    def get_category_description(self, category: str) -> str:
        """Get description for a category, with fallback to generic description."""
        if category in self.category_metadata:
            return self.category_metadata[category]
        return f"{category} related questions"
    
    def build_function_definitions(self) -> List[Dict]:
        """Build OpenAI function definitions with dynamic categories."""
        available_categories = self.get_available_categories()
        
        if not available_categories:
            logger.warning("No FAQ categories available, FAQ function will be disabled")
            # Return only database functions if no FAQ categories exist
            return self._build_database_functions()
        
        # Build category descriptions
        category_descriptions = []
        for category in available_categories:
            desc = self.get_category_description(category)
            category_descriptions.append(f"'{category}' ({desc})")
        
        description_text = ", ".join(category_descriptions)
        
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "get_faq_answer",
                    "description": f"Answer business questions using company FAQ knowledge base. Available categories: {description_text}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": available_categories,
                                "description": f"FAQ category. Available options: {description_text}"
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
            }
        ]
        
        # Add database functions
        functions.extend(self._build_database_functions())
        return functions
    
    def _build_database_functions(self) -> List[Dict]:
        """Build database-related function definitions."""
        return [
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