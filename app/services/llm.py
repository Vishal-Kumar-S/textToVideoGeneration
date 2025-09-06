import json
import logging
import re
import requests
from typing import List

import g4f
from loguru import logger
from openai import AzureOpenAI, OpenAI
from openai.types.chat import ChatCompletion

from app.config import config

# Maximum number of retries for API calls
_max_retries = 5


def _generate_response(prompt: str) -> str:
    """
    Generates a response from the configured LLM provider.
    This function routes the request to the appropriate provider based on the config file.
    """
    try:
        content = ""
        llm_provider = config.app.get("llm_provider", "openai")
        logger.info(f"llm provider: {llm_provider}")

        if llm_provider == "g4f":
            model_name = config.app.get("g4f_model_name", "gpt-3.5-turbo-16k-0613")
            content = g4f.ChatCompletion.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
        else:
            api_version = ""  # for azure
            if llm_provider == "moonshot":
                api_key = config.app.get("moonshot_api_key")
                model_name = config.app.get("moonshot_model_name")
                base_url = "https://api.moonshot.cn/v1"
            elif llm_provider == "ollama":
                api_key = "ollama"  # any string works but is required
                model_name = config.app.get("ollama_model_name")
                base_url = config.app.get("ollama_base_url", "http://localhost:11434/v1")
            elif llm_provider == "openai":
                api_key = config.app.get("openai_api_key")
                model_name = config.app.get("openai_model_name")
                base_url = config.app.get("openai_base_url", "https://api.openai.com/v1")
            elif llm_provider == "oneapi":
                api_key = config.app.get("oneapi_api_key")
                model_name = config.app.get("oneapi_model_name")
                base_url = config.app.get("oneapi_base_url", "")
            elif llm_provider == "azure":
                api_key = config.app.get("azure_api_key")
                model_name = config.app.get("azure_model_name")
                base_url = config.app.get("azure_base_url", "")
                api_version = config.app.get("azure_api_version", "2024-02-15-preview")
            elif llm_provider == "gemini":
                api_key = config.app.get("gemini_api_key")
                model_name = config.app.get("gemini_model_name")
                base_url = "***"  # Not used directly here, handled below
            elif llm_provider == "qwen":
                api_key = config.app.get("qwen_api_key")
                model_name = config.app.get("qwen_model_name")
                base_url = "***"  # Not used directly here, handled below
            elif llm_provider == "cloudflare":
                api_key = config.app.get("cloudflare_api_key")
                model_name = config.app.get("cloudflare_model_name")
                account_id = config.app.get("cloudflare_account_id")
                base_url = "***"  # Not used directly here, handled below
            elif llm_provider == "deepseek":
                api_key = config.app.get("deepseek_api_key")
                model_name = config.app.get("deepseek_model_name")
                base_url = config.app.get("deepseek_base_url", "https://api.deepseek.com")
            elif llm_provider == "ernie":
                api_key = config.app.get("ernie_api_key")
                secret_key = config.app.get("ernie_secret_key")
                base_url = config.app.get("ernie_base_url")
                model_name = "***"  # Not used directly here, handled below
                if not secret_key:
                    raise ValueError(f"{llm_provider}: secret_key is not set in config.")
            elif llm_provider == "pollinations":
                try:
                    base_url = config.app.get("pollinations_base_url", "https://text.pollinations.ai/openai")
                    model_name = config.app.get("pollinations_model_name", "openai-fast")

                    payload = {
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "seed": 101
                    }

                    if config.app.get("pollinations_private"):
                        payload["private"] = True
                    if config.app.get("pollinations_referrer"):
                        payload["referrer"] = config.app.get("pollinations_referrer")

                    headers = {"Content-Type": "application/json"}

                    response = requests.post(base_url, headers=headers, json=payload)
                    response.raise_for_status()
                    result = response.json()

                    if result and "choices" in result and result["choices"]:
                        content = result["choices"][0]["message"]["content"]
                        return content.replace("\n", "")
                    else:
                        raise Exception(f"[{llm_provider}] returned an invalid response format")

                except requests.exceptions.RequestException as e:
                    raise Exception(f"[{llm_provider}] request failed: {str(e)}")
                except Exception as e:
                    raise Exception(f"[{llm_provider}] error: {str(e)}")

            # Validate required fields for most providers
            if llm_provider not in ["pollinations", "ollama"]:
                if not api_key:
                    raise ValueError(f"{llm_provider}: api_key is not set in config.")
                if not model_name:
                    raise ValueError(f"{llm_provider}: model_name is not set in config.")
                if not base_url:
                    raise ValueError(f"{llm_provider}: base_url is not set in config.")

            # Handle providers with special SDKs or request formats
            if llm_provider == "qwen":
                import dashscope
                from dashscope.api_entities.dashscope_response import GenerationResponse

                dashscope.api_key = api_key
                response = dashscope.Generation.call(
                    model=model_name, messages=[{"role": "user", "content": prompt}]
                )
                if response:
                    if isinstance(response, GenerationResponse):
                        if response.status_code != 200:
                            raise Exception(f'[{llm_provider}] returned an error: "{response}"')
                        content = response["output"]["text"]
                        return content.replace("\n", "")
                    else:
                        raise Exception(f'[{llm_provider}] returned an invalid response: "{response}"')
                else:
                    raise Exception(f"[{llm_provider}] returned an empty response")

            if llm_provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=api_key, transport="rest")
                generation_config = {"temperature": 0.5, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                ]
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                )
                try:
                    response = model.generate_content(prompt)
                    return response.candidates[0].content.parts[0].text
                except (AttributeError, IndexError) as e:
                    logger.error(f"Gemini Error: {e}")
                    return f"Error: Failed to process Gemini response. Details: {e}"

            if llm_provider == "cloudflare":
                response = requests.post(
                    f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"messages": [{"role": "user", "content": prompt}]},
                )
                result = response.json()
                logger.info(result)
                return result["result"]["response"]

            if llm_provider == "ernie":
                token_response = requests.post(
                    "https://aip.baidubce.com/oauth/2.0/token",
                    params={"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key}
                )
                access_token = token_response.json().get("access_token")
                url = f"{base_url}?access_token={access_token}"
                payload = json.dumps({"messages": [{"role": "user", "content": prompt}]})
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, headers=headers, data=payload).json()
                return response.get("result")

            # Default handling for OpenAI-compatible APIs
            if llm_provider == "azure":
                client = AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=base_url)
            else:
                client = OpenAI(api_key=api_key, base_url=base_url)

            response = client.chat.completions.create(
                model=model_name, messages=[{"role": "user", "content": prompt}]
            )
            if response and isinstance(response, ChatCompletion):
                content = response.choices[0].message.content
            else:
                raise Exception(f"[{llm_provider}] returned an invalid or empty response.")

        return content.replace("\n", "")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Error: {str(e)}"


