import asyncio
import json
import os
import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from agents import Agent, Runner, function_tool, RunContextWrapper, trace
from pydantic import BaseModel, Field
from models.models import Historia, Personaje, ContenedorHistoria
from agent_tools.agente_creador_historia import agente_creador_historia
from agent_tools.agente_creador_personajes import agente_creador_de_personajes


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
        titulo: Título de la historia
        descripcion: Descripción de la historia
        generos: Lista de géneros de la historia
        dificultad: Nivel de dificultad de la historia (1-5)
        imagen_portada: URL o ruta a la imagen de portada
        min_jugadores: Número mínimo de jugadores
        max_jugadores: Número máximo de jugadores
        estado: Estado de la historia (borrador, publicada, etc.)
        personajes: Lista de diccionarios con datos de personajes
        
    Returns:
        ContenedorHistoria object
    """
    # Usar valores predeterminados si no se proporcionan
    titulo = titulo or "Historia sin título"
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
            # Añadir campos obligatorios si no están presentes
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
                
            # Crear el objeto Personaje y añadirlo a la lista
            personajes_list.append(Personaje(**personaje_data))
    
    # Crear el contenedor
    contenedor = ContenedorHistoria(historia=historia, personajes=personajes_list)
    
    # Devolver el contenedor directamente
    return contenedor

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        """Eres un agente que utiliza sus herramientas para crear historias interactivas.
        
        IMPORTANTE: Tu ÚNICA tarea es extraer información del mensaje del usuario, llamar a las herramientas que tienes y
        devolver el objeto JSON con la estructura correcta.
        
        Sigue estos pasos en ORDEN ESTRICTO:
        
        1. Extrae del mensaje del usuario los datos para crear una historia:
           - título
           - descripción
           - min_jugadores
           - max_jugadores
           - géneros
           - dificultad
           - estado
        
        2. PRIMERO llama a la herramienta creador_historia para crear la historia y obtener su ID.
        
        3. DESPUÉS extrae del mensaje del usuario los datos para crear los personajes.
           - DEBES crear al menos 2 personajes para cada historia.
           - Si el usuario no especifica personajes, crea personajes que sean apropiados para la historia.
           - Asegúrate de que cada personaje tenga al menos un nombre y una descripción.
        
        4. Utiliza el story_id obtenido de la historia creada en el paso 2 para crear los personajes
           con la herramienta creador_de_personajes. Asegúrate de asignar el story_id correcto a cada personaje.
        
        5. Finalmente, utiliza create_contenedor_historia para crear un contenedor que incluya
           tanto la historia como los personajes.
        
        6. Si falta información, usa estos valores predeterminados:
           - título = "Historia sin título"
           - min_jugadores = 1
           - max_jugadores = 4
           - descripción = null
           - géneros = null
           - dificultad = null
           - estado = null
                      
        7. Devuelve EXACTAMENTE el JSON que te proporciona la herramienta, sin añadir texto adicional.
        
        NUNCA hagas preguntas al usuario. Si falta información, usa los valores predeterminados.
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
Por favor, proporciona información para tu historia interactiva.
Por ejemplo: 'El título de la historia será 'El asombroso pedo errante', la descripción sería 'Una aventura mágica en un bosque lleno de criaturas fantásticas y misterios por resolver.' El mínimo de jugadores es 2 y el máximo 3. Incluye personajes como un guerrero, un mago y un pícaro.'

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
                                print("La respuesta no es un JSON válido:")
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
                print(f"Error durante la ejecución: {e}")
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
