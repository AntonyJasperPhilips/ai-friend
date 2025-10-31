
import boto3, uuid
from app.core.config import settings

_s3 = None
def s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    return _s3

def key_for_image(book_id:int, chapter_id:int, unit_id:int, ext:str="png") -> str:
    image_id = str(uuid.uuid4())
    key = f"books/{book_id}/chapters/{chapter_id}/units/{unit_id}/images/{image_id}.{ext}"
    return key, image_id

def upload_bytes_get_uri(data:bytes, mimetype:str, book_id:int, chapter_id:int, unit_id:int):
    key, image_id = key_for_image(book_id, chapter_id, unit_id, "png" if mimetype.endswith("png") else "jpg")
    s3().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=mimetype)
    uri = f"s3://{settings.S3_BUCKET}/{key}"
    return uri, image_id, key

def presign_get(key:str, expiry:int=600) -> str:
    return s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expiry
    )
