from fastapi import APIRouter, Depends
from .auth_controller import get_current_user  # Ajusta el import según tu estructura

router = APIRouter()

@router.get("/test-protegido")
def test_protegido(user=Depends(get_current_user)):
    return {"msg": "Acceso permitido solo a autenticados", "user": user}