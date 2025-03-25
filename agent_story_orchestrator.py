import asyncio
import json
import os
import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from agents import Agent, Runner, function_tool, RunContextWrapper, trace
from pydantic import BaseModel, Field


# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Successfully loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not available, skipping .env loading")



# Check if OPENAI_API_KEY is in environment variables
if "OPENAI_API_KEY" not in os.environ:
    print("OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")
else:
    print("OPENAI_API_KEY found in environment variables")


class Historia(BaseModel):
    """
    Modelo Pydantic para representar una historia interactiva.
    """
    story_id: str = Field(..., description="Identificador ├║nico de la historia")
    titulo: str = Field(..., description="T├¡tulo principal de la historia que se mostrar├í a los usuarios")
    descripcion: Optional[str] = Field(None, description="Resumen o sinopsis del contenido de la historia")
    generos: Optional[List[str]] = Field(None, description="Categor├¡as o g├®neros literarios a los que pertenece la historia")
    dificultad: Optional[int] = Field(None, description="Nivel de complejidad de la historia (1-5, donde 5 es muy dif├¡cil)")
    imagen_portada: Optional[str] = Field(None, description="URL o ruta a la imagen de portada que representa visualmente la historia")
    min_jugadores: int = Field(..., description="Cantidad m├¡nima de jugadores necesarios para iniciar una partida")
    max_jugadores: int = Field(..., description="Capacidad m├íxima de jugadores que pueden participar simult├íneamente")
    autor_id: str = Field(..., description="Identificador del usuario que cre├│ la historia")
    fecha_creacion: str = Field(..., description="Fecha y hora en que se cre├│ la historia en la base de datos")
    fecha_modificacion: str = Field(..., description="Fecha y hora de la ├║ltima actualizaci├│n de cualquier campo")
    estado: Optional[str] = Field(..., description="Estado actual de la historia (borrador, publicada, archivada, etc.)")


class Personaje(BaseModel):
    """
    Modelo Pydantic para representar un personaje en una historia interactiva.
    """
    personaje_id: str = Field(..., description="Identificador ├║nico del personaje")
    nombre: str = Field(..., description="Nombre del personaje que se mostrar├í a los usuarios")
    descripcion: Optional[str] = Field(None, description="Descripci├│n f├¡sica y de personalidad del personaje")
    story_id: str = Field(..., description="Identificador de la historia a la que pertenece el personaje")
    rol: Optional[str] = Field(None, description="Rol del personaje en la historia (protagonista, antagonista, secundario, etc.)")
    habilidades: Optional[List[str]] = Field(None, description="Lista de habilidades especiales que posee el personaje")
    nivel_poder: Optional[int] = Field(None, description="Nivel de poder del personaje (1-10, donde 10 es muy poderoso)")
    imagen_perfil: Optional[str] = Field(None, description="URL o ruta a la imagen que representa visualmente al personaje")
    edad: Optional[int] = Field(None, description="Edad del personaje en a├▒os")
    origen: Optional[str] = Field(None, description="Lugar de origen o procedencia del personaje")
    creador_id: str = Field(..., description="Identificador del usuario que cre├│ el personaje")
    fecha_creacion: str = Field(..., description="Fecha y hora en que se cre├│ el personaje en la base de datos")
    fecha_modificacion: str = Field(..., description="Fecha y hora de la ├║ltima actualizaci├│n de cualquier campo")
    estado: Optional[str] = Field(..., description="Estado actual del personaje (activo, inactivo, eliminado, etc.)")


class ContenedorHistoria(BaseModel):
    """
    Modelo Pydantic que contiene una Historia como ├║nico campo.
    Puede ser utilizado para encapsular una Historia en estructuras de datos m├ís complejas.
    """
    historia: Historia = Field(..., description="Historia interactiva contenida en este modelo")
    personajes: List[Personaje] = Field(default_factory=list, description="Lista de personajes asociados a esta historia")
    

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
        autor_id=str(uuid.uuid4())  # Generate a random author ID for testing
    )
    
    # Return the Historia as a dictionary
    return historia.model_dump()

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

