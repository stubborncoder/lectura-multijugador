from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict, Any, Optional, Union
from app.database import supabase
from uuid import UUID
from pydantic import BaseModel, Field

# Pydantic model for Variable
class VariableBase(BaseModel):
    historia_id: UUID
    nombre: str
    tipo: str  # string, number, boolean, object, array
    valor_defecto: Union[str, int, float, bool, Dict[str, Any], List[Any]]
    descripcion: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    estado: str = "activo"

class VariableCreate(VariableBase):
    pass

class VariableUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    valor_defecto: Optional[Union[str, int, float, bool, Dict[str, Any], List[Any]]] = None
    descripcion: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    estado: Optional[str] = None

class Variable(VariableBase):
    variable_id: UUID
    fecha_creacion: str
    fecha_modificacion: str

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/variables",
    tags=["variables"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Variable])
async def get_variables():
    """Obtener todas las variables"""
    response = supabase.table("variables").select("*").execute()
    return response.data

@router.get("/{variable_id}", response_model=Variable)
async def get_variable(variable_id: UUID = Path(..., description="ID de la variable a obtener")):
    """Obtener una variable por su ID"""
    response = supabase.table("variables").select("*").eq("variable_id", str(variable_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Variable no encontrada")
    
    return response.data[0]

@router.get("/historia/{historia_id}", response_model=List[Variable])
async def get_variables_by_historia(historia_id: UUID = Path(..., description="ID de la historia")):
    """Obtener todas las variables de una historia específica"""
    response = supabase.table("variables").select("*").eq("historia_id", str(historia_id)).execute()
    return response.data

@router.post("/", response_model=Variable, status_code=201)
async def create_variable(variable: VariableCreate = Body(...)):
    """Crear una nueva variable"""
    try:
        # Check if historia exists
        historia_check = supabase.table("historias").select("story_id").eq("story_id", str(variable.historia_id)).execute()
        if not historia_check.data:
            raise HTTPException(status_code=404, detail="La historia especificada no existe")
        
        # Check if variable name already exists for this historia
        name_check = supabase.table("variables").select("nombre").eq("historia_id", str(variable.historia_id)).eq("nombre", variable.nombre).execute()
        if name_check.data:
            raise HTTPException(status_code=400, detail=f"Ya existe una variable con el nombre '{variable.nombre}' en esta historia")
        
        response = supabase.table("variables").insert(variable.dict()).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear variable: {str(e)}")

@router.put("/{variable_id}", response_model=Variable)
async def update_variable(
    variable_id: UUID = Path(..., description="ID de la variable a actualizar"),
    variable: VariableUpdate = Body(...)
):
    """Actualizar una variable existente"""
    # Remove None values from the update data
    update_data = {k: v for k, v in variable.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
    
    try:
        # Check if variable exists
        check_response = supabase.table("variables").select("*").eq("variable_id", str(variable_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Variable no encontrada")
        
        existing_variable = check_response.data[0]
        
        # If updating nombre, check if it already exists for this historia
        if variable.nombre and variable.nombre != existing_variable["nombre"]:
            name_check = supabase.table("variables").select("nombre").eq("historia_id", existing_variable["historia_id"]).eq("nombre", variable.nombre).execute()
            if name_check.data:
                raise HTTPException(status_code=400, detail=f"Ya existe una variable con el nombre '{variable.nombre}' en esta historia")
        
        # Update variable
        response = supabase.table("variables").update(update_data).eq("variable_id", str(variable_id)).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Variable no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al actualizar variable: {str(e)}")

@router.delete("/{variable_id}", status_code=204)
async def delete_variable(variable_id: UUID = Path(..., description="ID de la variable a eliminar")):
    """Eliminar una variable"""
    try:
        # Check if variable exists
        check_response = supabase.table("variables").select("*").eq("variable_id", str(variable_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Variable no encontrada")
        
        # Delete variable
        supabase.table("variables").delete().eq("variable_id", str(variable_id)).execute()
        return None
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Variable no encontrada")
        raise HTTPException(status_code=400, detail=f"Error al eliminar variable: {str(e)}")
