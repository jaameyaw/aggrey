from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/webhooks")


@router.post("/sendblue", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def sendblue_webhook() -> None:
    """Placeholder until roadmap M7 adds signature checks. It reads no request body."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