# Function to create a ContenedorHistoria from a Historia
@function_tool
def create_contenedor_historia(
    ctx: RunContextWrapper,
    titulo: Optional[str] = None,
    descripcion: Optional[str] = None,
    generos: Optional[List[str]] = None,
    dificultad: Optional[int] = None,
    imagen_portada: Optional[str] = None,
    min_jugadores: Optional[int] = None,
    max_jugadores: Optional[int] = None,
    estado: Optional[str] = None,
    personajes: Optional[List[Dict[str, Any]]] = None,
) -> ContenedorHistoria:
    """
    Crea un ContenedorHistoria con una Historia y opcionalmente personajes.
    
    Args:
        titulo: T├¡tulo de la historia
        descripcion: Descripci├│n de la historia
        generos: Lista de g├®neros de la historia
        dificultad: Nivel de dificultad de la historia (1-5)
        imagen_portada: URL o ruta a la imagen de portada
        min_jugadores: N├║mero m├¡nimo de jugadores
        max_jugadores: N├║mero m├íximo de jugadores
        estado: Estado de la historia (borrador, publicada, etc.)
        personajes: Lista de diccionarios con datos de personajes
        
    Returns:
        ContenedorHistoria object
    """
    # Usar valores predeterminados si no se proporcionan
    titulo = titulo or "Historia sin t├¡tulo"
    min_jugadores = min_jugadores or 1
    max_jugadores = max_jugadores or 4
    
    # Crear la historia
    historia = Historia(
        story_id=str(uuid.uuid4()),
        titulo=titulo,
        descripcion=descripcion,
        generos=generos,
        dificultad=dificultad,
        imagen_portada=imagen_portada,
        min_jugadores=min_jugadores,
        max_jugadores=max_jugadores,
        autor_id=str(uuid.uuid4()),
        fecha_creacion=datetime.now(timezone.utc).isoformat(),
        fecha_modificacion=datetime.now(timezone.utc).isoformat(),
        estado=estado
    )
    
    # Crear lista de personajes si se proporcionan
    personajes_list = []
    if personajes:
        for personaje_data in personajes:
            # Asegurarse de que el personaje tenga el ID de la historia
            personaje_data['story_id'] = historia.story_id
            # A├▒adir campos obligatorios si no est├ín presentes
            if 'creador_id' not in personaje_data:
                personaje_data['creador_id'] = historia.autor_id
            if 'personaje_id' not in personaje_data:
                personaje_data['personaje_id'] = str(uuid.uuid4())
            if 'fecha_creacion' not in personaje_data:
                personaje_data['fecha_creacion'] = historia.fecha_creacion
            if 'fecha_modificacion' not in personaje_data:
                personaje_data['fecha_modificacion'] = historia.fecha_modificacion
            if 'estado' not in personaje_data:
                personaje_data['estado'] = 'activo'
                
            # Crear el objeto Personaje y a├▒adirlo a la lista
            personajes_list.append(Personaje(**personaje_data))
    
    # Crear el contenedor
    contenedor = ContenedorHistoria(historia=historia, personajes=personajes_list)
    
    # Devolver el contenedor directamente
    return contenedor

