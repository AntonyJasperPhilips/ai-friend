
import boto3, uuid
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def s3():
    # Validate AWS configuration
    if not settings.AWS_REGION:
        raise ValueError("AWS_REGION not configured in .env file")
    if not settings.AWS_ACCESS_KEY_ID:
        raise ValueError("AWS_ACCESS_KEY_ID not configured in .env file")
    if not settings.AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS_SECRET_ACCESS_KEY not configured in .env file")
    if not settings.S3_BUCKET:
        raise ValueError("S3_BUCKET not configured in .env file")
    
    try:
        return boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        raise ValueError(f"Invalid S3 configuration: {e}") from e

def key_for_image(book_id:str, chapter_id:str, unit_id:str, ext:str="png") -> tuple[str, str]:
    image_id = str(uuid.uuid4())
    key = f"content-management-books/{book_id}/{chapter_id}/{unit_id}/images/{image_id}.{ext}"
    return key, image_id

def upload_image_bytes(data:bytes, mimetype:str, book_id:str, chapter_id:str, unit_id:str):
    key, image_id = key_for_image(book_id, chapter_id, unit_id, "png" if mimetype.endswith("png") else "jpg")
    s3().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=mimetype)
    return f"s3://{settings.S3_BUCKET}/{key}", image_id, key

def presign_get(key:str, expiry:int=600) -> str:
    return s3().generate_presigned_url("get_object", Params={"Bucket": settings.S3_BUCKET, "Key": key}, ExpiresIn=expiry)

def fetch_image_from_s3(s3_uri: str) -> bytes:
    """
    Fetch image bytes from S3 using s3:// URI.
    
    Args:
        s3_uri: S3 URI in format s3://bucket/key
        
    Returns:
        Image bytes
    """
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3_uri}")
    
    # Parse bucket and key from s3:// URI
    parts = s3_uri.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    key = parts[1]
    
    # Fetch from S3
    response = s3().get_object(Bucket=bucket, Key=key)
    return response['Body'].read()