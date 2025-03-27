import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from agents import Agent, function_tool
from models.models import Personaje

# Define a function to create a Personaje from user input
@function_tool("create_personaje")
def create_personaje(nombre: str, historia_id: str, descripcion: Optional[str] = None, rol: Optional[str] = None, 
                    habilidades: Optional[List[str]] = None, nivel_poder: Optional[int] = None, 
                    imagen_perfil: Optional[str] = None, edad: Optional[int] = None, 
                    origen: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a Personaje object from the provided parameters.
    
    Args:
        nombre: Name of the character
        historia_id: ID of the story the character belongs to (MUST be a valid story_id from a previously created Historia)
        descripcion: Description of the character's physical appearance and personality
        rol: Role of the character in the story (protagonist, antagonist, etc.)
        habilidades: List of special abilities the character possesses
        nivel_poder: Power level of the character (1-10, where 10 is very powerful)
        imagen_perfil: URL or path to the image representing the character
        edad: Age of the character in years
        origen: Place of origin or background of the character
        
    Returns:
        A dictionary representation of the Personaje
    """
    # Create a Personaje object
    personaje = Personaje(
        personaje_id=str(uuid.uuid4()),
        nombre=nombre,
        descripcion=descripcion,
        story_id=historia_id,
        rol=rol,
        habilidades=habilidades,
        nivel_poder=nivel_poder,
        imagen_perfil=imagen_perfil,
        edad=edad,
        origen=origen,
        creador_id=str(uuid.uuid4()),  # Generate a random creator ID for testing
        fecha_creacion=datetime.now(timezone.utc).isoformat(),
        fecha_modificacion=datetime.now(timezone.utc).isoformat(),
        estado="activo"  # Default state
    )
    
    # Return the Personaje as a dictionary
    return personaje.model_dump()

# Define the agente_creador_de_personajes agent
agente_creador_de_personajes = Agent(
    name="Creador de Personajes",
    handoff_description="Agente especialista en la el tratamiento de la tabla o entidad **PERSONAJE** para lectura multijugardor",
    instructions="""Se encarga de interpretar la información que recibe y crear los personajes para una historia.
                
    Tu tarea es extraer los datos necesarios para crear los personajes y devolverlos en formato JSON.
    
    IMPORTANTE: Debes utilizar el story_id proporcionado por la historia previamente creada.
    
    Debes asegurarte de que los siguientes campos obligatorios estén presentes:
    - nombre: Nombre del personaje
    - story_id: ID de la historia a la que pertenece el personaje (DEBE ser el ID de una historia existente)
    
    También puedes incluir estos campos opcionales si están disponibles:
    - descripcion: Descripción física y de personalidad del personaje
    - rol: Rol del personaje en la historia (protagonista, antagonista, etc.)
    - habilidades: Lista de habilidades especiales que posee el personaje
    - nivel_poder: Nivel de poder del personaje (1-10)
    - imagen_perfil: URL o ruta a la imagen que representa al personaje
    - edad: Edad del personaje en años
    - origen: Lugar de origen o procedencia del personaje
    """,
    tools=[create_personaje]
)
