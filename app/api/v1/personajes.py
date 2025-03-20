from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for Personaje
class PersonajeBase(BaseModel):
    historia_id: UUID
    nombre: str
    descripcion: Optional[str] = None
    imagen: Optional[str] = None
    atributos: Optional[Dict[str, Any]] = Field(default_factory=dict)
    estado: str = "activo"

class PersonajeCreate(PersonajeBase):
    pass

class PersonajeUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    imagen: Optional[str] = None
    atributos: Optional[Dict[str, Any]] = None
    estado: Optional[str] = None

class Personaje(PersonajeBase):
    character_id: UUID
    fecha_creacion: str
    fecha_modificacion: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/personajes",
    tags=["personajes"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Personaje])
async def get_personajes():
    """Obtener todos los personajes"""
    response = supabase.table("personajes").select("*").execute()
    return response.data

@router.get("/{personaje_id}", response_model=Personaje)
async def get_personaje(personaje_id: UUID = Path(..., description="ID del personaje a obtener")):
    """Obtener un personaje por su ID"""
    response = supabase.table("personajes").select("*").eq("character_id", str(personaje_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    return response.data[0]

@router.get("/historia/{historia_id}", response_model=List[Personaje])
async def get_personajes_by_historia(historia_id: UUID = Path(..., description="ID de la historia")):
    """Obtener todos los personajes de una historia específica"""
    response = supabase.table("personajes").select("*").eq("historia_id", str(historia_id)).execute()
    return response.data

@router.post("/", response_model=Personaje, status_code=201)
async def create_personaje(personaje: PersonajeCreate = Body(...)):
    """Crear un nuevo personaje"""
    try:
        # Check if historia exists
        historia_check = supabase.table("historias").select("story_id").eq("story_id", str(personaje.historia_id)).execute()
        if not historia_check.data:
            raise HTTPException(status_code=404, detail="La historia especificada no existe")
        
        response = supabase.table("personajes").insert(personaje.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear personaje: {str(e)}")

@router.put("/{personaje_id}", response_model=Personaje)
async def update_personaje(
    personaje_id: UUID = Path(..., description="ID del personaje a actualizar"),
    personaje: PersonajeUpdate = Body(...)
):
    """Actualizar un personaje existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in personaje.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if personaje exists
        check_response = supabase.table("personajes").select("*").eq("character_id", str(personaje_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
        
        # Update personaje
        response = supabase.table("personajes").update(update_data).eq("character_id", str(personaje_id)).execute()
        return response.data[0]
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al actualizar personaje: {str(e)}")

@router.delete("/{personaje_id}", status_code=204)
async def delete_personaje(personaje_id: UUID = Path(..., description="ID del personaje a eliminar")):
    """Eliminar un personaje"""
    try:
        # Check if personaje exists
        check_response = supabase.table("personajes").select("*").eq("character_id", str(personaje_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
        
        # Delete personaje
        supabase.table("personajes").delete().eq("character_id", str(personaje_id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al eliminar personaje: {str(e)}")
