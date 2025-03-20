from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr

# Pydantic model for Jugador
class JugadorBase(BaseModel):
    nickname: str
    nombre_real: Optional[str] = None
    email: str
    estado: str = "activo"
    games_played: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class JugadorCreate(JugadorBase):
    pass

class JugadorUpdate(BaseModel):
    nickname: Optional[str] = None
    nombre_real: Optional[str] = None
    email: Optional[str] = None
    estado: Optional[str] = None
    games_played: Optional[List[Dict[str, Any]]] = None

class Jugador(JugadorBase):
    player_id: UUID
    fecha_creacion: str
    ultima_actividad: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/jugadores",
    tags=["jugadores"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Jugador])
async def get_jugadores():
    """Obtener todos los jugadores"""
    response = supabase.table("jugadores").select("*").execute()
    return response.data

@router.get("/{jugador_id}", response_model=Jugador)
async def get_jugador(jugador_id: UUID = Path(..., description="ID del jugador a obtener")):
    """Obtener un jugador por su ID"""
    response = supabase.table("jugadores").select("*").eq("player_id", str(jugador_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    return response.data[0]

@router.post("/", response_model=Jugador, status_code=201)
async def create_jugador(jugador: JugadorCreate = Body(...)):
    """Crear un nuevo jugador"""
    try:
        # Check if nickname or email already exists
        check_nickname = supabase.table("jugadores").select("nickname").eq("nickname", jugador.nickname).execute()
        if check_nickname.data:
            raise HTTPException(status_code=400, detail="El nickname ya está en uso")
        
        check_email = supabase.table("jugadores").select("email").eq("email", jugador.email).execute()
        if check_email.data:
            raise HTTPException(status_code=400, detail="El email ya está en uso")
        
        response = supabase.table("jugadores").insert(jugador.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear jugador: {str(e)}")

@router.put("/{jugador_id}", response_model=Jugador)
async def update_jugador(
    jugador_id: UUID = Path(..., description="ID del jugador a actualizar"),
    jugador: JugadorUpdate = Body(...)
):
    """Actualizar un jugador existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in jugador.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if jugador exists
        check_response = supabase.table("jugadores").select("*").eq("player_id", str(jugador_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Jugador no encontrado")
        
        # Check if updating nickname or email, verify they don't already exist
        if jugador.nickname:
            check_nickname = supabase.table("jugadores").select("nickname").eq("nickname", jugador.nickname).neq("player_id", str(jugador_id)).execute()
            if check_nickname.data:
                raise HTTPException(status_code=400, detail="El nickname ya está en uso")
        
        if jugador.email:
            check_email = supabase.table("jugadores").select("email").eq("email", jugador.email).neq("player_id", str(jugador_id)).execute()
            if check_email.data:
                raise HTTPException(status_code=400, detail="El email ya está en uso")
        
        # Update jugador
        response = supabase.table("jugadores").update(update_data).eq("player_id", str(jugador_id)).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Jugador no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al actualizar jugador: {str(e)}")

@router.delete("/{jugador_id}", status_code=204)
async def delete_jugador(jugador_id: UUID = Path(..., description="ID del jugador a eliminar")):
    """Eliminar un jugador"""
    try:
        # Check if jugador exists
        check_response = supabase.table("jugadores").select("*").eq("player_id", str(jugador_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Jugador no encontrado")
        
        # Delete jugador
        supabase.table("jugadores").delete().eq("player_id", str(jugador_id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Jugador no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al eliminar jugador: {str(e)}")
