from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.database import supabase
from app.auth.auth import get_current_user

router = APIRouter(prefix="/autores", tags=["autores"])

# Modelos de datos
class RedesSocialesModel(BaseModel):
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    linkedin: Optional[str] = None
    otros: Optional[dict] = None

class AutorBase(BaseModel):
    nombre: str
    apellidos: Optional[str] = None
    nombre_artistico: Optional[str] = None
    biografia: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nacionalidad: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    redes_sociales: Optional[RedesSocialesModel] = None
    imagen_perfil: Optional[str] = None
    usuario_id: Optional[str] = None
    estado: str = "activo"

class AutorCreate(AutorBase):
    pass

class AutorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    nombre_artistico: Optional[str] = None
    biografia: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nacionalidad: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    redes_sociales: Optional[RedesSocialesModel] = None
    imagen_perfil: Optional[str] = None
    usuario_id: Optional[str] = None
    estado: Optional[str] = None

class Autor(AutorBase):
    autor_id: str
    fecha_creacion: str
    fecha_modificacion: str

    class Config:
        from_attributes = True

# Endpoints
@router.get("/", response_model=List[Autor])
async def get_autores(user=Depends(get_current_user)):
    """
    Obtiene todos los autores.
    """
    response = supabase.table("autores").select("*").execute()
    return response.data

@router.get("/{autor_id}", response_model=Autor)
async def get_autor(autor_id: str, user=Depends(get_current_user)):
    """
    Obtiene un autor por su ID.
    """
    response = supabase.table("autores").select("*").eq("autor_id", autor_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Autor con ID {autor_id} no encontrado")
    
    return response.data[0]

@router.post("/", response_model=Autor, status_code=status.HTTP_201_CREATED)
async def create_autor(autor: AutorCreate, user=Depends(get_current_user)):
    """
    Crea un nuevo autor.
    """
    try:
        autor_data = autor.model_dump()
        
        # Convertir redes_sociales a formato JSON si existe
        if autor_data.get("redes_sociales"):
            # Asegurarse de que redes_sociales sea un diccionario serializable
            autor_data["redes_sociales"] = autor_data["redes_sociales"].model_dump() if hasattr(autor_data["redes_sociales"], "model_dump") else autor_data["redes_sociales"]
        
        # Imprimir datos para debugging
        print(f"Datos a insertar: {autor_data}")
        
        response = supabase.table("autores").insert(autor_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo crear el autor")
        
        return response.data[0]
    except Exception as e:
        print(f"Error al crear autor: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")

@router.put("/{autor_id}", response_model=Autor)
async def update_autor(autor_id: str, autor: AutorUpdate, user=Depends(get_current_user)):
    """
    Actualiza un autor existente.
    """
    # Verificar que el autor existe
    check_response = supabase.table("autores").select("*").eq("autor_id", autor_id).execute()
    
    if not check_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Autor con ID {autor_id} no encontrado")
    
    # Filtrar campos nulos
    autor_data = {k: v for k, v in autor.model_dump().items() if v is not None}
    
    # Convertir redes_sociales a formato JSON si existe
    if autor_data.get("redes_sociales"):
        autor_data["redes_sociales"] = autor_data["redes_sociales"]
    
    response = supabase.table("autores").update(autor_data).eq("autor_id", autor_id).execute()
    
    return response.data[0]

@router.delete("/{autor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_autor(autor_id: str, user=Depends(get_current_user)):
    """
    Elimina un autor.
    """
    # Verificar que el autor existe
    check_response = supabase.table("autores").select("*").eq("autor_id", autor_id).execute()
    
    if not check_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Autor con ID {autor_id} no encontrado")
    
    supabase.table("autores").delete().eq("autor_id", autor_id).execute()
    
    return None

# Endpoints para la relación historias-autores
@router.get("/historia/{historia_id}", response_model=List[Autor])
async def get_autores_by_historia(historia_id: str, user=Depends(get_current_user)):
    """
    Obtiene todos los autores asociados a una historia.
    """
    response = supabase.table("historias_autores")\
        .select("autores(*)")\
        .eq("historia_id", historia_id)\
        .execute()
    
    # Extraer los datos de autores de la respuesta
    autores = [item["autores"] for item in response.data if "autores" in item]
    
    return autores

@router.get("/{autor_id}/historias", response_model=List[dict])
async def get_historias_by_autor(autor_id: str, user=Depends(get_current_user)):
    """
    Obtiene todas las historias asociadas a un autor.
    """
    response = supabase.table("historias_autores")\
        .select("historia_id, rol, porcentaje_contribucion, historias(*)")\
        .eq("autor_id", autor_id)\
        .execute()
    
    if not response.data:
        return []
    
    return response.data

@router.post("/historia/{historia_id}/autor/{autor_id}", status_code=status.HTTP_201_CREATED)
async def add_autor_to_historia(
    historia_id: str, 
    autor_id: str, 
    rol: Optional[str] = "autor principal",
    porcentaje_contribucion: Optional[int] = 100,
    user=Depends(get_current_user)
):
    """
    Asocia un autor a una historia.
    """
    # Verificar que la historia existe
    check_historia = supabase.table("historias").select("*").eq("story_id", historia_id).execute()
    if not check_historia.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Historia con ID {historia_id} no encontrada")
    
    # Verificar que el autor existe
    check_autor = supabase.table("autores").select("*").eq("autor_id", autor_id).execute()
    if not check_autor.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Autor con ID {autor_id} no encontrado")
    
    # Crear la relación
    data = {
        "historia_id": historia_id,
        "autor_id": autor_id,
        "rol": rol,
        "porcentaje_contribucion": porcentaje_contribucion
    }
    
    response = supabase.table("historias_autores").insert(data).execute()
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo asociar el autor a la historia")
    
    return response.data[0]

@router.delete("/historia/{historia_id}/autor/{autor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_autor_from_historia(historia_id: str, autor_id: str, user=Depends(get_current_user)):
    """
    Elimina la asociación entre un autor y una historia.
    """
    # Verificar que la relación existe
    check_response = supabase.table("historias_autores")\
        .select("*")\
        .eq("historia_id", historia_id)\
        .eq("autor_id", autor_id)\
        .execute()
    
    if not check_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No se encontró la relación entre la historia {historia_id} y el autor {autor_id}"
        )
    
    supabase.table("historias_autores")\
        .delete()\
        .eq("historia_id", historia_id)\
        .eq("autor_id", autor_id)\
        .execute()
    
    return None
