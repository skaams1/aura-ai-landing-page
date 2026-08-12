import requests
from config import Config

class LLMService:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"

    def generate_response(self, question, context=""):
        """Generate a response using Groq API with RAG context"""

        # Build the user message with context
        if context:
            user_message = f"""Based on the following NCERT Chemistry content:

{context}

---

**Student Question:** {question}

Please provide a comprehensive JEE-focused answer."""
        else:
            user_message = f"""**Student Question:** {question}

Please provide a comprehensive JEE-focused answer based on NCERT Chemistry syllabus."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": Config.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            result = response.json()

            if "choices" in result:
                return {
                    "success": True,
                    "response": result["choices"][0]["message"]["content"]
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error: {result}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_llm_service = None

def get_llm_service():
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
