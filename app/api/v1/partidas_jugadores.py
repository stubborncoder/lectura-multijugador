from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for PartidaJugador
class PartidaJugadorBase(BaseModel):
    partida_id: UUID
    jugador_id: UUID
    personaje_id: Optional[UUID] = None
    estado: str = "activo"
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PartidaJugadorCreate(PartidaJugadorBase):
    pass

class PartidaJugadorUpdate(BaseModel):
    personaje_id: Optional[UUID] = None
    estado: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class PartidaJugador(PartidaJugadorBase):
    id: UUID
    fecha_union: str
    ultima_actividad: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/partidas-jugadores",
    tags=["partidas_jugadores"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[PartidaJugador])
async def get_partidas_jugadores():
    """Obtener todas las relaciones partida-jugador"""
    response = supabase.table("partidas_jugadores").select("*").execute()
    return response.data

@router.get("/{id}", response_model=PartidaJugador)
async def get_partida_jugador(id: UUID = Path(..., description="ID de la relación partida-jugador a obtener")):
    """Obtener una relación partida-jugador por su ID"""
    response = supabase.table("partidas_jugadores").select("*").eq("id", str(id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Relación partida-jugador no encontrada")
    
    return response.data[0]

@router.get("/partida/{partida_id}", response_model=List[PartidaJugador])
async def get_jugadores_by_partida(partida_id: UUID = Path(..., description="ID de la partida")):
    """Obtener todos los jugadores de una partida específica"""
    response = supabase.table("partidas_jugadores").select("*").eq("partida_id", str(partida_id)).execute()
    return response.data

@router.get("/jugador/{jugador_id}", response_model=List[PartidaJugador])
async def get_partidas_by_jugador(jugador_id: UUID = Path(..., description="ID del jugador")):
    """Obtener todas las partidas de un jugador específico"""
    response = supabase.table("partidas_jugadores").select("*").eq("jugador_id", str(jugador_id)).execute()
    return response.data

@router.post("/", response_model=PartidaJugador, status_code=201)
async def create_partida_jugador(partida_jugador: PartidaJugadorCreate = Body(...)):
    """Crear una nueva relación partida-jugador"""
    try:
        # Check if partida exists
        partida_check = supabase.table("partidas").select("game_id").eq("game_id", str(partida_jugador.partida_id)).execute()
        if not partida_check.data:
            raise HTTPException(status_code=404, detail="La partida especificada no existe")
        
        # Check if jugador exists
        jugador_check = supabase.table("jugadores").select("player_id").eq("player_id", str(partida_jugador.jugador_id)).execute()
        if not jugador_check.data:
            raise HTTPException(status_code=404, detail="El jugador especificado no existe")
        
        # Check if personaje exists (if provided)
        if partida_jugador.personaje_id:
            personaje_check = supabase.table("personajes").select("character_id").eq("character_id", str(partida_jugador.personaje_id)).execute()
            if not personaje_check.data:
                raise HTTPException(status_code=404, detail="El personaje especificado no existe")
        
        # Check if jugador is already in the partida
        existing_check = supabase.table("partidas_jugadores").select("id").eq("partida_id", str(partida_jugador.partida_id)).eq("jugador_id", str(partida_jugador.jugador_id)).execute()
        if existing_check.data:
            raise HTTPException(status_code=400, detail="El jugador ya está en esta partida")
        
        response = supabase.table("partidas_jugadores").insert(partida_jugador.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear relación partida-jugador: {str(e)}")

@router.put("/{id}", response_model=PartidaJugador)
async def update_partida_jugador(
    id: UUID = Path(..., description="ID de la relación partida-jugador a actualizar"),
    partida_jugador: PartidaJugadorUpdate = Body(...)
):
    """Actualizar una relación partida-jugador existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in partida_jugador.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if partida_jugador exists
        check_response = supabase.table("partidas_jugadores").select("*").eq("id", str(id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Relación partida-jugador no encontrada")
        
        # If updating personaje_id, check if it exists
        if partida_jugador.personaje_id:
            personaje_check = supabase.table("personajes").select("character_id").eq("character_id", str(partida_jugador.personaje_id)).execute()
            if not personaje_check.data:
                raise HTTPException(status_code=404, detail="El personaje especificado no existe")
        
        # Update partida_jugador
        response = supabase.table("partidas_jugadores").update(update_data).eq("id", str(id)).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Relación partida-jugador no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al actualizar relación partida-jugador: {str(e)}")

@router.delete("/{id}", status_code=204)
async def delete_partida_jugador(id: UUID = Path(..., description="ID de la relación partida-jugador a eliminar")):
    """Eliminar una relación partida-jugador"""
    try:
        # Check if partida_jugador exists
        check_response = supabase.table("partidas_jugadores").select("*").eq("id", str(id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Relación partida-jugador no encontrada")
        
        # Delete partida_jugador
        supabase.table("partidas_jugadores").delete().eq("id", str(id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Relación partida-jugador no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al eliminar relación partida-jugador: {str(e)}")
