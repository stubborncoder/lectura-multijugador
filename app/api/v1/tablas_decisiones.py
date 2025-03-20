from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for TablaDecision
class TablaDecisionBase(BaseModel):
    historia_id: UUID
    nombre: str
    descripcion: Optional[str] = None
    condiciones: List[Dict[str, Any]] = Field(default_factory=list)
    resultados: List[Dict[str, Any]] = Field(default_factory=list)
    estado: str = "activo"

class TablaDecisionCreate(TablaDecisionBase):
    pass

class TablaDecisionUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    condiciones: Optional[List[Dict[str, Any]]] = None
    resultados: Optional[List[Dict[str, Any]]] = None
    estado: Optional[str] = None

class TablaDecision(TablaDecisionBase):
    table_id: UUID
    fecha_creacion: str
    fecha_modificacion: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/tablas-decisiones",
    tags=["tablas_decisiones"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[TablaDecision])
async def get_tablas_decisiones():
    """Obtener todas las tablas de decisiones"""
    response = supabase.table("tablas_decisiones").select("*").execute()
    return response.data

@router.get("/{tabla_id}", response_model=TablaDecision)
async def get_tabla_decision(tabla_id: UUID = Path(..., description="ID de la tabla de decisión a obtener")):
    """Obtener una tabla de decisión por su ID"""
    response = supabase.table("tablas_decisiones").select("*").eq("table_id", str(tabla_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Tabla de decisión no encontrada")
    
    return response.data[0]

@router.get("/historia/{historia_id}", response_model=List[TablaDecision])
async def get_tablas_by_historia(historia_id: UUID = Path(..., description="ID de la historia")):
    """Obtener todas las tablas de decisiones de una historia específica"""
    response = supabase.table("tablas_decisiones").select("*").eq("historia_id", str(historia_id)).execute()
    return response.data

@router.post("/", response_model=TablaDecision, status_code=201)
async def create_tabla_decision(tabla: TablaDecisionCreate = Body(...)):
    """Crear una nueva tabla de decisión"""
    try:
        # Check if historia exists
        historia_check = supabase.table("historias").select("story_id").eq("story_id", str(tabla.historia_id)).execute()
        if not historia_check.data:
            raise HTTPException(status_code=404, detail="La historia especificada no existe")
        
        response = supabase.table("tablas_decisiones").insert(tabla.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear tabla de decisión: {str(e)}")

@router.put("/{tabla_id}", response_model=TablaDecision)
async def update_tabla_decision(
    tabla_id: UUID = Path(..., description="ID de la tabla de decisión a actualizar"),
    tabla: TablaDecisionUpdate = Body(...)
):
    """Actualizar una tabla de decisión existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in tabla.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if tabla exists
        check_response = supabase.table("tablas_decisiones").select("*").eq("table_id", str(tabla_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Tabla de decisión no encontrada")
        
        # Update tabla
        response = supabase.table("tablas_decisiones").update(update_data).eq("table_id", str(tabla_id)).execute()
        return response.data[0]
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Tabla de decisión no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al actualizar tabla de decisión: {str(e)}")

@router.delete("/{tabla_id}", status_code=204)
async def delete_tabla_decision(tabla_id: UUID = Path(..., description="ID de la tabla de decisión a eliminar")):
    """Eliminar una tabla de decisión"""
    try:
        # Check if tabla exists
        check_response = supabase.table("tablas_decisiones").select("*").eq("table_id", str(tabla_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Tabla de decisión no encontrada")
        
        # Delete tabla
        supabase.table("tablas_decisiones").delete().eq("table_id", str(tabla_id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Tabla de decisión no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al eliminar tabla de decisión: {str(e)}")
