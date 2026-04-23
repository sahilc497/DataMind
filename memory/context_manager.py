from typing import List, Dict, Any

class ContextManager:
    @staticmethod
    def format_history(history: List[Dict[str, Any]]) -> str:
        """
        Formats conversational history for the SQL agent.
        """
        if not history:
            return ""
        
        formatted = "### CONVERSATIONAL CONTEXT ###\n"
        for entry in history[-3:]:  # Last 3 turns for context
            role = "User" if entry.get("role") == "user" else "Assistant"
            content = entry.get("content", "")
            formatted += f"{role}: {content}\n"
        
        return formatted

    @staticmethod
    def extract_relevant_context(history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts last SQL and intent to help modify queries.
        """
        context = {"last_sql": "", "last_query": ""}
        for entry in reversed(history):
            if entry.get("role") == "assistant" and "sql" in entry:
                context["last_sql"] = entry["sql"]
            if entry.get("role") == "user":
                context["last_query"] = entry["content"]
                break
        return context
