from typing import TypedDict, List, Dict, Literal, Any, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import re
import json
from datetime import datetime
import os
import ast 
from ast import operator
import math

class ToolLogger:
    """Logs tool usage with automatic persistence"""

    # Create log directory, log list, and  log file
    def __init__(self, 
                 logs_dir:str = "./logs", 
                 session_id:str = None):
        """Create a log directory, log list and log file"""
        self.logs=[]
        self.logs_dir = logs_dir
        self.session_id = session_id

        os.makedirs(logs_dir, exist_ok=True)

        if session_id:
            self.log_file = os.path.join(logs_dir, f"_session_{session_id}.json")
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_file = os.path.join(logs_dir, f"tool_usage_{timestamp}.json")

    # Populate the log list with time, tool name, input, and output
    def log_tool_use(self, 
                     tool_name:str, 
                     input_data: Dict[str, Any], 
                     output:Any):
        """Populate the log list with time, tool, input and output. 
        Save it automatically for persistence."""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "input": input_data,
            "output": str(output)
        }

        self.logs.append(log_entry)
        self.auto_save()
        return log_entry
    
    # Helper function to save the log list persistently to the log directory.
    def auto_save(self):
        """Helper function to save the log list persistently to the log directory."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            print("Warning failed to auto-save Logs: {e}")

    # Get Logs
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get the logs"""
        return self.logs

