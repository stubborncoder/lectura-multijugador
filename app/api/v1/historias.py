from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for Historia
class HistoriaBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    generos: Optional[List[str]] = Field(default_factory=list)
    dificultad: Optional[int] = None
    imagen_portada: Optional[str] = None
    min_jugadores: Optional[int] = 1
    max_jugadores: Optional[int] = None
    estado: str = "borrador"

class HistoriaCreate(HistoriaBase):
    pass

class HistoriaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    generos: Optional[List[str]] = None
    dificultad: Optional[int] = None
    imagen_portada: Optional[str] = None
    min_jugadores: Optional[int] = None
    max_jugadores: Optional[int] = None
    estado: Optional[str] = None

class Historia(HistoriaBase):
    story_id: UUID
    autor_id: Optional[UUID] = None
    fecha_creacion: str
    fecha_modificacion: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/historias",
    tags=["historias"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Historia])
async def get_historias():
    """Obtener todas las historias"""
    response = supabase.table("historias").select("*").execute()
    return response.data

@router.get("/{historia_id}", response_model=Historia)
async def get_historia(historia_id: UUID = Path(..., description="ID de la historia a obtener")):
    """Obtener una historia por su ID"""
    response = supabase.table("historias").select("*").eq("story_id", str(historia_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Historia no encontrada")
    
    return response.data[0]

@router.post("/", response_model=Historia, status_code=201)
async def create_historia(historia: HistoriaCreate = Body(...)):
    """Crear una nueva historia"""
    try:
        response = supabase.table("historias").insert(historia.dict()).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear historia: {str(e)}")

@router.put("/{historia_id}", response_model=Historia)
async def update_historia(
    historia_id: UUID = Path(..., description="ID de la historia a actualizar"),
    historia: HistoriaUpdate = Body(...)
):
    """Actualizar una historia existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in historia.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if historia exists
        check_response = supabase.table("historias").select("*").eq("story_id", str(historia_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Historia no encontrada")
        
        # Update historia
        response = supabase.table("historias").update(update_data).eq("story_id", str(historia_id)).execute()
        return response.data[0]
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Historia no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al actualizar historia: {str(e)}")

@router.delete("/{historia_id}", status_code=204)
async def delete_historia(historia_id: UUID = Path(..., description="ID de la historia a eliminar")):
    """Eliminar una historia"""
    try:
        # Check if historia exists
        check_response = supabase.table("historias").select("*").eq("story_id", str(historia_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Historia no encontrada")
        
        # Delete historia
        supabase.table("historias").delete().eq("story_id", str(historia_id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Historia no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al eliminar historia: {str(e)}")