# Define the agente_creador_historia agent
agente_creador_historia = Agent(
    name="Creador de Historia",
    handoff_description="Agente especialista en la el tratamiento de la tabla o entidad **HISTORIA** para lectura multijugardor",
    instructions="""Se encarga de interpretar la informaci├│n que recibe y crear una estructura JSON con los datos de la historia.
                
    Tu tarea es extraer los datos necesarios para crear una Historia y devolverlos en formato JSON.
    
    Debes asegurarte de que los siguientes campos obligatorios est├®n presentes:
    - titulo: T├¡tulo de la historia
    - min_jugadores: N├║mero m├¡nimo de jugadores (debe ser al menos 1)
    - max_jugadores: N├║mero m├íximo de jugadores (debe ser al menos igual a min_jugadores)
    - autor_id: Se generar├í autom├íticamente, no te preocupes por este campo
    
    Tambi├®n puedes incluir estos campos opcionales si est├ín disponibles:
    - descripcion: Descripci├│n o sinopsis de la historia
    - generos: Lista de g├®neros literarios
    - dificultad: Nivel de complejidad (1-5)
    - imagen_portada: URL de la imagen de portada
    - estado: Estado de la historia (por defecto es "borrador")
    """,
    tools=[create_historia]
)

# Define the agente_creador_de_personajes agent
agente_creador_de_personajes = Agent(
    name="Creador de Personajes",
    handoff_description="Agente especialista en la el tratamiento de la tabla o entidad **PERSONAJE** para lectura multijugardor",
    instructions="""Se encarga de interpretar la informaci├│n que recibe y crear los personajes para una historia.
                
    Tu tarea es extraer los datos necesarios para crear los personajes y devolverlos en formato JSON.
    
    IMPORTANTE: Debes utilizar el story_id proporcionado por la historia previamente creada.
    
    Debes asegurarte de que los siguientes campos obligatorios est├®n presentes:
    - nombre: Nombre del personaje
    - story_id: ID de la historia a la que pertenece el personaje (DEBE ser el ID de una historia existente)
    
    Tambi├®n puedes incluir estos campos opcionales si est├ín disponibles:
    - descripcion: Descripci├│n f├¡sica y de personalidad del personaje
    - rol: Rol del personaje en la historia (protagonista, antagonista, etc.)
    - habilidades: Lista de habilidades especiales que posee el personaje
    - nivel_poder: Nivel de poder del personaje (1-10)
    - imagen_perfil: URL o ruta a la imagen que representa al personaje
    - edad: Edad del personaje en a├▒os
    - origen: Lugar de origen o procedencia del personaje
    """,
    tools=[create_personaje]
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        """Eres un agente que utiliza sus herramientas para crear historias interactivas.
        
        IMPORTANTE: Tu ├ÜNICA tarea es extraer informaci├│n del mensaje del usuario, llamar a las herramientas que tienes y
        devolver el objeto JSON con la estructura correcta.
        
        Sigue estos pasos en ORDEN ESTRICTO:
        
        1. Extrae del mensaje del usuario los datos para crear una historia:
           - t├¡tulo
           - descripci├│n
           - min_jugadores
           - max_jugadores
           - g├®neros
           - dificultad
           - estado
        
        2. PRIMERO llama a la herramienta creador_historia para crear la historia y obtener su ID.
        
        3. DESPU├ëS extrae del mensaje del usuario los datos para crear los personajes.
           - DEBES crear al menos 2 personajes para cada historia.
           - Si el usuario no especifica personajes, crea personajes que sean apropiados para la historia.
           - Aseg├║rate de que cada personaje tenga al menos un nombre y una descripci├│n.
        
        4. Utiliza el story_id obtenido de la historia creada en el paso 2 para crear los personajes
           con la herramienta creador_de_personajes. Aseg├║rate de asignar el story_id correcto a cada personaje.
        
        5. Finalmente, utiliza create_contenedor_historia para crear un contenedor que incluya
           tanto la historia como los personajes.
        
        6. Si falta informaci├│n, usa estos valores predeterminados:
           - t├¡tulo = "Historia sin t├¡tulo"
           - min_jugadores = 1
           - max_jugadores = 4
           - descripci├│n = null
           - g├®neros = null
           - dificultad = null
           - estado = null
                      
        7. Devuelve EXACTAMENTE el JSON que te proporciona la herramienta, sin a├▒adir texto adicional.
        
        NUNCA hagas preguntas al usuario. Si falta informaci├│n, usa los valores predeterminados.
        """
    ),
    tools=[
        agente_creador_historia.as_tool(
            tool_name="creador_historia",
            tool_description="Agente especialista en la el tratamiento de la tabla o entidad **HISTORIA** para lectura multijugardor",
        ),
        agente_creador_de_personajes.as_tool(
            tool_name="creador_de_personajes",
            tool_description="Agente especialista en la el tratamiento de la tabla o entidad **PERSONAJE** para lectura multijugardor",
        ),
        create_contenedor_historia,
    ],
    output_type=ContenedorHistoria
)

