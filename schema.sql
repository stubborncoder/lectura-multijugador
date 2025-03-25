-- Schema for Interactive Stories with Multiple Players

-- Tabla HISTORIA
CREATE TABLE historias (
    story_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    generos VARCHAR[] DEFAULT '{}',
    dificultad SMALLINT CHECK (dificultad BETWEEN 1 AND 10),
    imagen_portada VARCHAR(255),
    min_jugadores SMALLINT DEFAULT 1,
    max_jugadores SMALLINT,
    creador_id UUID, -- ID del usuario que creó la historia
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    estado VARCHAR(50) NOT NULL DEFAULT 'borrador' CHECK (estado IN ('borrador', 'publicada', 'archivada')),
    CONSTRAINT check_jugadores CHECK (min_jugadores <= max_jugadores)
);

-- Tabla PARTIDA
CREATE TABLE partidas (
    game_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    historia_id UUID NOT NULL REFERENCES historias(story_id) ON DELETE CASCADE,
    estado VARCHAR(50) NOT NULL DEFAULT 'en_curso' CHECK (estado IN ('en_curso', 'completada', 'abandonada')),
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ultima_actividad TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decisiones JSONB DEFAULT '{}' -- Registro de elecciones (estructura no relacional)
);

-- Tabla JUGADOR
CREATE TABLE jugadores (
    player_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nickname VARCHAR(100) NOT NULL UNIQUE,
    nombre_real VARCHAR(255),
    email VARCHAR(255) NOT NULL UNIQUE,
    estado VARCHAR(50) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'suspendido')),
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ultima_actividad TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    games_played JSONB DEFAULT '[]' -- Array de game_id jugados (estructura no relacional)
);

-- Tabla PERSONAJE (actualizada para coincidir con el modelo Pydantic)
CREATE TABLE personajes (
    personaje_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Mantenemos UUID como en el modelo anterior (character_id)
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    historia_id UUID NOT NULL REFERENCES historias(story_id) ON DELETE CASCADE, -- Nuevo campo como clave externa
    partida_id UUID REFERENCES partidas(game_id) ON DELETE CASCADE, -- Ya no es NOT NULL porque ahora un personaje puede existir sin estar en una partida
    rol VARCHAR(100),
    habilidades TEXT[], -- Lista de habilidades como array de texto
    nivel_poder SMALLINT CHECK (nivel_poder BETWEEN 1 AND 10),
    imagen_perfil VARCHAR(255),
    edad INTEGER,
    origen VARCHAR(255),
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    estado VARCHAR(50) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'eliminado'))
);

-- Tabla NODO
CREATE TABLE nodos (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    personaje_id UUID NOT NULL REFERENCES personajes(personaje_id) ON DELETE CASCADE,
    partida_id UUID NOT NULL REFERENCES partidas(game_id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    contenido TEXT NOT NULL,
    contenido_alternativo JSONB DEFAULT '[]', -- Array de contenido condicional
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('narrativo', 'decision', 'evento', 'final')),
    es_victoria BOOLEAN DEFAULT FALSE,
    posicion_x FLOAT,
    posicion_y FLOAT,
    condiciones_visibilidad JSONB DEFAULT '[]' -- Condiciones para que el nodo sea visible
);

-- Tabla OPCION
CREATE TABLE opciones (
    option_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nodo_id UUID NOT NULL REFERENCES nodos(node_id) ON DELETE CASCADE,
    texto TEXT NOT NULL,
    nodo_destino_id UUID REFERENCES nodos(node_id),
    efectos JSONB DEFAULT '[]', -- Array de cambios en variables
    condiciones_visibilidad JSONB DEFAULT '[]', -- Condiciones para que la opción sea visible
    orden SMALLINT DEFAULT 0
);

-- Tabla TABLA_DECISIONES (para decisiones que afectan a múltiples personajes)
CREATE TABLE tablas_decisiones (
    table_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partida_id UUID NOT NULL REFERENCES partidas(game_id) ON DELETE CASCADE,
    nodo_origen_id UUID NOT NULL REFERENCES nodos(node_id) ON DELETE CASCADE,
    mapeos JSONB NOT NULL DEFAULT '{}', -- Relaciones decisión-resultado
    mapeo_por_defecto JSONB -- Resultado predeterminado
);

-- Tabla VARIABLE
CREATE TABLE variables (
    variable_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    personaje_id UUID NOT NULL REFERENCES personajes(personaje_id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('numero', 'texto', 'booleano', 'objeto')),
    valor_inicial JSONB NOT NULL, -- Valor predeterminado de cualquier tipo
    UNIQUE (personaje_id, nombre) -- Una variable con el mismo nombre no puede repetirse para un personaje
);

