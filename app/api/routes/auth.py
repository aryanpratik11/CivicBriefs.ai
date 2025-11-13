from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/test")
def test_auth():
    return {"message": "Auth route working ✅"}
