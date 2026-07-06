import aiohttp
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

# Initialize the GenAI client (using the API key from config)
client = genai.Client(api_key=GEMINI_API_KEY)

async def generate_thumbnail(prompt: str, style_prompt: str, headshot_url: str) -> bytes:
    full_prompt = (
        f"{style_prompt}\n\n"
        f"User request: {prompt}"
    )

    # 1. Fetch the image bytes asynchronously
    async with aiohttp.ClientSession() as session:
        async with session.get(headshot_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch headshot from URL. Status: {response.status}")
            image_bytes = await response.read()
            # Detect MIME type from headers (default to image/png if not present)
            content_type = response.headers.get("Content-Type", "image/png")

    # 2. Build the contents list with prompt and the image bytes part
    contents = [
        full_prompt,
        types.Part.from_bytes(
            data=image_bytes,
            mime_type=content_type
        )
    ]

    # 3. Call the model using 'contents' (not 'input')
    response = client.models.generate_content(
        model="gemini-3.1-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        )
    )

    # 4. Extract and return the generated image bytes
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data:
                return part.inline_data.data

    raise Exception("No image was returned by the GenAI model.")