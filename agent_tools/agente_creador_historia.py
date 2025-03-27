import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from agents import Agent, function_tool
from models.models import Historia

# Define a simple function to create a Historia from user input
@function_tool("create_historia")
def create_historia(titulo: str, descripcion: str, min_jugadores: int, max_jugadores: int, generos: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create a Historia object from the provided parameters.
    
    Args:
        titulo: The title of the story
        descripcion: The description of the story
        min_jugadores: Minimum number of players
        max_jugadores: Maximum number of players
        generos: Optional list of genres
        
    Returns:
        A dictionary representation of the Historia
    """
    # Create a Historia object
    historia = Historia(
        story_id=str(uuid.uuid4()),
        titulo=titulo,
        descripcion=descripcion,
        min_jugadores=min_jugadores,
        max_jugadores=max_jugadores,
        generos=generos,
        autor_id=str(uuid.uuid4()),  # Generate a random author ID for testing
        fecha_creacion=datetime.now(timezone.utc).isoformat(),
        fecha_modificacion=datetime.now(timezone.utc).isoformat(),
        estado="borrador"  # Default state
    )
    
    # Return the Historia as a dictionary
    return historia.model_dump()

# Define the agente_creador_historia agent
agente_creador_historia = Agent(
    name="Creador de Historia",
    handoff_description="Agente especialista en la el tratamiento de la tabla o entidad **HISTORIA** para lectura multijugardor",
    instructions="""Se encarga de interpretar la información que recibe y crear una estructura JSON con los datos de la historia.
                
    Tu tarea es extraer los datos necesarios para crear una Historia y devolverlos en formato JSON.
    
    Debes asegurarte de que los siguientes campos obligatorios estén presentes:
    - titulo: Título de la historia
    - min_jugadores: Número mínimo de jugadores (debe ser al menos 1)
    - max_jugadores: Número máximo de jugadores (debe ser al menos igual a min_jugadores)
    - autor_id: Se generará automáticamente, no te preocupes por este campo
    
    También puedes incluir estos campos opcionales si están disponibles:
    - descripcion: Descripción o sinopsis de la historia
    - generos: Lista de géneros literarios
    - dificultad: Nivel de complejidad (1-5)
    - imagen_portada: URL de la imagen de portada
    - estado: Estado de la historia (por defecto es "borrador")
    """,
    tools=[create_historia]
)
