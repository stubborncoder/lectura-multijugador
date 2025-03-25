from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

# Pydantic model for Personaje
class PersonajeBase(BaseModel):
    nombre: str = Field(..., description="Nombre del personaje que se mostrará a los usuarios")
    descripcion: Optional[str] = Field(None, description="Descripción física y de personalidad del personaje")
    historia_id: UUID = Field(..., description="Identificador de la historia a la que pertenece el personaje")
    partida_id: Optional[UUID] = Field(None, description="Identificador de la partida a la que pertenece el personaje")
    rol: Optional[str] = Field(None, description="Rol del personaje en la historia (protagonista, antagonista, secundario, etc.)")
    habilidades: Optional[List[str]] = Field(None, description="Lista de habilidades especiales que posee el personaje")
    nivel_poder: Optional[int] = Field(None, description="Nivel de poder del personaje (1-10, donde 10 es muy poderoso)")
    imagen_perfil: Optional[str] = Field(None, description="URL o ruta a la imagen que representa visualmente al personaje")
    edad: Optional[int] = Field(None, description="Edad del personaje en años")
    origen: Optional[str] = Field(None, description="Lugar de origen o procedencia del personaje")
    estado: str = Field("activo", description="Estado actual del personaje (activo, inactivo, eliminado, etc.)")

class PersonajeCreate(PersonajeBase):
    pass

class PersonajeUpdate(BaseModel):
    nombre: Optional[str] = Field(None, description="Nombre del personaje que se mostrará a los usuarios")
    descripcion: Optional[str] = Field(None, description="Descripción física y de personalidad del personaje")
    historia_id: Optional[UUID] = Field(None, description="Identificador de la historia a la que pertenece el personaje")
    partida_id: Optional[UUID] = Field(None, description="Identificador de la partida a la que pertenece el personaje")
    rol: Optional[str] = Field(None, description="Rol del personaje en la historia (protagonista, antagonista, secundario, etc.)")
    habilidades: Optional[List[str]] = Field(None, description="Lista de habilidades especiales que posee el personaje")
    nivel_poder: Optional[int] = Field(None, description="Nivel de poder del personaje (1-10, donde 10 es muy poderoso)")
    imagen_perfil: Optional[str] = Field(None, description="URL o ruta a la imagen que representa visualmente al personaje")
    edad: Optional[int] = Field(None, description="Edad del personaje en años")
    origen: Optional[str] = Field(None, description="Lugar de origen o procedencia del personaje")
    estado: Optional[str] = Field(None, description="Estado actual del personaje (activo, inactivo, eliminado, etc.)")

class Personaje(PersonajeBase):
    personaje_id: UUID = Field(..., description="Identificador único del personaje")
    fecha_creacion: datetime
    fecha_modificacion: datetime

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
    response = supabase.table("personajes").select("*").eq("personaje_id", str(personaje_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    return response.data[0]

@router.get("/historia/{historia_id}", response_model=List[Personaje])
async def get_personajes_by_historia(historia_id: UUID = Path(..., description="ID de la historia")):
    """Obtener todos los personajes de una historia específica"""
    response = supabase.table("personajes").select("*").eq("historia_id", str(historia_id)).execute()
    return response.data

@router.get("/partida/{partida_id}", response_model=List[Personaje])
async def get_personajes_by_partida(partida_id: UUID = Path(..., description="ID de la partida")):
    """Obtener todos los personajes de una partida específica"""
    response = supabase.table("personajes").select("*").eq("partida_id", str(partida_id)).execute()
    return response.data

@router.post("/", response_model=Personaje, status_code=201)
async def create_personaje(personaje: PersonajeCreate = Body(...)):
    """Crear un nuevo personaje"""
    try:
        # Check if historia exists
        historia_check = supabase.table("historias").select("story_id").eq("story_id", str(personaje.historia_id)).execute()
        if not historia_check.data:
            raise HTTPException(status_code=404, detail="La historia especificada no existe")
        
        # Check if partida exists if provided
        if personaje.partida_id:
            partida_check = supabase.table("partidas").select("game_id").eq("game_id", str(personaje.partida_id)).execute()
            if not partida_check.data:
                raise HTTPException(status_code=404, detail="La partida especificada no existe")
        
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
        check_response = supabase.table("personajes").select("*").eq("personaje_id", str(personaje_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
        
        # If historia_id is being updated, check if the new historia exists
        if "historia_id" in update_data:
            historia_check = supabase.table("historias").select("story_id").eq("story_id", str(update_data["historia_id"])).execute()
            if not historia_check.data:
                raise HTTPException(status_code=404, detail="La historia especificada no existe")
        
        # If partida_id is being updated, check if the new partida exists
        if "partida_id" in update_data and update_data["partida_id"] is not None:
            partida_check = supabase.table("partidas").select("game_id").eq("game_id", str(update_data["partida_id"])).execute()
            if not partida_check.data:
                raise HTTPException(status_code=404, detail="La partida especificada no existe")
        
        # Update fecha_modificacion
        update_data["fecha_modificacion"] = datetime.now().isoformat()
        
        # Update personaje
        response = supabase.table("personajes").update(update_data).eq("personaje_id", str(personaje_id)).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar personaje: {str(e)}")

@router.delete("/{personaje_id}", status_code=204)
async def delete_personaje(personaje_id: UUID = Path(..., description="ID del personaje a eliminar")):
    """Eliminar un personaje"""
    try:
        # Check if personaje exists
        check_response = supabase.table("personajes").select("*").eq("personaje_id", str(personaje_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
        
        # Delete personaje
        supabase.table("personajes").delete().eq("personaje_id", str(personaje_id)).execute()
        return None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al eliminar personaje: {str(e)}")
