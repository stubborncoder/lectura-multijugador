from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Historia(BaseModel):
    """
    Modelo Pydantic para representar una historia interactiva.
    """
    story_id: str = Field(..., description="Identificador único de la historia")
    titulo: str = Field(..., description="Título principal de la historia que se mostrará a los usuarios")
    descripcion: Optional[str] = Field(None, description="Resumen o sinopsis del contenido de la historia")
    generos: Optional[List[str]] = Field(None, description="Categorías o géneros literarios a los que pertenece la historia")
    dificultad: Optional[int] = Field(None, description="Nivel de complejidad de la historia (1-5, donde 5 es muy difícil)")
    imagen_portada: Optional[str] = Field(None, description="URL o ruta a la imagen de portada que representa visualmente la historia")
    min_jugadores: int = Field(..., description="Cantidad mínima de jugadores necesarios para iniciar una partida")
    max_jugadores: int = Field(..., description="Capacidad máxima de jugadores que pueden participar simultáneamente")
    autor_id: str = Field(..., description="Identificador del usuario que creó la historia")
    fecha_creacion: str = Field(..., description="Fecha y hora en que se creó la historia en la base de datos")
    fecha_modificacion: str = Field(..., description="Fecha y hora de la última actualización de cualquier campo")
    estado: Optional[str] = Field(..., description="Estado actual de la historia (borrador, publicada, archivada, etc.)")


class Personaje(BaseModel):
    """
    Modelo Pydantic para representar un personaje en una historia interactiva.
    """
    personaje_id: str = Field(..., description="Identificador único del personaje")
    nombre: str = Field(..., description="Nombre del personaje que se mostrará a los usuarios")
    descripcion: Optional[str] = Field(None, description="Descripción física y de personalidad del personaje")
    story_id: str = Field(..., description="Identificador de la historia a la que pertenece el personaje")
    rol: Optional[str] = Field(None, description="Rol del personaje en la historia (protagonista, antagonista, secundario, etc.)")
    habilidades: Optional[List[str]] = Field(None, description="Lista de habilidades especiales que posee el personaje")
    nivel_poder: Optional[int] = Field(None, description="Nivel de poder del personaje (1-10, donde 10 es muy poderoso)")
    imagen_perfil: Optional[str] = Field(None, description="URL o ruta a la imagen que representa visualmente al personaje")
    edad: Optional[int] = Field(None, description="Edad del personaje en años")
    origen: Optional[str] = Field(None, description="Lugar de origen o procedencia del personaje")
    creador_id: str = Field(..., description="Identificador del usuario que creó el personaje")
    fecha_creacion: str = Field(..., description="Fecha y hora en que se creó el personaje en la base de datos")
    fecha_modificacion: str = Field(..., description="Fecha y hora de la última actualización de cualquier campo")
    estado: Optional[str] = Field(..., description="Estado actual del personaje (activo, inactivo, eliminado, etc.)")


class ContenedorHistoria(BaseModel):
    """
    Modelo Pydantic que contiene una Historia como único campo.
    Puede ser utilizado para encapsular una Historia en estructuras de datos más complejas.
    """
    historia: Historia = Field(..., description="Historia interactiva contenida en este modelo")
    personajes: List[Personaje] = Field(default_factory=list, description="Lista de personajes asociados a esta historia")