-- Tabla de relación entre PARTIDA y JUGADOR
CREATE TABLE partidas_jugadores (
    partida_id UUID REFERENCES partidas(game_id) ON DELETE CASCADE,
    jugador_id UUID REFERENCES jugadores(player_id) ON DELETE CASCADE,
    personaje_id UUID REFERENCES personajes(personaje_id) ON DELETE SET NULL,
    fecha_union TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (partida_id, jugador_id)
);

-- Tabla para el historial de decisiones
CREATE TABLE historial_decisiones (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partida_id UUID NOT NULL REFERENCES partidas(game_id) ON DELETE CASCADE,
    jugador_id UUID NOT NULL REFERENCES jugadores(player_id) ON DELETE CASCADE,
    personaje_id UUID NOT NULL REFERENCES personajes(personaje_id) ON DELETE CASCADE,
    nodo_id UUID NOT NULL REFERENCES nodos(node_id) ON DELETE CASCADE,
    opcion_id UUID NOT NULL REFERENCES opciones(option_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    efectos_aplicados JSONB DEFAULT '[]' -- Registro detallado de los efectos aplicados
);

-- Índices para optimización
CREATE INDEX idx_partidas_historia ON partidas(historia_id);
CREATE INDEX idx_personajes_partida ON personajes(partida_id);
CREATE INDEX idx_nodos_personaje ON nodos(personaje_id);
CREATE INDEX idx_nodos_partida ON nodos(partida_id);
CREATE INDEX idx_opciones_nodo ON opciones(nodo_id);
CREATE INDEX idx_opciones_destino ON opciones(nodo_destino_id);
CREATE INDEX idx_tablas_decisiones_partida ON tablas_decisiones(partida_id);
CREATE INDEX idx_variables_personaje ON variables(personaje_id);
CREATE INDEX idx_partidas_jugadores_partida ON partidas_jugadores(partida_id);
CREATE INDEX idx_partidas_jugadores_jugador ON partidas_jugadores(jugador_id);
CREATE INDEX idx_partidas_jugadores_personaje ON partidas_jugadores(personaje_id);
CREATE INDEX idx_historial_partida ON historial_decisiones(partida_id);
CREATE INDEX idx_historial_jugador ON historial_decisiones(jugador_id);
CREATE INDEX idx_historial_personaje ON historial_decisiones(personaje_id);
CREATE INDEX idx_historial_nodo ON historial_decisiones(nodo_id);

-- Definición de las estructuras JSONB

COMMENT ON COLUMN partidas.decisiones IS 'Estructura: {
  "personaje_id": {
    "nodo_id": {
      "opcion_id": "timestamp",
      "efectos_aplicados": [...]
    }
  }
}';

COMMENT ON COLUMN personajes.estado IS 'Estructura: {
  "variable_nombre": valor,
  "otra_variable": valor
}';

COMMENT ON COLUMN nodos.contenido_alternativo IS 'Estructura: [
  {
    "contenido": "Texto alternativo",
    "condiciones": [
      {"variable": "nombre_variable", "operador": "==", "valor": valor}
    ]
  }
]';

COMMENT ON COLUMN nodos.condiciones_visibilidad IS 'Estructura: [
  {"variable": "nombre_variable", "operador": "==", "valor": valor},
  {"variable": "otra_variable", "operador": ">", "valor": 10}
]';

COMMENT ON COLUMN opciones.efectos IS 'Estructura: [
  {"variable": "nombre_variable", "operador": "=", "valor": nuevo_valor},
  {"variable": "otra_variable", "operador": "+=", "valor": 5}
]';

COMMENT ON COLUMN opciones.condiciones_visibilidad IS 'Estructura: [
  {"variable": "nombre_variable", "operador": "==", "valor": valor},
  {"variable": "otra_variable", "operador": ">", "valor": 10}
]';

COMMENT ON COLUMN tablas_decisiones.mapeos IS 'Estructura: {
  "combinacion_decisiones": {
    "personaje_id1": "nodo_destino_id1",
    "personaje_id2": "nodo_destino_id2"
  }
}';

COMMENT ON COLUMN tablas_decisiones.mapeo_por_defecto IS 'Estructura: {
  "personaje_id1": "nodo_destino_id1",
  "personaje_id2": "nodo_destino_id2"
}';

COMMENT ON COLUMN historial_decisiones.efectos_aplicados IS 'Estructura: [
  {"variable": "nombre_variable", "valor_anterior": valor, "valor_nuevo": nuevo_valor}
]';