def generate_script(video_subject: str, language: str = "", paragraph_number: int = 1) -> str:
    """
    Generates a video script based on a subject.
    """
    prompt = f"""
# Role: Video Script Generator
## Goals:
Generate a script for a video, depending on the subject of the video.
## Constraints:
1. The script is to be returned as a string with the specified number of paragraphs.
2. Do not under any circumstance reference this prompt in your response.
3. Get straight to the point; don't start with unnecessary things like, "welcome to this video".
4. You must not include any type of markdown or formatting in the script; never use a title.
5. Only return the raw content of the script.
6. Do not include "voiceover", "narrator" or similar indicators of what should be spoken.
7. You must not mention the prompt or anything about the script itself.
8. Respond in the same language as the video subject.
# Initialization:
- video subject: {video_subject}
- number of paragraphs: {paragraph_number}
""".strip()
    if language:
        prompt += f"\n- language: {language}"

    final_script = ""
    logger.info(f"Generating script for subject: {video_subject}")

    def format_response(response):
        # Clean the script by removing markdown and unwanted characters
        response = response.replace("*", "").replace("#", "")
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)
        return "\n\n".join(response.split("\n\n"))

    for i in range(_max_retries):
        try:
            response = _generate_response(prompt=prompt)
            if response and "Error: " not in response:
                final_script = format_response(response)
                break  # Exit loop on success
            else:
                logger.error(f"LLM returned an error or empty response: {response}")
        except Exception as e:
            logger.error(f"Failed to generate script on attempt {i + 1}: {e}")

        if i < _max_retries - 1:
            logger.warning(f"Retrying script generation... ({i + 2}/{_max_retries})")

    if not final_script or "Error: " in final_script:
        logger.error(f"Failed to generate video script after all retries.")
    else:
        logger.success(f"Script generated successfully:\n{final_script}")

    return final_script.strip()


def generate_terms(video_subject: str, video_script: str, amount: int = 5) -> List[str]:
    """
    Generates a list of search terms for stock videos based on the script.
    """
    prompt = f"""
# Role: Video Search Terms Generator
## Goals:
Generate {amount} search terms for stock videos, based on the video's subject and script.
## Constraints:
1. The search terms are to be returned as a JSON array of strings.
2. Each search term should consist of 1-3 words.
3. You must only return the JSON array of strings. Do not return anything else.
4. The search terms must be related to the subject of the video.
5. Reply with English search terms only.
## Output Example:
["search term 1", "search term 2", "search term 3", "search term 4", "search term 5"]
## Context:
### Video Subject
{video_subject}
### Video Script
{video_script}
""".strip()

    logger.info(f"Generating search terms for subject: {video_subject}")
    search_terms = []

    for i in range(_max_retries):
        response = _generate_response(prompt)
        if "Error: " in response:
            logger.error(f"LLM returned an error while generating terms: {response}")
            return [response] # Return error to be displayed in UI

        try:
            # Attempt to parse the entire response as JSON
            search_terms = json.loads(response)
            if isinstance(search_terms, list) and all(isinstance(term, str) for term in search_terms):
                break # Success
        except json.JSONDecodeError:
            # If parsing fails, try to find a JSON array within the response string
            logger.warning("Response was not a clean JSON array, attempting to extract it.")
            match = re.search(r'\[\s*".*?"\s*(,\s*".*?"\s*)*\]', response)
            if match:
                try:
                    search_terms = json.loads(match.group())
                    break # Success
                except json.JSONDecodeError:
                    logger.warning("Could not parse extracted JSON array.")
            else:
                logger.warning("No JSON array found in the response.")

        if i < _max_retries - 1:
            logger.warning(f"Retrying term generation... ({i + 2}/{_max_retries})")

    if not search_terms:
        logger.error("Failed to generate video terms after all retries.")
    else:
        logger.success(f"Search terms generated successfully: {search_terms}")

    return search_terms


if __name__ == "__main__":
    # Example usage for testing the functions directly
    video_subject = "The meaning of life"
    script = generate_script(video_subject=video_subject, language="en-US", paragraph_number=1)
    print("######################")
    print(f"Generated Script:\n{script}")

    if script and "Error: " not in script:
        search_terms = generate_terms(video_subject=video_subject, video_script=script, amount=5)
        print("######################")
        print(f"Generated Search Terms:\n{search_terms}")