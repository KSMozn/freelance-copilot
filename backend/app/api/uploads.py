from fastapi import HTTPException, UploadFile, status


async def read_upload_limited(
    file: UploadFile,
    *,
    max_bytes: int,
    detail: str,
) -> bytes:
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=detail,
        )
    return content
