
import base64
import logging
from typing import List, Dict, Any
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Create embeddings for text using configured model."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    embed_model = settings.EMBED_MODEL
    resp = client.embeddings.create(model=embed_model, input=texts)
    logger.debug(f"Embedded {len(texts)} texts using {embed_model}")
    return [d.embedding for d in resp.data]

def embed_image(image_bytes: bytes) -> List[float]:
    """
    Create embeddings for a single image using OpenAI's vision API.
    
    Note: OpenAI doesn't have direct image embeddings, so we use a workaround:
    We generate a descriptive caption and embed that text instead.
    
    Args:
        image_bytes: Raw image data
        
    Returns:
        3072-dimensional embedding vector
    """
    try:
        # Convert image to base64
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Use GPT-4o vision to describe the image
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this educational image/diagram/formula in detail, including all visual elements, labels, symbols, and their relationships. Be comprehensive and precise."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0
        )
        
        # Extract the description
        description = response.choices[0].message.content
        
        # Embed the description
        embedding = embed_texts([description])[0]
        logger.info(f"Generated embedding for image (description length: {len(description)})")
        
        return embedding
        
    except Exception as e:
        logger.error(f"Failed to embed image: {e}")
        raise

def embed_images(image_bytes_list: List[bytes]) -> List[List[float]]:
    """
    Create embeddings for multiple images.
    
    Args:
        image_bytes_list: List of raw image data
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    for i, img_bytes in enumerate(image_bytes_list):
        try:
            emb = embed_image(img_bytes)
            embeddings.append(emb)
            logger.debug(f"Embedded image {i+1}/{len(image_bytes_list)}")
        except Exception as e:
            logger.error(f"Failed to embed image {i+1}: {e}")
            # Append zero vector as fallback (or skip)
            embeddings.append([0.0] * 3072)
    
    return embeddings

def embed_latex_formulas(latex_formulas: List[str]) -> List[List[float]]:
    """
    Embed LaTeX formulas as text.
    
    Args:
        latex_formulas: List of LaTeX strings
        
    Returns:
        List of embedding vectors
    """
    if not latex_formulas:
        return []
    
    # Embed LaTeX formulas as text
    embeddings = embed_texts(latex_formulas)
    logger.info(f"Embedded {len(embeddings)} LaTeX formulas")
    
    return embeddings
