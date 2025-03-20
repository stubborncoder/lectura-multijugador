from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for HistorialDecision
class HistorialDecisionBase(BaseModel):
    partida_id: UUID
    jugador_id: UUID
    nodo_id: UUID
    opcion_id: UUID
    variables_antes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    variables_despues: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class HistorialDecisionCreate(HistorialDecisionBase):
    pass

class HistorialDecisionUpdate(BaseModel):
    variables_antes: Optional[Dict[str, Any]] = None
    variables_despues: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class HistorialDecision(HistorialDecisionBase):
    id: UUID
    fecha_decision: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/historial-decisiones",
    tags=["historial_decisiones"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[HistorialDecision])
async def get_historial_decisiones():
    """Obtener todo el historial de decisiones"""
    response = supabase.table("historial_decisiones").select("*").execute()
    return response.data

@router.get("/{id}", response_model=HistorialDecision)
async def get_historial_decision(id: UUID = Path(..., description="ID del registro de historial a obtener")):
    """Obtener un registro de historial por su ID"""
    response = supabase.table("historial_decisiones").select("*").eq("id", str(id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Registro de historial no encontrado")
    
    return response.data[0]

@router.get("/partida/{partida_id}", response_model=List[HistorialDecision])
async def get_historial_by_partida(partida_id: UUID = Path(..., description="ID de la partida")):
    """Obtener todo el historial de decisiones de una partida específica"""
    response = supabase.table("historial_decisiones").select("*").eq("partida_id", str(partida_id)).execute()
    return response.data

@router.get("/jugador/{jugador_id}", response_model=List[HistorialDecision])
async def get_historial_by_jugador(jugador_id: UUID = Path(..., description="ID del jugador")):
    """Obtener todo el historial de decisiones de un jugador específico"""
    response = supabase.table("historial_decisiones").select("*").eq("jugador_id", str(jugador_id)).execute()
    return response.data

@router.get("/partida/{partida_id}/jugador/{jugador_id}", response_model=List[HistorialDecision])
async def get_historial_by_partida_and_jugador(
    partida_id: UUID = Path(..., description="ID de la partida"),
    jugador_id: UUID = Path(..., description="ID del jugador")
):
    """Obtener el historial de decisiones de un jugador en una partida específica"""
    response = supabase.table("historial_decisiones").select("*").eq("partida_id", str(partida_id)).eq("jugador_id", str(jugador_id)).execute()
    return response.data

@router.post("/", response_model=HistorialDecision, status_code=201)
async def create_historial_decision(historial: HistorialDecisionCreate = Body(...)):
    """Crear un nuevo registro de historial de decisión"""
    try:
        # Check if partida exists
        partida_check = supabase.table("partidas").select("game_id").eq("game_id", str(historial.partida_id)).execute()
        if not partida_check.data:
            raise HTTPException(status_code=404, detail="La partida especificada no existe")
        
        # Check if jugador exists
        jugador_check = supabase.table("jugadores").select("player_id").eq("player_id", str(historial.jugador_id)).execute()
        if not jugador_check.data:
            raise HTTPException(status_code=404, detail="El jugador especificado no existe")
        
        # Check if nodo exists
        nodo_check = supabase.table("nodos").select("node_id").eq("node_id", str(historial.nodo_id)).execute()
        if not nodo_check.data:
            raise HTTPException(status_code=404, detail="El nodo especificado no existe")
        
        # Check if opcion exists
        opcion_check = supabase.table("opciones").select("option_id").eq("option_id", str(historial.opcion_id)).execute()
        if not opcion_check.data:
            raise HTTPException(status_code=404, detail="La opción especificada no existe")
        
        # Check if jugador is in the partida
        partida_jugador_check = supabase.table("partidas_jugadores").select("id").eq("partida_id", str(historial.partida_id)).eq("jugador_id", str(historial.jugador_id)).execute()
        if not partida_jugador_check.data:
            raise HTTPException(status_code=400, detail="El jugador no está en esta partida")
        
        response = supabase.table("historial_decisiones").insert(historial.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear registro de historial: {str(e)}")

@router.put("/{id}", response_model=HistorialDecision)
async def update_historial_decision(
    id: UUID = Path(..., description="ID del registro de historial a actualizar"),
    historial: HistorialDecisionUpdate = Body(...)
):
    """Actualizar un registro de historial existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in historial.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if historial exists
        check_response = supabase.table("historial_decisiones").select("*").eq("id", str(id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Registro de historial no encontrado")
        
        # Update historial
        response = supabase.table("historial_decisiones").update(update_data).eq("id", str(id)).execute()
        return response.data[0]
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Registro de historial no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al actualizar registro de historial: {str(e)}")

@router.delete("/{id}", status_code=204)
async def delete_historial_decision(id: UUID = Path(..., description="ID del registro de historial a eliminar")):
    """Eliminar un registro de historial"""
    try:
        # Check if historial exists
        check_response = supabase.table("historial_decisiones").select("*").eq("id", str(id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Registro de historial no encontrado")
        
        # Delete historial
        supabase.table("historial_decisiones").delete().eq("id", str(id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Registro de historial no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al eliminar registro de historial: {str(e)}")
