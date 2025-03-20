# Base de Datos para Historias Interactivas Multijugador

Este proyecto implementa una base de datos PostgreSQL en Supabase para gestionar historias interactivas donde múltiples jugadores pueden participar en una misma narrativa, controlando diferentes personajes y tomando decisiones que afectan el desarrollo de la historia.

## Configuración en Supabase

1. Crea un nuevo proyecto en Supabase (https://supabase.com)
2. Obtén la URL y la API key de tu proyecto
3. Ejecuta el script `supabase_setup.sql` en el SQL Editor de Supabase
4. Configura la autenticación en Supabase habilitando el proveedor de Email/Password

## Estructura de la Base de Datos

El sistema se basa en las siguientes relaciones jerárquicas:

1. Una **HISTORIA** contiene múltiples **PARTIDAS**
2. Una **PARTIDA** incluye múltiples **PERSONAJES**
3. Un **PERSONAJE** tiene múltiples **NODOS** (situaciones narrativas)
4. Un **NODO** ofrece múltiples **OPCIONES** (decisiones posibles)
5. Un **PERSONAJE** posee múltiples **VARIABLES** (atributos o estados)
6. En una **PARTIDA** participan varios **JUGADORES** a través de una tabla de relación
7. Una **HISTORIA** puede tener múltiples **AUTORES** a través de una tabla de relación

## Autenticación y Autorización

El sistema utiliza la autenticación de Supabase para gestionar usuarios y permisos:

1. **Registro e inicio de sesión**: Los usuarios pueden registrarse e iniciar sesión a través de email/contraseña
2. **Tokens JWT**: La API utiliza tokens JWT para autenticar las solicitudes
3. **Protección de endpoints**: Todos los endpoints de la API requieren autenticación
4. **Integración con Streamlit**: La interfaz de Streamlit incluye pantallas de inicio de sesión y registro

### Flujo de autenticación:

1. El usuario se registra o inicia sesión a través de la interfaz de Streamlit
2. Las credenciales se envían a la API, que utiliza Supabase Auth para validarlas
3. Si son válidas, se devuelve un token JWT que se almacena en la sesión de Streamlit
4. Todas las solicitudes posteriores a la API incluyen este token en la cabecera de autorización

## Funciones Principales

El sistema incluye las siguientes funciones:

1. `crear_nueva_partida`: Crea una nueva partida a partir de una historia existente
2. `anadir_jugador_a_partida`: Añade un jugador a una partida y le asigna un personaje
3. `registrar_decision`: Registra una decisión de un jugador en un nodo y aplica sus efectos
4. `actualizar_estado_personaje`: Recalcula el estado de un personaje basado en las decisiones tomadas

## Despliegue en la Nube

El proyecto está diseñado para ser desplegado con una arquitectura de dos componentes desde un único repositorio:

1. **Backend (API FastAPI)**: Desplegado en Render
2. **Frontend (Streamlit)**: Desplegado en Streamlit Community Cloud

### Pasos para el Despliegue

#### 1. Preparación del Repositorio

Asegúrate de que tu repositorio contenga:
- El código de la API en la carpeta `app/`
- El archivo `streamlit_app.py` en la raíz
- Los archivos `requirements.txt`, `render.yaml` y `Procfile` en la raíz
- La carpeta `.streamlit` con el archivo `secrets.toml.example`

#### 2. Despliegue del Backend en Render

1. Crea una cuenta en [Render](https://render.com) si aún no tienes una
2. Desde el Dashboard de Render, selecciona "New" > "Web Service"
3. Conecta tu repositorio de GitHub
4. Configura el servicio con los siguientes parámetros:
   - **Nombre**: lectura-multijugador-api (o el nombre que prefieras)
   - **Entorno**: Python
   - **Rama**: main (o la rama que contenga tu código)
   - **Comando de construcción**: `pip install -r requirements.txt`
   - **Comando de inicio**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. En la sección "Environment", añade las siguientes variables de entorno:
   - `SUPABASE_URL`: La URL de tu proyecto Supabase
   - `SUPABASE_KEY`: La API key de tu proyecto Supabase
6. Haz clic en "Create Web Service"
7. Espera a que el servicio se despliegue y toma nota de la URL (será algo como `https://lectura-multijugador-api.onrender.com`)
8. Verifica que la API funciona accediendo a `https://tu-api.onrender.com/api/v1/docs`

#### 3. Despliegue del Frontend en Streamlit Community Cloud

1. Crea una cuenta en [Streamlit Community Cloud](https://streamlit.io/cloud) si aún no tienes una
2. Desde el Dashboard, haz clic en "New app"
3. Conecta tu repositorio de GitHub
4. Configura la app con los siguientes parámetros:
   - **Repositorio**: Selecciona tu repositorio
   - **Rama**: main (o la rama que contenga tu código)
   - **Archivo principal**: streamlit_app.py
   - **Python version**: 3.9 (o la versión que prefieras)
5. En la sección "Advanced settings" > "Secrets", añade el siguiente contenido:
   ```toml
   [api]
   base_url = "https://tu-api.onrender.com/api/v1"
   ```
   (Reemplaza con la URL real de tu API en Render)
6. Haz clic en "Deploy!"
7. Espera a que la app se despliegue y accede a la URL proporcionada

#### 4. Verificación del Despliegue

1. Accede a tu app de Streamlit
2. Intenta registrar un nuevo usuario
3. Inicia sesión con el usuario creado
4. Prueba las diferentes funcionalidades (crear historias, consultar partidas, etc.)
5. Verifica que los datos se almacenan correctamente en Supabase

### Consideraciones Importantes

- **CORS**: El backend está configurado para aceptar solicitudes desde cualquier origen (`"*"`). En un entorno de producción, deberías restringir esto a solo los orígenes necesarios.
- **Variables de Entorno**: Nunca compartas tus claves de API o credenciales. Utiliza siempre las variables de entorno o secretos proporcionados por las plataformas.
- **Escalado**: Tanto Render como Streamlit Community Cloud ofrecen opciones de escalado si tu aplicación crece.
- **Monitorización**: Configura alertas y monitorización para estar al tanto del estado de tu aplicación.

### Despliegue desde un Monorepo

Este proyecto utiliza un enfoque de monorepo (un solo repositorio para frontend y backend). Las ventajas de este enfoque son:

- **Desarrollo simplificado**: Todos los cambios se realizan en un solo lugar
- **Versionado conjunto**: Frontend y backend evolucionan juntos
- **CI/CD simplificado**: Más fácil de configurar pipelines de integración continua

Para desplegar componentes separados desde un monorepo, cada plataforma está configurada para ejecutar solo la parte relevante del código:
- Render ejecuta solo el backend FastAPI usando el comando especificado
- Streamlit Community Cloud ejecuta solo el frontend Streamlit

## Guía Detallada de Despliegue

### Despliegue del Backend en Render

#### Preparación del Código

1. Asegúrate de que tu repositorio contenga los siguientes archivos en la raíz:
   - `requirements.txt`: Con todas las dependencias necesarias
   - `render.yaml`: Con la configuración para Render
   - `Procfile`: Con el comando para iniciar la aplicación

2. Verifica que el archivo `render.yaml` tenga el siguiente contenido:
   ```yaml
   services:
     - type: web
       name: lectura-multijugador-api
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
       envVars:
         - key: SUPABASE_URL
           sync: false
         - key: SUPABASE_KEY
           sync: false
   ```

3. Verifica que el archivo `Procfile` tenga el siguiente contenido:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. Asegúrate de que el archivo `app/main.py` tenga configurado CORS para permitir solicitudes desde cualquier origen:
   ```python
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Para desarrollo - restringe esto en producción
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

#### Pasos para Desplegar en Render

1. **Crea una cuenta en Render**:
   - Ve a [render.com](https://render.com) y regístrate o inicia sesión
   - Puedes usar tu cuenta de GitHub para un proceso más rápido

2. **Conecta tu repositorio de GitHub**:
   - En el Dashboard de Render, haz clic en "New" y selecciona "Web Service"
   - Selecciona "GitHub" como proveedor de código
   - Autoriza a Render para acceder a tus repositorios si es necesario
   - Busca y selecciona tu repositorio "lectura-multijugador"

3. **Configura el servicio web**:
   - **Nombre**: `lectura-multijugador-api` (o el nombre que prefieras)
   - **Región**: Selecciona la región más cercana a tus usuarios
   - **Rama**: `main` (o la rama que contenga tu código)
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Configura las variables de entorno**:
   - Desplázate hacia abajo hasta la sección "Environment"
   - Haz clic en "Add Environment Variable"
   - Añade las siguientes variables:
     - `SUPABASE_URL`: La URL de tu proyecto Supabase
     - `SUPABASE_KEY`: La API key de tu proyecto Supabase

5. **Opciones avanzadas** (opcional):
   - **Plan**: Selecciona el plan gratuito para empezar
   - **Auto-Deploy**: Mantén activado para despliegues automáticos cuando haya cambios en la rama

6. **Crea el servicio web**:
   - Haz clic en "Create Web Service"
   - Render comenzará a construir y desplegar tu aplicación (esto puede tardar unos minutos)

7. **Verifica el despliegue**:
   - Una vez completado, Render te proporcionará una URL (algo como `https://lectura-multijugador-api.onrender.com`)
   - Accede a `https://tu-url.onrender.com/api/v1/docs` para verificar que la documentación de la API está disponible
   - Prueba algunos endpoints básicos para asegurarte de que todo funciona correctamente

### Despliegue del Frontend en Streamlit Community Cloud

#### Preparación del Código

1. Asegúrate de que tu repositorio contenga:
   - El archivo `streamlit_app.py` en la raíz
   - La carpeta `.streamlit` con la configuración necesaria

2. Verifica que el archivo `streamlit_app.py` esté configurado para obtener la URL de la API desde las variables de entorno o los secretos:
   ```python
   # Get API URL from environment or secrets
   def get_api_url():
       # First check for environment variable
       api_url = os.environ.get("API_BASE_URL")
       
       # Then check Streamlit secrets (for Streamlit Cloud deployment)
       if not api_url and hasattr(st, "secrets") and "api" in st.secrets:
           api_url = st.secrets.api.base_url
           
       # Fall back to default
       return api_url or DEFAULT_API_URL
   ```

3. Crea un archivo `.streamlit/secrets.toml` (no lo subas a GitHub, es solo para desarrollo local) con el siguiente contenido:
   ```toml
   [api]
   base_url = "http://localhost:8000/api/v1"  # Para desarrollo local
   ```

#### Pasos para Desplegar en Streamlit Community Cloud

1. **Crea una cuenta en Streamlit Community Cloud**:
   - Ve a [streamlit.io/cloud](https://streamlit.io/cloud) y regístrate o inicia sesión
   - Puedes usar tu cuenta de GitHub para un proceso más rápido

2. **Conecta tu repositorio de GitHub**:
   - En el Dashboard, haz clic en "New app"
   - Autoriza a Streamlit para acceder a tus repositorios si es necesario
   - Busca y selecciona tu repositorio "lectura-multijugador"

3. **Configura la aplicación**:
   - **Repositorio**: Selecciona tu repositorio "lectura-multijugador"
   - **Rama**: `main` (o la rama que contenga tu código)
   - **Archivo principal**: `streamlit_app.py`
   - **Python version**: Selecciona la versión que estás usando (recomendado 3.9 o superior)

4. **Configura los secretos**:
   - Haz clic en "Advanced settings"
   - En la sección "Secrets", añade el siguiente contenido:
   ```toml
   [api]
   base_url = "https://tu-api-en-render.onrender.com/api/v1"
   ```
   (Reemplaza con la URL real de tu API en Render que obtuviste en el paso anterior)

5. **Despliega la aplicación**:
   - Haz clic en "Deploy!"
   - Streamlit comenzará a construir y desplegar tu aplicación (esto puede tardar unos minutos)

6. **Verifica el despliegue**:
   - Una vez completado, Streamlit te proporcionará una URL (algo como `https://lectura-multijugador.streamlit.app`)
   - Accede a la URL para verificar que la aplicación está funcionando correctamente
   - Intenta registrar un usuario y realizar algunas operaciones básicas

### Conexión entre Frontend y Backend

1. **Verifica la comunicación**:
   - Abre la consola del navegador mientras usas la aplicación Streamlit
   - Verifica que las solicitudes a la API se están realizando correctamente
   - Comprueba que no hay errores CORS

2. **Solución de problemas comunes**:
   - **Error CORS**: Asegúrate de que el backend tiene configurado correctamente CORS para permitir solicitudes desde el dominio de Streamlit
   - **Error de conexión**: Verifica que la URL de la API en los secretos de Streamlit es correcta
   - **Error de autenticación**: Asegúrate de que las credenciales de Supabase están configuradas correctamente en Render

3. **Monitorización**:
   - Configura alertas en Render para recibir notificaciones sobre problemas en el backend
   - Revisa los logs de Streamlit y Render regularmente para detectar problemas

### Actualización de la Aplicación

1. **Actualización del Backend**:
   - Realiza los cambios necesarios en el código
   - Haz commit y push a GitHub
   - Render detectará los cambios y desplegará automáticamente la nueva versión

2. **Actualización del Frontend**:
   - Realiza los cambios necesarios en el código
   - Haz commit y push a GitHub
   - Streamlit detectará los cambios y desplegará automáticamente la nueva versión

3. **Cambios que requieren actualización de secretos o variables de entorno**:
   - Actualiza las variables de entorno en Render si es necesario
   - Actualiza los secretos en Streamlit Community Cloud si es necesario

## Desarrollo Local

### Configuración del Entorno

1. Clona este repositorio
2. Instala las dependencias usando UV (recomendado) o pip:
   ```
   uv pip install -r requirements.txt
   ```
3. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```
   SUPABASE_URL=tu_url_de_supabase
   SUPABASE_KEY=tu_api_key_de_supabase
   ```

### Ejecución de la API

Para iniciar el servidor de desarrollo:

```
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`.

### Estructura de la API

La API está organizada en módulos por entidad, cada uno con sus propios endpoints CRUD:

#### Historias
- `GET /api/v1/historias/`: Obtener todas las historias
- `GET /api/v1/historias/{story_id}`: Obtener una historia por ID
- `POST /api/v1/historias/`: Crear una nueva historia
- `PUT /api/v1/historias/{story_id}`: Actualizar una historia existente
- `DELETE /api/v1/historias/{story_id}`: Eliminar una historia

#### Partidas
- `GET /api/v1/partidas/`: Obtener todas las partidas
- `GET /api/v1/partidas/{game_id}`: Obtener una partida por ID
- `POST /api/v1/partidas/`: Crear una nueva partida
- `PUT /api/v1/partidas/{game_id}`: Actualizar una partida existente
- `DELETE /api/v1/partidas/{game_id}`: Eliminar una partida

#### Jugadores
- `GET /api/v1/jugadores/`: Obtener todos los jugadores
- `GET /api/v1/jugadores/{player_id}`: Obtener un jugador por ID
- `POST /api/v1/jugadores/`: Crear un nuevo jugador
- `PUT /api/v1/jugadores/{player_id}`: Actualizar un jugador existente
- `DELETE /api/v1/jugadores/{player_id}`: Eliminar un jugador

#### Personajes
- `GET /api/v1/personajes/`: Obtener todos los personajes
- `GET /api/v1/personajes/{character_id}`: Obtener un personaje por ID
- `POST /api/v1/personajes/`: Crear un nuevo personaje
- `PUT /api/v1/personajes/{character_id}`: Actualizar un personaje existente
- `DELETE /api/v1/personajes/{character_id}`: Eliminar un personaje

#### Nodos
- `GET /api/v1/nodos/`: Obtener todos los nodos
- `GET /api/v1/nodos/{node_id}`: Obtener un nodo por ID
- `POST /api/v1/nodos/`: Crear un nuevo nodo
- `PUT /api/v1/nodos/{node_id}`: Actualizar un nodo existente
- `DELETE /api/v1/nodos/{node_id}`: Eliminar un nodo

#### Opciones
- `GET /api/v1/opciones/`: Obtener todas las opciones
- `GET /api/v1/opciones/{option_id}`: Obtener una opción por ID
- `POST /api/v1/opciones/`: Crear una nueva opción
- `PUT /api/v1/opciones/{option_id}`: Actualizar una opción existente
- `DELETE /api/v1/opciones/{option_id}`: Eliminar una opción

#### Tablas de Decisiones
- `GET /api/v1/tablas-decisiones/`: Obtener todas las tablas de decisiones
- `GET /api/v1/tablas-decisiones/{id}`: Obtener una tabla de decisiones por ID
- `POST /api/v1/tablas-decisiones/`: Crear una nueva tabla de decisiones
- `PUT /api/v1/tablas-decisiones/{id}`: Actualizar una tabla de decisiones existente
- `DELETE /api/v1/tablas-decisiones/{id}`: Eliminar una tabla de decisiones

#### Variables
- `GET /api/v1/variables/`: Obtener todas las variables
- `GET /api/v1/variables/{variable_id}`: Obtener una variable por ID
- `GET /api/v1/variables/historia/{historia_id}`: Obtener variables por historia
- `POST /api/v1/variables/`: Crear una nueva variable
- `PUT /api/v1/variables/{variable_id}`: Actualizar una variable existente
- `DELETE /api/v1/variables/{variable_id}`: Eliminar una variable

#### Partidas-Jugadores
- `GET /api/v1/partidas-jugadores/`: Obtener todas las relaciones partida-jugador
- `GET /api/v1/partidas-jugadores/{id}`: Obtener una relación por ID
- `GET /api/v1/partidas-jugadores/partida/{partida_id}`: Obtener jugadores de una partida
- `GET /api/v1/partidas-jugadores/jugador/{jugador_id}`: Obtener partidas de un jugador
- `POST /api/v1/partidas-jugadores/`: Crear una nueva relación partida-jugador
- `PUT /api/v1/partidas-jugadores/{id}`: Actualizar una relación existente
- `DELETE /api/v1/partidas-jugadores/{id}`: Eliminar una relación

#### Historial de Decisiones
- `GET /api/v1/historial-decisiones/`: Obtener todo el historial de decisiones
- `GET /api/v1/historial-decisiones/{id}`: Obtener un registro de historial por ID
- `GET /api/v1/historial-decisiones/partida/{partida_id}`: Obtener historial por partida
- `GET /api/v1/historial-decisiones/jugador/{jugador_id}`: Obtener historial por jugador
- `GET /api/v1/historial-decisiones/partida/{partida_id}/jugador/{jugador_id}`: Obtener historial filtrado
- `POST /api/v1/historial-decisiones/`: Crear un nuevo registro de historial
- `PUT /api/v1/historial-decisiones/{id}`: Actualizar un registro existente
- `DELETE /api/v1/historial-decisiones/{id}`: Eliminar un registro

#### Autores
- `GET /api/v1/autores/`: Obtener todos los autores
- `GET /api/v1/autores/{autor_id}`: Obtener un autor por ID
- `POST /api/v1/autores/`: Crear un nuevo autor
- `PUT /api/v1/autores/{autor_id}`: Actualizar un autor existente
- `DELETE /api/v1/autores/{autor_id}`: Eliminar un autor
- `GET /api/v1/autores/historia/{historia_id}`: Obtener todos los autores asociados a una historia
- `GET /api/v1/autores/{autor_id}/historias`: Obtener todas las historias asociadas a un autor
- `POST /api/v1/autores/historia/{historia_id}/autor/{autor_id}`: Asociar un autor a una historia
- `DELETE /api/v1/autores/historia/{historia_id}/autor/{autor_id}`: Eliminar la asociación entre un autor y una historia

### Validación de Datos

Todos los endpoints utilizan modelos Pydantic para validar los datos de entrada y salida, garantizando la integridad de los datos y proporcionando mensajes de error claros cuando la validación falla.

### Seguridad

La API utiliza la autenticación proporcionada por Supabase y respeta las políticas de seguridad RLS configuradas en la base de datos.

## Ejemplo de Uso de la API

### Crear una nueva historia
```python
import requests
import json

url = "http://localhost:8000/api/v1/historias/"
payload = {
    "titulo": "La mansión misteriosa",
    "descripcion": "Una historia de misterio y terror",
    "autor": "Juan Pérez",
    "genero": "Misterio",
    "estado": "publicado"
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print(response.json())
```

### Obtener todas las partidas de un jugador
```python
import requests

jugador_id = "id_del_jugador"
url = f"http://localhost:8000/api/v1/partidas-jugadores/jugador/{jugador_id}"

response = requests.get(url)
print(response.json())

```

## Ejecutando Consultas Importantes

### Obtener todos los nodos de un personaje en una partida
```sql
SELECT * FROM nodos
WHERE personaje_id = 'id_del_personaje' AND partida_id = 'id_de_la_partida';
```

### Obtener el historial de decisiones de un jugador en una partida
```sql
SELECT h.*, o.texto as opcion_texto, n.titulo as nodo_titulo
FROM historial_decisiones h
JOIN opciones o ON h.opcion_id = o.option_id
JOIN nodos n ON h.nodo_id = n.node_id
WHERE h.jugador_id = 'id_del_jugador' AND h.partida_id = 'id_de_la_partida'
ORDER BY h.timestamp;
```

### Calcular el estado actual de un personaje
```sql
SELECT actualizar_estado_personaje('id_del_personaje');
```

## API REST con FastAPI

Este proyecto implementa una API REST completa utilizando FastAPI para interactuar con la base de datos Supabase. La API proporciona endpoints CRUD (Crear, Leer, Actualizar, Eliminar) para todas las entidades del sistema.
