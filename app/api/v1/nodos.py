from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for Nodo
class NodoBase(BaseModel):
    historia_id: UUID
    titulo: str
    contenido: str
    tipo: str = "texto"  # texto, decision, final
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    estado: str = "activo"

class NodoCreate(NodoBase):
    pass

class NodoUpdate(BaseModel):
    titulo: Optional[str] = None
    contenido: Optional[str] = None
    tipo: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    estado: Optional[str] = None

class Nodo(NodoBase):
    node_id: UUID
    fecha_creacion: str
    fecha_modificacion: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/nodos",
    tags=["nodos"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Nodo])
async def get_nodos():
    """Obtener todos los nodos"""
    response = supabase.table("nodos").select("*").execute()
    return response.data

@router.get("/{nodo_id}", response_model=Nodo)
async def get_nodo(nodo_id: UUID = Path(..., description="ID del nodo a obtener")):
    """Obtener un nodo por su ID"""
    response = supabase.table("nodos").select("*").eq("node_id", str(nodo_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    
    return response.data[0]

@router.get("/historia/{historia_id}", response_model=List[Nodo])
async def get_nodos_by_historia(historia_id: UUID = Path(..., description="ID de la historia")):
    """Obtener todos los nodos de una historia específica"""
    response = supabase.table("nodos").select("*").eq("historia_id", str(historia_id)).execute()
    return response.data

@router.post("/", response_model=Nodo, status_code=201)
async def create_nodo(nodo: NodoCreate = Body(...)):
    """Crear un nuevo nodo"""
    try:
        # Check if historia exists
        historia_check = supabase.table("historias").select("story_id").eq("story_id", str(nodo.historia_id)).execute()
        if not historia_check.data:
            raise HTTPException(status_code=404, detail="La historia especificada no existe")
        
        response = supabase.table("nodos").insert(nodo.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear nodo: {str(e)}")

@router.put("/{nodo_id}", response_model=Nodo)
async def update_nodo(
    nodo_id: UUID = Path(..., description="ID del nodo a actualizar"),
    nodo: NodoUpdate = Body(...)
):
    """Actualizar un nodo existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in nodo.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if nodo exists
        check_response = supabase.table("nodos").select("*").eq("node_id", str(nodo_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        
        # Update nodo
        response = supabase.table("nodos").update(update_data).eq("node_id", str(nodo_id)).execute()
        return response.data[0]
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al actualizar nodo: {str(e)}")

@router.delete("/{nodo_id}", status_code=204)
async def delete_nodo(nodo_id: UUID = Path(..., description="ID del nodo a eliminar")):
    """Eliminar un nodo"""
    try:
        # Check if nodo exists
        check_response = supabase.table("nodos").select("*").eq("node_id", str(nodo_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        
        # Delete nodo
        supabase.table("nodos").delete().eq("node_id", str(nodo_id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        raise HTTPException(status_code=400, detail=f"Error al eliminar nodo: {str(e)}")