async def main():
    print("Iniciando el agente orquestador para crear historias interactivas...")
    
    try:
        # Initial prompt
        msg = input("""
Por favor, proporciona informaci├│n para tu historia interactiva.
Por ejemplo: 'El t├¡tulo de la historia ser├í 'El asombroso pedo errante', la descripci├│n ser├¡a 'Una aventura m├ígica en un bosque lleno de criaturas fant├ísticas y misterios por resolver.' El m├¡nimo de jugadores es 2 y el m├íximo 3. Incluye personajes como un guerrero, un mago y un p├¡caro.'

Tu entrada: """)

        print("\nProcesando tu solicitud...\n")

        # Run the agent with the user's message
        with trace("Orchestrator evaluator") as session:
            try:
                # Use Runner.run with the user's message
                result = await Runner.run(orchestrator_agent, msg)
                
                # Print the result
                print("\n=== RESULTADO ===")
                
                # Check if we have a final_output
                if hasattr(result, 'final_output') and result.final_output:
                    try:
                        # If it's a ContenedorHistoria object
                        if isinstance(result.final_output, ContenedorHistoria):
                            # Format the historia
                            historia_dict = result.final_output.historia.model_dump()
                            print("Historia:")
                            print(json.dumps(historia_dict, indent=2, ensure_ascii=False))
                            
                            # Format the personajes if any
                            if result.final_output.personajes:
                                print("\nPersonajes:")
                                for i, personaje in enumerate(result.final_output.personajes, 1):
                                    print(f"\nPersonaje {i}:")
                                    personaje_dict = personaje.model_dump()
                                    print(json.dumps(personaje_dict, indent=2, ensure_ascii=False))
                                                        
                        # Try to parse as JSON if it's a string
                        elif isinstance(result.final_output, str):
                            try:
                                # If it's valid JSON, we've created a story
                                json_output = json.loads(result.final_output)
                                print(json.dumps(json_output, indent=2, ensure_ascii=False))

                            except json.JSONDecodeError:
                                print("La respuesta no es un JSON v├ílido:")
                                print(result.final_output)
                        # If it's already a dict or other object, format it nicely
                        elif isinstance(result.final_output, dict):
                            print(json.dumps(result.final_output, indent=2, ensure_ascii=False))
                            
                        else:
                            print(str(result.final_output))
                    except Exception as e:
                        print(f"Error al formatear la salida: {e}")
                        print(str(result.final_output) if result.final_output else "No hay respuesta")
                else:
                    # Try to extract output from new_items
                    if hasattr(result, 'new_items') and result.new_items:
                        for item in result.new_items:
                            if hasattr(item, 'content') and item.content:
                                try:
                                    # Try to parse as JSON
                                    json_content = json.loads(item.content)
                                    print(json.dumps(json_content, indent=2, ensure_ascii=False))

                                    break
                                except json.JSONDecodeError:
                                    # Not JSON, continue checking other items
                                    continue
                    else:
                        print("No se ha generado una respuesta estructurada.")
                
                print("\n=== FIN DEL RESULTADO ===")
                
            except Exception as e:
                print(f"Error durante la ejecuci├│n: {e}")
                import traceback
                traceback.print_exc()
    
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma terminado por el usuario.")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