def create_calculator_tool(logger: ToolLogger):
    """
    Creates a calculator tool
    """
    ops = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

    def eval_node(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return ops[type(node.op)](eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](eval_node(node.operand))
        else:
            raise ValueError("Unsupported expression")

    @tool
    def calculator_tool(expression:str): 
        """
        This is a calculator tool. It takes mathematical expression as input. It validates the expression and allows only basic mathematical operations like addition, subtraction, multiplication, division, logarithmic computation.
        Args:
            input: Mathematical expression (e.g., "30% of total Profit")
            query_type: Type of operation - 'Addition', 'Subtraction', 'Multiplication', 'Division'
        Returns: 
            Formatted result string 
        """
        tree = ast.parse(expression, mode="eval")
        result = eval_node(tree.body)
        logger.log_tool_use(
            "calculator_tool",
            {"expression":expression},
            {"result": result}
        )
        return result
    
    
def create_document_search_tool(retriever,logger:ToolLogger):
    """
    Creates a document search tool.
    """

    @tool
    def document_search(
        query: str,
        search_type: Literal["keyword", "type", "amount", "amount_range", "all"] = "keyword",
        doc_type: Optional[str] = None,
        min_amount: Optional[float]= None,
        max_amount : Optional[float] = None,
        comparison: Optional[Literal["over","under","between","exact","approximate"]] = None,
        amount: Optional[float] = None
    )-> str:
        """
        Search for relevant documents using various criteria. Handles natural language amount queries.

        Args:
            query: Search query (e.g., "invoices over $50,000, "contracts", "insurance claims")
            search_type: Type of search - 'keyword', 'type', 'amount', 'amount_range' or 'all'
            doc_type: Document type filter (e.g., 'invoice', 'contract', 'claim')
            min_amount: Minimum amount (for range queries or "over" queries)
                max_amount: Maximum amount (for range queries or "under" queries)
                comparison: Type of amount comparison - 'over', 'under', 'between', 'exact', 'approximate'
                amount: Single amount value for comparisons (used with 'over', 'under', 'exact', 'approximate')

            Examples:
                - "Find documents over $50,000" → comparison='over', amount=50000
                - "Show invoices under $10,000" → search_type='type', doc_type='invoice', comparison='under', amount=10000
                - "Documents between $20,000 and $80,000" → min_amount=20000, max_amount=80000
                - "Contracts around $100,000" → comparison='approximate', amount=100000

            Returns:
                Formatted search results with document details
        """
        try:
            results = []

            if search_type == "all":
                results = retriever.retrieve_all()

            if search_type == "keyword":
                results = retriever.retrieve_by_keyword(query)

            elif search_type == "type" and doc_type:
                results = retriever.retreieve_by_topic(doc_type)
                if comparison or min_amount is not None or max_amount is not None:
                    amount_results = _handle_amount_search(
                        retriever, comparison, amount, min_amount, max_amount, query
                    )
                    result_ids = {r.doc_id for r in amount_results}
                    results = [ r for r in results if r.doc_id in result_ids]
            
            else:
                query_lower = query.lower()

                if any(word in query_lower for word in ['over', 'under', 'above', 'below', 'between', 'around', 'exactly', '$']):
                    results = retriever._parse_and_retrieve_by_amount(query)

                elif any(word in query_lower for word in ['invoice', 'contract', 'claim']):
                    for doc_type in ['invoice', 'contract', 'claim']:
                        if doc_type in query_lower:
                            results = retriever.retrieve_by_type(doc_type)
                            break

                else:
                    results = retriever.retrieve_by_keyword(query)
            
            if not results:
                formatted = "No documents found matching your search criteria"
            else:
                formatted = f"Found {len(results)} documents:\n\n"
                for i, chunk in enumerate(results,1):
                    formatted+= f"Document {i} (ID: {chunk.doc_id})\n"
                    formatted += f"Title: {chunk.metadata.get('title', 'Unknown')}\n"
                    formatted += f"Type: {chunk.metadata.get('doc_type', 'Unknown')}\n"

                    amount_value = None
                    for field in ["total", "amount", "value"]:
                        if field in chunk.metadata:
                            amount_value = chunk.metadata[field]
                            formatted += f"Amount: ${amount_value:,.2f}\n"
                            break
                    
                    if hasattr(chunk, 'relevance_score'):
                        formatted += f"Relevance Score: {chunk.relevance_score:.2f}\n"
                    fromatted += f"Preview: {chunk.content[:200]}...\n"
                    formatted += "-" * 50 + "\n"

            logger.log_tool_use(
                "document_search",
                {
                    "query": query,
                    "search_type": search_type,
                    "doc_type": doc_type,
                    "min_amount": min_amount,
                    "max_amount": max_amount,
                    "comparison": comparison,
                    "amount": amount
                },
                {
                    "results_count": len(results)
                }
            )
            return formatted
        
        except Exception as e:
            error_msg = f"Error searching documents: {str(e)}"
            logger.log_tool_use(
                "document_search",
                {"query": query,
                 "search_type": search_type},
                {"error": error_msg}
            )
            return error_msg


    def _handle_amount_search(
            retriever,
            comparison,
            amount,
            min_amount,
            max_amount,
            query
    ):
        """Helper function to handle amount based searches"""

        if comparison:
            if comparison == "over" and amount is not None:
                return retriever.retrieve_by_amount_range(min_amount=amount)
            elif comparison == "under" and amount is not None:
                return retriever.retrieve_by_amount_range(max_amount=amount)
            elif comparison == "exact" and amount is not None:
                return retriever.retrieve_by_exact_amount(amount)
            elif comparison == "approximate" and amount is not None:
                return retriever.retrieve_by_approximate_amount(amount)
            elif comparison == "between" and min_amount is not None and max_amount is not None:
                return retriever.retrieve_by_amount_range(min_amount= min_amount, max_amount=max_amount)
            
        if min_amount is not None or max_amount is not None:
            return retriever.retrieve_by_amount_range(min_amount=min_amount, max_amount=max_amount)
        return retriever._parse_and_retrieve_by_amount(query)
    
    document_search._handle_amount_search = _handle_amount_search
    return document_search

def create_document_reader_tool(retriever, logger:ToolLogger):
    """Creates a tool to read a full document content"""   

    @tool
    def document_reader(doc_id:str)-> str:
        """
        Read the full content of a document by its document id.
        Args:
            doc_id: The exact document ID to read(e.g., 'INV-001', 'CON-001')
        Returns:
            The full content of the document or an error message if not found. 
        """         
        try:
            doc = retriever.get_document_by_id(doc_id)
            if doc: 
                amount_info = ""
                for field in ['total','amount','value']:
                    if field in doc.metadata:
                        amount_info = f"\nAmount: ${doc.metadata[field]:,.2f}"
                        break
                result = f"Document {doc_id}:{amount_info}\n\n{doc.content}"
                logger.log_tool_use(
                    "document_reader",
                    {"doc_id": doc_id}
                    ,{"found": True, "doc_type":doc.metadata.get('doc_type')}
                )
                return result
            else:
                logger.log_tool_use(
                    "document_reader",
                    {"doc_id": doc_id},
                    {"found":False}
                )
                return f"Document with ID {doc_id} not found"
        except Exception as e:
            error_msg = f"Error reading document: {str(e)}"
            logger.log_tool_use(
                "document_reader",
                {"doc_id": doc_id},
                {"error": error_msg}
            )
            return error_msg
    return document_reader

def create_document_statistics(retriever, logger:ToolLogger):
    """Creates a tool to get statistics about the document collection"""
    @tool
    def document_statistics()->str:
        """ Get statistics about all the documents in the system.
        Returns:
            Summary statistics including document counts, amount totals, and averages.
        """
        try:
            stats = retriever.get_statistics()
            formatted  = "DOCUMENT COLLECTION STATISTICS\n\n"
            formatted+= f"Total Documents: {stats['total_documents']}\n"
            formatted+= f"Documents with Amounts: {stats['documents_with_amounts']}\n"
            formatted+= f"\nDocument Types: \n"

            for doc_type, count in stats['document_types'].items():
                formatted+= f" - {doc_type.capitalize()}: {count}\n"

            if stats['documents_with_amounts']>0:
                formatted+= f"\nFinancial Summary:\n"
                formatted += f" - Total Amount: ${stats['total_amount']:,.2f}\n"
                formatted += f"  - Average Amount: ${stats['average_amount']:,.2f}\n"
                formatted += f"  - Minimum Amount: ${stats['min_amount']:,.2f}\n"
                formatted += f"  - Maximum Amount: ${stats['max_amount']:,.2f}\n"
            
            logger.log_tool_use(
                "document_statistics",
                {},
                {"stats":stats}
            )

            return formatted
        
        except Exception as e:
            error_msg = str(e)
            logger.log_tool_use(
                "document_statistics",
                {},
                {"error": error_msg}
            )
            return error_msg
    return document_statistics

def get_all_tools(retriever, logger:ToolLogger)-> List:
    """Get all available tools for the agent"""
    return[
        create_calculator_tool(logger),
        create_document_search_tool(retriever,logger),
        create_document_reader_tool(retriever, logger),
        create_document_statistics(retriever, logger)
    ]

















































