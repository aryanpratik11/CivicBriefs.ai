import os
import logging
import requests

logger = logging.getLogger(__name__)

LOCAL_LLM_ENDPOINT = os.getenv(
    "LOCAL_LLM_ENDPOINT",
    "http://localhost:8000/v1/chat/completions"
)

DEFAULT_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 512))
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))


def local_llama_call(
    prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    endpoint: str = LOCAL_LLM_ENDPOINT,
    timeout: int = 300
) -> str:
    """
    Call local Llama server (llama-cpp-python OpenAI-compatible server)
    and safely return output text.
    """

    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    try:
        logger.debug(f"Calling LLM endpoint={endpoint}")
        resp = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=timeout
        )

        if resp.status_code != 200:
            logger.error(f"LLM error {resp.status_code}: {resp.text[:500]}")
            return ""

        data = resp.json()

        if "choices" in data and len(data["choices"]) > 0:
            msg = data["choices"][0].get("message", {})
            content = msg.get("content", "").strip()
            logger.info(f"LLM output len={len(content)}")
            return content

        logger.warning(f"Unexpected LLM response: {data}")
        return ""

    except requests.exceptions.Timeout:
        logger.error(f"LLM request timed out after {timeout}s")
        return ""

    except Exception as e:
        logger.exception(f"LLM call failed: {e}")
        return ""


def call_llm_and_get_text(
    llm_unused,
    prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE
):
    """Compatibility wrapper (older code passes llm as first arg)."""
    return local_llama_call(prompt, max_tokens, temperature)
