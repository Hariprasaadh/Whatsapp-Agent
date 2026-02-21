import os
from typing import List

import aiohttp
from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from settings import settings

RAPIDAPI_TTI_URL = "https://ai-text-to-image-generator-flux-free-api.p.rapidapi.com/aaaaaaaaaaaaaaaaaiimagegenerator/quick.php"
RAPIDAPI_HOST = "ai-text-to-image-generator-flux-free-api.p.rapidapi.com"

SCENARIO_PROMPT = """\
You are a creative assistant that produces vivid image-generation prompts.
Given the recent conversation below, craft a single detailed visual prompt
(style, lighting, subject, mood) that the AI companion would want to share
as an image. Be descriptive and specific – avoid abstract concepts.\
"""


class ScenarioResponse(BaseModel):
    image_prompt: str = Field(
        description=(
            "A detailed, comma-separated description suitable for an image "
            "generation model. Include subject, style, lighting and mood."
        )
    )


class TextToImageError(Exception):
    """Raised when image generation fails."""


class TextToImage:
    """Generate images from text prompts using Pollinations.ai (free, no API key)."""

    async def create_scenario(self, messages: List[AnyMessage]) -> ScenarioResponse:
        model = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.TEXT_MODEL_NAME,
            temperature=0.7,
        ).with_structured_output(ScenarioResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SCENARIO_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | model
        return await chain.ainvoke({"messages": messages})

    async def generate_image(self, image_prompt: str, output_path: str) -> str:
        """Generate an image via RapidAPI Flux and save it to output_path.

        Raises:
            ValueError:       If image_prompt is empty.
            TextToImageError: If the request fails.
        """
        if not image_prompt.strip():
            raise ValueError("image_prompt cannot be empty")

        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": settings.RAPIDAPI_KEY,
        }
        payload = {"prompt": image_prompt, "style_id": 4, "size": "1-1"}

        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: request image generation
                async with session.post(
                    RAPIDAPI_TTI_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        raise TextToImageError(
                            f"RapidAPI returned HTTP {resp.status}: {body[:200]}"
                        )
                    data = await resp.json()

                # Step 2: pick first non-NSFW image URL
                results = data.get("final_result", [])
                if not results:
                    raise TextToImageError("RapidAPI returned no images.")

                image_url = next(
                    (r["origin"] for r in results if not r.get("nsfw", False)),
                    None,
                )
                if not image_url:
                    raise TextToImageError("All returned images were flagged as NSFW.")

                # Step 3: download the webp
                async with session.get(
                    image_url, timeout=aiohttp.ClientTimeout(total=60)
                ) as img_resp:
                    if img_resp.status != 200:
                        raise TextToImageError(
                            f"Failed to download image: HTTP {img_resp.status}"
                        )
                    image_bytes = await img_resp.read()

            if not image_bytes:
                raise TextToImageError("Downloaded image is empty.")

            parent_dir = os.path.dirname(output_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            base = os.path.splitext(output_path)[0]
            output_path = f"{base}.webp"
            with open(output_path, "wb") as fh:
                fh.write(image_bytes)

            return output_path

        except TextToImageError:
            raise
        except Exception as exc:
            raise TextToImageError(f"Image generation failed: {exc}") from exc
