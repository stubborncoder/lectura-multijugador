from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for Opcion
class OpcionBase(BaseModel):
    nodo_origen_id: UUID
    nodo_destino_id: UUID
    texto: str
    condiciones: Optional[Dict[str, Any]] = Field(default_factory=dict)
    efectos: Optional[Dict[str, Any]] = Field(default_factory=dict)
    orden: Optional[int] = None
    estado: str = "activo"

class OpcionCreate(OpcionBase):
    pass

class OpcionUpdate(BaseModel):
    nodo_origen_id: Optional[UUID] = None
    nodo_destino_id: Optional[UUID] = None
    texto: Optional[str] = None
    condiciones: Optional[Dict[str, Any]] = None
    efectos: Optional[Dict[str, Any]] = None
    orden: Optional[int] = None
    estado: Optional[str] = None

class Opcion(OpcionBase):
    option_id: UUID
    fecha_creacion: str
    fecha_modificacion: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/opciones",
    tags=["opciones"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Opcion])
async def get_opciones():
    """Obtener todas las opciones"""
    response = supabase.table("opciones").select("*").execute()
    return response.data

@router.get("/{opcion_id}", response_model=Opcion)
async def get_opcion(opcion_id: UUID = Path(..., description="ID de la opción a obtener")):
    """Obtener una opción por su ID"""
    response = supabase.table("opciones").select("*").eq("option_id", str(opcion_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Opción no encontrada")
    
    return response.data[0]

@router.get("/nodo/{nodo_id}", response_model=List[Opcion])
async def get_opciones_by_nodo(nodo_id: UUID = Path(..., description="ID del nodo origen")):
    """Obtener todas las opciones de un nodo específico"""
    response = supabase.table("opciones").select("*").eq("nodo_origen_id", str(nodo_id)).execute()
    return response.data

@router.post("/", response_model=Opcion, status_code=201)
async def create_opcion(opcion: OpcionCreate = Body(...)):
    """Crear una nueva opción"""
    try:
        # Check if nodo_origen exists
        nodo_origen_check = supabase.table("nodos").select("node_id").eq("node_id", str(opcion.nodo_origen_id)).execute()
        if not nodo_origen_check.data:
            raise HTTPException(status_code=404, detail="El nodo origen especificado no existe")
        
        # Check if nodo_destino exists
        nodo_destino_check = supabase.table("nodos").select("node_id").eq("node_id", str(opcion.nodo_destino_id)).execute()
        if not nodo_destino_check.data:
            raise HTTPException(status_code=404, detail="El nodo destino especificado no existe")
        
        response = supabase.table("opciones").insert(opcion.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear opción: {str(e)}")

@router.put("/{opcion_id}", response_model=Opcion)
async def update_opcion(
    opcion_id: UUID = Path(..., description="ID de la opción a actualizar"),
    opcion: OpcionUpdate = Body(...)
):
    """Actualizar una opción existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in opcion.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if opcion exists
        check_response = supabase.table("opciones").select("*").eq("option_id", str(opcion_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Opción no encontrada")
        
        # If updating nodo_origen, check if it exists
        if opcion.nodo_origen_id:
            nodo_origen_check = supabase.table("nodos").select("node_id").eq("node_id", str(opcion.nodo_origen_id)).execute()
            if not nodo_origen_check.data:
                raise HTTPException(status_code=404, detail="El nodo origen especificado no existe")
        
        # If updating nodo_destino, check if it exists
        if opcion.nodo_destino_id:
            nodo_destino_check = supabase.table("nodos").select("node_id").eq("node_id", str(opcion.nodo_destino_id)).execute()
            if not nodo_destino_check.data:
                raise HTTPException(status_code=404, detail="El nodo destino especificado no existe")
        
        # Update opcion
        response = supabase.table("opciones").update(update_data).eq("option_id", str(opcion_id)).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Opción no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al actualizar opción: {str(e)}")

@router.delete("/{opcion_id}", status_code=204)
async def delete_opcion(opcion_id: UUID = Path(..., description="ID de la opción a eliminar")):
    """Eliminar una opción"""
    try:
        # Check if opcion exists
        check_response = supabase.table("opciones").select("*").eq("option_id", str(opcion_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Opción no encontrada")
        
        # Delete opcion
        supabase.table("opciones").delete().eq("option_id", str(opcion_id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Opción no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al eliminar opción: {str(e)}")
