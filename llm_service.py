import ollama


def get_llm_response(user_message: str, model: str = "llama3"):
    """
    Usa Ollama con chat API.
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": user_message}],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"
