from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for Partida
class PartidaBase(BaseModel):
    historia_id: UUID
    estado: str = "en_curso"
    decisiones: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PartidaCreate(PartidaBase):
    pass

class PartidaUpdate(BaseModel):
    estado: Optional[str] = None
    decisiones: Optional[Dict[str, Any]] = None

class Partida(PartidaBase):
    game_id: UUID
    fecha_creacion: str
    ultima_actividad: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/partidas",
    tags=["partidas"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Partida])
async def get_partidas():
    """Obtener todas las partidas"""
    response = supabase.table("partidas").select("*").execute()
    return response.data

@router.get("/{partida_id}", response_model=Partida)
async def get_partida(partida_id: UUID = Path(..., description="ID de la partida a obtener")):
    """Obtener una partida por su ID"""
    response = supabase.table("partidas").select("*").eq("game_id", str(partida_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    return response.data[0]

@router.post("/", response_model=Partida, status_code=201)
async def create_partida(partida: PartidaCreate = Body(...)):
    """Crear una nueva partida"""
    try:
        # Check if historia exists
        historia_check = supabase.table("historias").select("story_id").eq("story_id", str(partida.historia_id)).execute()
        if not historia_check.data:
            raise HTTPException(status_code=404, detail="La historia especificada no existe")
        
        response = supabase.table("partidas").insert(partida.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear partida: {str(e)}")

@router.put("/{partida_id}", response_model=Partida)
async def update_partida(
    partida_id: UUID = Path(..., description="ID de la partida a actualizar"),
    partida: PartidaUpdate = Body(...)
):
    """Actualizar una partida existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in partida.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if partida exists
        check_response = supabase.table("partidas").select("*").eq("game_id", str(partida_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        
        # Update partida
        response = supabase.table("partidas").update(update_data).eq("game_id", str(partida_id)).execute()
        return response.data[0]
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al actualizar partida: {str(e)}")

@router.delete("/{partida_id}", status_code=204)
async def delete_partida(partida_id: UUID = Path(..., description="ID de la partida a eliminar")):
    """Eliminar una partida"""
    try:
        # Check if partida exists
        check_response = supabase.table("partidas").select("*").eq("game_id", str(partida_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        
        # Delete partida
        supabase.table("partidas").delete().eq("game_id", str(partida_id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al eliminar partida: {str(e)}")
