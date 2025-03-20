import streamlit as st
import requests
import json
import logging
import os
import time
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to get API URL from environment or secrets
def get_api_url():
    # First try to get from secrets
    try:
        return st.secrets["api"]["base_url"]
    except Exception as e:
        logger.info(f"Could not get API URL from secrets: {e}")
        # Fallback to environment variable or default
        return os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1")

API_BASE_URL = get_api_url()

# Initialize session state for auth
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "email_confirmed" not in st.session_state:
    st.session_state.email_confirmed = True
if "session_expiry" not in st.session_state:
    st.session_state.session_expiry = None

# Custom CSS for better styling
st.markdown("""
<style>
    /* Custom sidebar header styles */
    .sidebar-header {
        padding: 0.5rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0;
        color: #262730;
    }
    
    .sidebar-user {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #e6e6e6;
    }
    
    .sidebar-email {
        font-size: 0.85rem;
        color: #0068c9;
        max-width: 70%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .sidebar-logout {
        background: none;
        border: none;
        cursor: pointer;
        color: #ff4b4b;
        font-size: 1.1rem;
        padding: 0.25rem;
        border-radius: 4px;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Function to make API requests with authentication
def make_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, debug: bool = True) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/{endpoint}"
    
    headers = {}
    if st.session_state.authenticated and st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    try:
        if debug:
            logger.info(f"Making {method} request to {url}")
            if data:
                logger.info(f"Request data: {data}")
                
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Check if token has expired
        if response.status_code == 401 and st.session_state.authenticated:
            logger.warning("Token expired or invalid, attempting to refresh")
            # Try to refresh the token or log out if that fails
            if not refresh_token():
                logger.error("Token refresh failed, logging out")
                logout()
                st.error("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
                st.rerun()
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if debug:
            logger.error(f"Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                if debug:
                    logger.error(f"Error response: {error_data}")
                return error_data
            except:
                if debug:
                    logger.error(f"Error status code: {e.response.status_code}, text: {e.response.text}")
                return {"detail": f"Error: {e.response.status_code} - {e.response.text}"}
        return {"detail": f"Error de conexión: {str(e)}"}

# Function to refresh the authentication token
def refresh_token() -> bool:
    if not st.session_state.refresh_token:
        return False
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/refresh",
            json={"refresh_token": st.session_state.refresh_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data.get("access_token")
            st.session_state.refresh_token = data.get("refresh_token")
            # Set session expiry to 1 hour from now
            st.session_state.session_expiry = time.time() + 3600
            logger.info("Token refreshed successfully")
            return True
        else:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception during token refresh: {e}")
        return False

# Login function
def login(email: str, password: str) -> bool:
    try:
        logger.info(f"Attempting login for {email}")
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Store authentication data in session state
            st.session_state.authenticated = True
            st.session_state.access_token = data.get("access_token")
            st.session_state.refresh_token = data.get("refresh_token")
            st.session_state.user_info = data.get("user")
            st.session_state.session_expiry = time.time() + 3600  # 1 hour expiry
            
            logger.info(f"Login successful for {email}")
            return True
        elif response.status_code == 401:
            data = response.json()
            if "email_confirmed" in data and not data["email_confirmed"]:
                st.session_state.email_confirmed = False
                logger.warning(f"Email not confirmed for {email}")
                return False
            st.error("Credenciales inválidas")
            logger.warning(f"Invalid credentials for {email}")
            return False
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            logger.error(f"Login error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        logger.error(f"Connection error during login: {e}")
        return False

# Register function
def register(email: str, password: str, nombre: Optional[str] = None, apellidos: Optional[str] = None) -> bool:
    try:
        logger.info(f"Attempting to register user with email: {email}")
        
        # Prepare registration data
        reg_data = {
            "email": email,
            "password": password
        }
        
        if nombre:
            reg_data["nombre"] = nombre
        if apellidos:
            reg_data["apellidos"] = apellidos
            
        logger.info(f"Registration data: {json.dumps(reg_data, indent=2)}")
        
        response = make_request("POST", "auth/register", reg_data)
        
        # Check if registration was successful but email needs confirmation
        if "id" in response and "email_confirmed" in response and response["email_confirmed"] is False:
            logger.info(f"Registration successful but email needs confirmation for: {email}")
            st.success("Registro exitoso. Por favor, revisa tu correo electrónico para confirmar tu cuenta.")
            st.info(response.get("message", "Se ha enviado un correo de confirmación a tu dirección de email."))
            st.session_state.email_confirmed = False
            return True
        
        # Check if registration was successful and no email confirmation is needed
        elif "id" in response and "access_token" in response:
            logger.info(f"Registration successful for: {email}")
            st.success("Registro exitoso.")
            st.session_state.authenticated = True
            st.session_state.user_info = response
            st.session_state.access_token = response["access_token"]
            st.session_state.refresh_token = response["refresh_token"]
            st.session_state.email_confirmed = True
            return True
        else:
            error_msg = response.get('detail', 'No se pudo completar el registro')
            logger.error(f"Registration error: {error_msg}")
            st.error(f"Error al registrarse: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"Exception during registration: {str(e)}")
        st.error(f"Error al registrarse: {str(e)}")
        return False

# Logout function
def logout():
    logger.info("Logging out user")
    # Clear all authentication data from session state
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.session_expiry = None
    st.rerun()

# Check if logout was requested via query parameters
query_params = st.experimental_get_query_params()
if "logout" in query_params and query_params["logout"][0] == "true" and st.session_state.authenticated:
    logout()

# Check if session has expired
if st.session_state.authenticated and st.session_state.session_expiry:
    if time.time() > st.session_state.session_expiry:
        # Try to refresh the token
        if not refresh_token():
            logger.info("Session expired, logging out")
            logout()
            st.error("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
            st.rerun()

# Authentication UI
if not st.session_state.authenticated:
    # App title for non-authenticated users
    st.title("API Tester - Lectura Multijugador")
    
    st.header("Iniciar Sesión / Registrarse")
    
    # Tabs for login and register
    auth_tab = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with auth_tab[0]:
        st.subheader("Iniciar Sesión")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Contraseña", type="password", key="login_password")
        
        if st.button("Iniciar Sesión"):
            if login(login_email, login_password):
                st.success("¡Inicio de sesión exitoso!")
                st.rerun()
            elif not st.session_state.email_confirmed:
                st.warning("Por favor, confirma tu correo electrónico antes de iniciar sesión.")
    
    with auth_tab[1]:
        st.subheader("Registrarse")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Contraseña", type="password", key="reg_password")
        reg_nombre = st.text_input("Nombre (opcional)", key="reg_nombre")
        reg_apellidos = st.text_input("Apellidos (opcional)", key="reg_apellidos")
        
        if st.button("Registrarse"):
            logger.info("Registration button clicked")
            if register(reg_email, reg_password, reg_nombre, reg_apellidos):
                if st.session_state.email_confirmed:
                    st.success("¡Registro exitoso!")
                    st.rerun()
            else:
                st.error("No se pudo completar el registro. Revisa los errores arriba.")
else:
    # User is authenticated, show the main app
    
    # Add app title, user info, and logout to sidebar
    # Use a form submission to trigger logout via query parameter
    user_email = "Usuario"
    if st.session_state.user_info and isinstance(st.session_state.user_info, dict):
        user_email = st.session_state.user_info.get('email', 'Usuario')
    
    sidebar_header = f"""
    <div class="sidebar-header">
        <div class="sidebar-title">API Tester - Lectura Multijugador</div>
        <div class="sidebar-user">
            <div class="sidebar-email">{user_email}</div>
            <a href="?logout=true" class="sidebar-logout">🚪</a>
        </div>
    </div>
    """
    st.sidebar.markdown(sidebar_header, unsafe_allow_html=True)
    
    # Display API URL in development (hidden in production)
    if "localhost" in API_BASE_URL or "127.0.0.1" in API_BASE_URL:
        st.sidebar.info(f"Conectado a API: {API_BASE_URL}")
    
    # Map entity names to API endpoints
    entity_endpoints = {
        "Historias": "historias",
        "Partidas": "partidas",
        "Jugadores": "jugadores",
        "Personajes": "personajes",
        "Nodos": "nodos",
        "Opciones": "opciones",
        "Tablas Decisiones": "tablas-decisiones",
        "Variables": "variables",
        "Partidas-Jugadores": "partidas-jugadores",
        "Historial Decisiones": "historial-decisiones",
        "Autores": "autores"
    }

    # Map entity names to their ID field names
    entity_id_fields = {
        "Historias": "story_id",
        "Partidas": "game_id",
        "Jugadores": "player_id",
        "Personajes": "character_id",
        "Nodos": "node_id",
        "Opciones": "option_id",
        "Tablas Decisiones": "id",
        "Variables": "variable_id",
        "Partidas-Jugadores": "id",
        "Historial Decisiones": "id",
        "Autores": "autor_id"
    }

    # Display the selected entity and operation
    st.header("API Tester - Lectura Multijugador")
    
    # Operation selection
    operation = st.sidebar.selectbox(
        "Selecciona una operación",
        ["Listar Todos", "Buscar por ID", "Crear", "Actualizar", "Eliminar"]
    )

    # Special endpoints
    special_endpoint = st.sidebar.selectbox(
        "Endpoints Especiales",
        ["Ninguno", "Variables por Historia", "Jugadores por Partida", "Partidas por Jugador", 
         "Historial por Partida", "Historial por Jugador", "Historial por Partida y Jugador",
         "Autores por Historia", "Historias por Autor", "Nodos por Historia", "Opciones por Nodo",
         "Actualizar Historia por ID"]
    )
    
    # Entity selection
    entity = st.sidebar.selectbox(
        "Selecciona una entidad",
        ["Historias", "Partidas", "Jugadores", "Personajes", "Nodos", 
         "Opciones", "Tablas Decisiones", "Variables", "Partidas-Jugadores", 
         "Historial Decisiones", "Autores"]
    )

    # Only show regular operations if no special endpoint is selected
    if special_endpoint == "Ninguno":
        # Handle different operations
        if operation == "Listar Todos":
            if st.button("Buscar"):
                with st.spinner("Buscando..."):
                    result = make_request("GET", entity_endpoints[entity])
                    st.json(result)
                
        elif operation == "Buscar por ID":
            entity_id = st.text_input(f"ID de {entity}")
            if st.button("Buscar") and entity_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"{entity_endpoints[entity]}/{entity_id}")
                    st.json(result)
                
        elif operation == "Crear" or operation == "Actualizar":
            # Initialize form data
            form_data = {}
            
            # Entity-specific form fields
            if entity == "Historias":
                form_data["titulo"] = st.text_input("Título")
                form_data["descripcion"] = st.text_area("Descripción")
                form_data["generos"] = st.text_input("Géneros (separados por comas)").split(",") if st.text_input("Géneros (separados por comas)") else []
                form_data["dificultad"] = st.slider("Dificultad", 1, 10, 5)
                form_data["estado"] = st.selectbox("Estado", ["borrador", "publicado", "archivado"])
                form_data["autor_id"] = st.text_input("ID del Autor")
                form_data["publicada"] = st.checkbox("Publicada")
            
            elif entity == "Partidas":
                form_data["historia_id"] = st.text_input("ID de Historia")
                form_data["nombre"] = st.text_input("Nombre")
                form_data["estado"] = st.selectbox("Estado", ["activa", "completada", "abandonada"])
                form_data["fecha_inicio"] = st.date_input("Fecha de Inicio").isoformat()
            
            elif entity == "Jugadores":
                form_data["nickname"] = st.text_input("Nickname")
                form_data["email"] = st.text_input("Email")
                form_data["nombre"] = st.text_input("Nombre")
            
            elif entity == "Personajes":
                form_data["nombre"] = st.text_input("Nombre")
                form_data["descripcion"] = st.text_area("Descripción")
                form_data["historia_id"] = st.text_input("ID de la Historia")
                form_data["atributos"] = st.text_area("Atributos (JSON)", "{}")
                form_data["imagen"] = st.text_input("URL de Imagen")
            
            elif entity == "Nodos":
                form_data["historia_id"] = st.text_input("ID de la Historia")
                form_data["titulo"] = st.text_input("Título")
                form_data["contenido"] = st.text_area("Contenido")
                form_data["es_final"] = st.checkbox("Es Final")
                form_data["orden"] = st.number_input("Orden", min_value=1)
                form_data["imagen"] = st.text_input("URL de Imagen")
                form_data["audio"] = st.text_input("URL de Audio")
                form_data["video"] = st.text_input("URL de Video")
            
            elif entity == "Opciones":
                form_data["nodo_origen_id"] = st.text_input("ID del Nodo Origen")
                form_data["nodo_destino_id"] = st.text_input("ID del Nodo Destino")
                form_data["texto"] = st.text_input("Texto")
                form_data["condicion"] = st.text_area("Condición (opcional)")
                form_data["orden"] = st.number_input("Orden", min_value=1)
                form_data["efectos"] = st.text_area("Efectos (JSON)", "{}")
            
            elif entity == "Tablas Decisiones":
                form_data["historia_id"] = st.text_input("ID de la Historia")
                form_data["nombre"] = st.text_input("Nombre")
                form_data["descripcion"] = st.text_area("Descripción")
                form_data["reglas"] = st.text_area("Reglas (JSON)", "[]")
            
            elif entity == "Variables":
                form_data["historia_id"] = st.text_input("ID de la Historia")
                form_data["nombre"] = st.text_input("Nombre")
                form_data["tipo"] = st.selectbox("Tipo", ["texto", "numero", "booleano"])
                form_data["valor_defecto"] = st.text_input("Valor por Defecto")
                form_data["descripcion"] = st.text_area("Descripción")
            
            elif entity == "Partidas-Jugadores":
                form_data["partida_id"] = st.text_input("ID de la Partida")
                form_data["jugador_id"] = st.text_input("ID del Jugador")
                form_data["personaje_id"] = st.text_input("ID del Personaje")
                form_data["estado"] = st.selectbox("Estado", ["activo", "inactivo", "eliminado"])
                form_data["variables"] = st.text_area("Variables (JSON)", "{}")
            
            elif entity == "Historial Decisiones":
                form_data["partida_id"] = st.text_input("ID de la Partida")
                form_data["jugador_id"] = st.text_input("ID del Jugador")
                form_data["nodo_id"] = st.text_input("ID del Nodo")
                form_data["opcion_id"] = st.text_input("ID de la Opción")
                form_data["timestamp"] = st.text_input("Timestamp (YYYY-MM-DD HH:MM:SS)")
                form_data["variables_antes"] = st.text_area("Variables Antes (JSON)", "{}")
                form_data["variables_despues"] = st.text_area("Variables Después (JSON)", "{}")
            
            elif entity == "Autores":
                form_data["nombre"] = st.text_input("Nombre")
                form_data["apellidos"] = st.text_input("Apellidos")
                form_data["nombre_artistico"] = st.text_input("Nombre Artístico", "")
                form_data["biografia"] = st.text_area("Biografía", "")
                form_data["nacionalidad"] = st.text_input("Nacionalidad", "")
                form_data["email"] = st.text_input("Email", "")
                form_data["website"] = st.text_input("Sitio Web", "")
                form_data["imagen_perfil"] = st.text_input("URL de Imagen de Perfil", "")
                form_data["estado"] = st.selectbox("Estado", ["activo", "inactivo", "eliminado"])
                
                # Redes sociales como campos separados
                st.subheader("Redes Sociales")
                redes_sociales = {}
                redes_sociales["twitter"] = st.text_input("Twitter", "")
                redes_sociales["instagram"] = st.text_input("Instagram", "")
                redes_sociales["facebook"] = st.text_input("Facebook", "")
                redes_sociales["linkedin"] = st.text_input("LinkedIn", "")
                
                # Solo agregar redes sociales si al menos una tiene valor
                if any(redes_sociales.values()):
                    form_data["redes_sociales"] = redes_sociales
            
            # Generic JSON input for other entities or complex data
            json_input = st.text_area("JSON (para datos complejos o entidades no especificadas)", 
                                    value=json.dumps(form_data, indent=2))
            
            try:
                form_data = json.loads(json_input)
            except json.JSONDecodeError:
                st.error("JSON inválido. Por favor, verifica el formato.")
                form_data = {}
                
            if operation == "Crear":
                if st.button("Crear") and form_data:
                    with st.spinner("Creando..."):
                        result = make_request("POST", entity_endpoints[entity], form_data)
                        st.json(result)
            else:  # Actualizar
                entity_id = st.text_input(f"ID de {entity} a actualizar")
                if st.button("Actualizar") and entity_id and form_data:
                    with st.spinner("Actualizando..."):
                        result = make_request("PUT", f"{entity_endpoints[entity]}/{entity_id}", form_data)
                        st.json(result)
                        
        elif operation == "Eliminar":
            entity_id = st.text_input(f"ID de {entity} a eliminar")
            if st.button("Eliminar") and entity_id:
                # Confirmation
                if st.checkbox("Confirmar eliminación"):
                    with st.spinner("Eliminando..."):
                        result = make_request("DELETE", f"{entity_endpoints[entity]}/{entity_id}")
                        st.json(result)
                else:
                    st.warning("Por favor, confirma la eliminación marcando la casilla.")
                    
    # Only show special endpoints section if a special endpoint is selected
    else:
        st.subheader(f"Endpoint Especial: {special_endpoint}")
        
        if special_endpoint == "Variables por Historia":
            historia_id = st.text_input("ID de Historia", key="variables_historia_id")
            if st.button("Buscar", key="variables_historia_button") and historia_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"historias/{historia_id}/variables")
                    st.json(result)
        
        elif special_endpoint == "Jugadores por Partida":
            partida_id = st.text_input("ID de Partida", key="jugadores_partida_id")
            if st.button("Buscar", key="jugadores_partida_button") and partida_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"partidas-jugadores/partida/{partida_id}")
                    st.json(result)
        
        elif special_endpoint == "Partidas por Jugador":
            jugador_id = st.text_input("ID de Jugador", key="partidas_jugador_id")
            if st.button("Buscar", key="partidas_jugador_button") and jugador_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"partidas-jugadores/jugador/{jugador_id}")
                    st.json(result)
        
        elif special_endpoint == "Historial por Partida":
            partida_id = st.text_input("ID de Partida", key="historial_partida_id")
            if st.button("Buscar", key="historial_partida_button") and partida_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"historial-decisiones/partida/{partida_id}")
                    st.json(result)
        
        elif special_endpoint == "Historial por Jugador":
            jugador_id = st.text_input("ID de Jugador", key="historial_jugador_id")
            if st.button("Buscar", key="historial_jugador_button") and jugador_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"historial-decisiones/jugador/{jugador_id}")
                    st.json(result)
        
        elif special_endpoint == "Historial por Partida y Jugador":
            partida_id = st.text_input("ID de Partida", key="historial_partida_jugador_partida_id")
            jugador_id = st.text_input("ID de Jugador", key="historial_partida_jugador_jugador_id")
            if st.button("Buscar", key="historial_partida_jugador_button") and partida_id and jugador_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"historial-decisiones/partida/{partida_id}/jugador/{jugador_id}")
                    st.json(result)
                    
        elif special_endpoint == "Autores por Historia":
            historia_id = st.text_input("ID de Historia", key="autores_historia_id")
            if st.button("Buscar", key="autores_historia_button") and historia_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"autores/historia/{historia_id}")
                    st.json(result)
        
        elif special_endpoint == "Historias por Autor":
            autor_id = st.text_input("ID de Autor", key="historias_autor_id")
            if st.button("Buscar", key="historias_autor_button") and autor_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"autores/{autor_id}/historias")
                    st.json(result)
        
        elif special_endpoint == "Nodos por Historia":
            historia_id = st.text_input("ID de Historia", key="nodos_historia_id")
            if st.button("Buscar", key="nodos_historia_button") and historia_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"historias/{historia_id}/nodos")
                    st.json(result)
        
        elif special_endpoint == "Opciones por Nodo":
            nodo_id = st.text_input("ID de Nodo", key="opciones_nodo_id")
            if st.button("Buscar", key="opciones_nodo_button") and nodo_id:
                with st.spinner("Buscando..."):
                    result = make_request("GET", f"nodos/{nodo_id}/opciones")
                    st.json(result)
        
        elif special_endpoint == "Actualizar Historia por ID":
            historia_id = st.text_input("ID de Historia a actualizar", key="update_historia_id_input")
            
            if historia_id:
                # Primero obtenemos los datos actuales de la historia
                if st.button("Cargar datos de la historia", key="load_historia_button"):
                    with st.spinner("Cargando datos de la historia..."):
                        historia_actual = make_request("GET", f"historias/{historia_id}")
                        if "error" in historia_actual:
                            st.error(f"Error al cargar la historia: {historia_actual.get('error', 'No se encontró la historia')}")
                        else:
                            st.success("Historia cargada correctamente")
                            
                            # Crear formulario con los datos actuales
                            st.subheader("Actualizar Historia")
                            form_data = {}
                            
                            # Campos principales
                            form_data["titulo"] = st.text_input("Título", value=historia_actual.get("titulo", ""), key="update_historia_titulo")
                            form_data["descripcion"] = st.text_area("Descripción", value=historia_actual.get("descripcion", ""), key="update_historia_descripcion")
                            
                            # Géneros (convertir lista a string para el input)
                            generos_str = ", ".join(historia_actual.get("generos", []))
                            generos_input = st.text_input("Géneros (separados por comas)", value=generos_str, key="update_historia_generos")
                            form_data["generos"] = [g.strip() for g in generos_input.split(",")] if generos_input else []
                            
                            # Otros campos
                            form_data["dificultad"] = st.slider("Dificultad", 1, 10, historia_actual.get("dificultad", 5), key="update_historia_dificultad")
                            
                            # Manejar el estado de forma segura
                            estado_options = ["borrador", "publicado", "archivado"]
                            estado_actual = historia_actual.get("estado", "borrador")
                            try:
                                estado_index = estado_options.index(estado_actual)
                            except ValueError:
                                # Si el estado no está en la lista, usar el valor predeterminado
                                logger.warning(f"Estado '{estado_actual}' no reconocido, usando valor predeterminado")
                                estado_index = 0
                                
                            form_data["estado"] = st.selectbox("Estado", 
                                                            estado_options, 
                                                            index=estado_index,
                                                            key="update_historia_estado")
                            
                            # Manejar el autor_id de forma segura
                            autor_id = historia_actual.get("autor_id", "")
                            if autor_id is not None:
                                autor_id_str = str(autor_id)
                            else:
                                autor_id_str = ""
                            form_data["autor_id"] = st.text_input("ID del Autor", value=autor_id_str, key="update_historia_autor_id")
                            
                            # Manejar publicada de forma segura
                            publicada = historia_actual.get("publicada")
                            if publicada is None:
                                publicada = False
                            form_data["publicada"] = st.checkbox("Publicada", value=publicada, key="update_historia_publicada")
                            
                            # Mostrar JSON para edición avanzada
                            st.subheader("Edición Avanzada (JSON)")
                            json_input = st.text_area("JSON", value=json.dumps(form_data, indent=2), key="update_historia_json")
                            
                            try:
                                form_data = json.loads(json_input)
                            except json.JSONDecodeError:
                                st.error("JSON inválido. Por favor, verifica el formato.")
                            
                            # Botón para actualizar
                            if st.button("Actualizar Historia", key="update_historia_submit"):
                                with st.spinner("Actualizando historia..."):
                                    result = make_request("PUT", f"historias/{historia_id}", form_data)
                                    if "error" in result:
                                        st.error(f"Error al actualizar la historia: {result.get('error')}")
                                    else:
                                        st.success("Historia actualizada correctamente")
                                        st.json(result)

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Desarrollado para el proyecto de Lectura Multijugador")
