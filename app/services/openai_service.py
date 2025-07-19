import json
import time
import uuid
from typing import Dict, List, Any
from openai import OpenAI
from app.config import get_settings
from app.services.faq_service import FAQService
from app.services.database_service import DatabaseService
from app.utils.logger import get_logger
from app.utils.exceptions import OpenAIServiceError, FAQNotFoundError

settings = get_settings()
logger = get_logger(__name__)


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.faq_service = FAQService()
        self.database_service = DatabaseService()
    
    async def get_faq_answer(self, question: str, conversation_id: str = None) -> Dict:
        """
        Get FAQ answer using OpenAI function calling - Strategy 3 implementation.
        Returns: {answer, category, conversation_id, processing_time}
        """
        start_time = time.time()
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        try:
            # Step 1: Determine which functions to call
            step1_start = time.time()
            tool_calls = await self._get_function_calls(question)
            step1_time = time.time() - step1_start
            logger.debug(f"Step 1 (function calls) took: {step1_time:.3f}s")
            
            # No tool calls means out of scope
            if not tool_calls:
                return await self._handle_out_of_scope(question, conversation_id, start_time)
            
            # Step 2: Execute the functions
            step2_start = time.time()
            function_results = await self._execute_functions(tool_calls)
            step2_time = time.time() - step2_start
            logger.debug(f"Step 2 (function execution) took: {step2_time:.3f}s")
            
            # Step 3: Generate final answer with function results
            step3_start = time.time()
            answer, category = await self._generate_final_answer(question, tool_calls, function_results)
            step3_time = time.time() - step3_start
            logger.debug(f"Step 3 (final answer generation) took: {step3_time:.3f}s")
            
            processing_time = time.time() - start_time
            logger.debug(f"Total processing time: {processing_time:.3f}s")
            
            return {
                "answer": answer,
                "category": category,
                "conversation_id": conversation_id,
                "processing_time": round(processing_time, 3)
            }
            
        except Exception as e:
            logger.error(f"Error in get_faq_answer: {e}")
            raise OpenAIServiceError(f"Failed to process question: {str(e)}")
    
    async def _get_function_calls(self, question: str) -> List[Any]:
        """Get function calls from OpenAI using the consolidated function definitions."""
        try:
            api_start = time.time()
            functions = self.faq_service.build_function_definitions()
            
            logger.info(f"Making OpenAI API call #1 (function selection) with model: {settings.openai_model}")
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an intelligent assistant that provides both FAQ support and pathogen database information.
IMPORTANT RULES:
- Use the most specific function for the question type
- Do not call any functions if the question is completely unrelated to the functions
"""
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                tools=functions,
                tool_choice="auto",
                #temperature=settings.openai_temperature,
                #max_tokens=settings.openai_max_tokens
            )
            
            api_time = time.time() - api_start
            logger.debug(f"OpenAI API call #1 took: {api_time:.3f}s")
            
            message = response.choices[0].message
            tool_calls = message.tool_calls if message.tool_calls else []
            
            logger.info(f"OpenAI returned {len(tool_calls)} function calls for question")
            return tool_calls
            
        except Exception as e:
            logger.error(f"Error getting function calls: {e}")
            raise
    
    async def _execute_functions(self, tool_calls: List[Any]) -> List[Dict]:
        """Execute the actual functions based on OpenAI's tool calls."""
        results = []
        
        for tool_call in tool_calls:
            try:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing function: {function_name} with args: {arguments}")
                
                if function_name == "get_faq_answer":
                    result = await self._execute_faq_function(arguments)
                elif function_name == "get_organism_statistics":
                    result = await self._execute_statistics_function(arguments)
                elif function_name == "search_and_list_organisms":
                    result = await self._execute_search_and_list_function(arguments)
                else:
                    logger.warning(f"Unknown function: {function_name}")
                    result = {"error": f"Unknown function: {function_name}"}
                
                results.append({
                    "function_name": function_name,
                    "arguments": arguments,
                    "result": result,
                    "tool_call_id": tool_call.id
                })
                
            except Exception as e:
                logger.error(f"Error executing function {tool_call.function.name}: {e}")
                results.append({
                    "function_name": tool_call.function.name,
                    "error": str(e),
                    "tool_call_id": tool_call.id
                })
        
        return results
    
    async def _execute_faq_function(self, arguments: Dict) -> Dict:
        """Execute the get_faq_answer function."""
        category = arguments.get("category")
        question = arguments.get("question")
        
        if not category or not self.faq_service.is_valid_category(category):
            available_categories = self.faq_service.get_available_categories()
            raise ValueError(f"Invalid FAQ category: {category}. Available categories: {available_categories}")
        
        faq_content = self.faq_service.get_faq_content(category)
        if not faq_content:
            raise FAQNotFoundError(f"FAQ content not found for category: {category}")
        
        return {
            "type": "faq",
            "category": category,
            "content": faq_content,
            "success": True
        }
    
    async def _execute_statistics_function(self, arguments: Dict) -> Dict:
        """Execute the get_organism_statistics function."""
        stats = self.database_service.get_organism_statistics(
            classification=arguments.get("classification"),
            nucleic_acid=arguments.get("nucleic_acid"),
            infection_type=arguments.get("infection_type"),
            pathogenic_level=arguments.get("pathogenic_level")
        )
        
        return {
            "type": "database_statistics",
            "statistics": stats,
            "success": True
        }
    
    async def _execute_search_and_list_function(self, arguments: Dict) -> Dict:
        """Execute the search_and_list_organisms function."""
        search_result = self.database_service.search_and_list_organisms(
            organism_name=arguments.get("organism_name"),
            list_mode=arguments.get("list_mode", False),
            classification=arguments.get("classification"),
            nucleic_acid=arguments.get("nucleic_acid"),
            infection_type=arguments.get("infection_type"),
            pathogenic_level=arguments.get("pathogenic_level")
        )
        
        return {
            "type": "organism_search_and_list",
            "result": search_result,
            "success": True
        }
    
    async def _generate_final_answer(self, question: str, tool_calls: List[Any], function_results: List[Dict]) -> tuple[str, str]:
        """Generate the final answer using function results."""
        try:
            logger.info(f"Generating final answer for question: {question}")
            # Prepare messages with function results
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful assistant providing answers based on function results. 
                    
                    Guidelines:
                    - Use the function results to provide accurate, helpful responses
                    - Do not answer based on your own knowledge.
                    - Be concise but informative
                    - Use a friendly, professional tone to answer on behalf of 亞洲準譯高階主管(Asia Pathogenomics)"""
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
            
            # Add tool calls and results to conversation
            for i, tool_call in enumerate(tool_calls):
                # Add the assistant's tool call
                messages.append({
                    "role": "assistant",
                    "tool_calls": [tool_call]
                })
                
                # Add the function result
                function_result = function_results[i]
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(function_result["result"])
                })
            
            # Get final response from OpenAI
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                #temperature=settings.openai_temperature,
                #max_tokens=settings.openai_max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Determine category from function calls
            category = self._determine_category_from_functions(function_results)
            
            logger.info(f"Generated final answer for category: {category}")
            return answer, category
            
        except Exception as e:
            logger.error(f"Error generating final answer: {e}")
            raise
    
    def _determine_category_from_functions(self, function_results: List[Dict]) -> str:
        """Determine the response category based on executed functions."""
        for result in function_results:
            function_name = result.get("function_name")
            
            if function_name == "get_faq_answer":
                return result["result"]["category"]
            elif function_name in ["get_organism_statistics", "search_and_list_organisms"]:
                return "database_stats"
        
        return "out_of_scope"
    
    async def _handle_out_of_scope(self, question: str, conversation_id: str, start_time: float) -> Dict:
        """Handle questions that don't match any function."""
        logger.info(f"Question outside scope: {question[:100]}...")
        processing_time = time.time() - start_time
        
        return {
            "answer": "抱歉此問題不在知識庫，請聯繫FAS人員回答。",
            "category": "out_of_scope",
            "conversation_id": conversation_id,
            "processing_time": round(processing_time, 3)
        } 