import logging
import httpx


class LLMClient:
    """Manages communication with the LLM provider."""

    def __init__(self, api_key: str) -> None:
        self.api_key: str = api_key

    def get_response(self, messages: list[dict[str, str]]) -> str:
        """Get a response from the LLM.
        Args:
            messages: A list of message dictionaries.
        Returns:
            The LLM's response as a string.
        Raises:
            httpx.RequestError: If the request to the LLM fails.
        """
        url = "https://api.together.xyz/v1/chat/completions"
        # url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            # "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
            # "model": "qwen-qwq-32b"
            "model": "Qwen/Qwen3-235B-A22B-fp8-tput",
            "messages": messages,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                total, prompt, completion = data["usage"]["total_tokens"], data["usage"]["prompt_tokens"], data["usage"]["completion_tokens"]
                print(f"Total Tokens: {total}, Prompt Tokens: {prompt}, Completion Tokens: {completion}")
                return data["choices"][0]["message"]["content"]

        except httpx.RequestError as e:
            error_message = f"Error getting LLM response: {str(e)}"
            logging.error(error_message)

            if isinstance(e, httpx.HTTPStatusError):
                status_code = e.response.status_code
                logging.error(f"Status code: {status_code}")
                logging.error(f"Response details: {e.response.text}")

            return (
                f"I encountered an error: {error_message}. "
                "Please try again or rephrase your request."
            )
        
    def get_summary(self, messages: list[dict[str, str]]) -> str:
        """Get a response from the LLM.
        Args:
            messages: A list of message dictionaries.
        Returns:
            The LLM's response as a string.
        Raises:
            httpx.RequestError: If the request to the LLM fails.
        """
        url = "https://api.together.xyz/v1/chat/completions"
        # url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "messages": messages,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                total, prompt, completion = data["usage"]["total_tokens"], data["usage"]["prompt_tokens"], data["usage"]["completion_tokens"]
                print(f"Total Tokens: {total}, Prompt Tokens: {prompt}, Completion Tokens: {completion}")
                return data["choices"][0]["message"]["content"]

        except httpx.RequestError as e:
            error_message = f"Error getting LLM response: {str(e)}"
            logging.error(error_message)

            if isinstance(e, httpx.HTTPStatusError):
                status_code = e.response.status_code
                logging.error(f"Status code: {status_code}")
                logging.error(f"Response details: {e.response.text}")

            return (
                f"I encountered an error: {error_message}. "
                "Please try again or rephrase your request."
            )