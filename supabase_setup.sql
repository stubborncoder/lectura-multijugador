-- Script para generar la base de datos en Supabase
-- URL y API key se añadirán manualmente

-- Habilitar las extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Configuración inicial
ALTER DATABASE postgres SET timezone TO 'UTC';

-- Esquema principal
CREATE SCHEMA IF NOT EXISTS public;

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

-- Tabla PERSONAJE
CREATE TABLE personajes (
    character_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partida_id UUID NOT NULL REFERENCES partidas(game_id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    estado JSONB DEFAULT '{}' -- Estado actual del personaje (valores de variables)
);

-- Tabla NODO
CREATE TABLE nodos (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    personaje_id UUID NOT NULL REFERENCES personajes(character_id) ON DELETE CASCADE,
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
    personaje_id UUID NOT NULL REFERENCES personajes(character_id) ON DELETE CASCADE,
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
    personaje_id UUID REFERENCES personajes(character_id) ON DELETE SET NULL,
    fecha_union TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (partida_id, jugador_id)
);

-- Tabla para el historial de decisiones
CREATE TABLE historial_decisiones (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partida_id UUID NOT NULL REFERENCES partidas(game_id) ON DELETE CASCADE,
    jugador_id UUID NOT NULL REFERENCES jugadores(player_id) ON DELETE CASCADE,
    personaje_id UUID NOT NULL REFERENCES personajes(character_id) ON DELETE CASCADE,
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

-- Tabla AUTOR
CREATE TABLE autores (
    autor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(255) NOT NULL,
    apellidos VARCHAR(255),
    nombre_artistico VARCHAR(255),
    biografia TEXT,
    fecha_nacimiento DATE,
    nacionalidad VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    website VARCHAR(255),
    redes_sociales JSONB DEFAULT '{}',
    imagen_perfil VARCHAR(255),
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    usuario_id UUID, -- Opcional: ID del usuario si el autor tiene cuenta en el sistema
    estado VARCHAR(50) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'eliminado'))
);

-- Comentario sobre la estructura JSONB para redes sociales
COMMENT ON COLUMN autores.redes_sociales IS 'Estructura: {
  "twitter": "https://twitter.com/username",
  "instagram": "https://instagram.com/username",
  "facebook": "https://facebook.com/username",
  "linkedin": "https://linkedin.com/in/username"
}';

-- Índice para búsquedas por nombre
CREATE INDEX idx_autores_nombre ON autores(nombre);
CREATE INDEX idx_autores_nombre_artistico ON autores(nombre_artistico);

-- Tabla de relación entre HISTORIA y AUTOR (permite múltiples autores por historia)
CREATE TABLE historias_autores (
    historia_id UUID REFERENCES historias(story_id) ON DELETE CASCADE,
    autor_id UUID REFERENCES autores(autor_id) ON DELETE CASCADE,
    rol VARCHAR(100) DEFAULT 'autor principal', -- Ej: autor principal, coautor, editor, etc.
    porcentaje_contribucion SMALLINT CHECK (porcentaje_contribucion BETWEEN 0 AND 100),
    fecha_asignacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (historia_id, autor_id)
);

-- Índices para optimización
CREATE INDEX idx_historias_autores_historia ON historias_autores(historia_id);
CREATE INDEX idx_historias_autores_autor ON historias_autores(autor_id);

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

-- =============================================
-- FUNCIONES DE UTILIDAD
-- =============================================

-- 1. Función para crear una nueva partida a partir de una historia
CREATE OR REPLACE FUNCTION crear_nueva_partida(
    p_historia_id UUID,
    p_creador_id UUID
) RETURNS UUID AS $$
DECLARE
    v_partida_id UUID;
    v_min_jugadores SMALLINT;
    v_max_jugadores SMALLINT;
BEGIN
    -- Obtener información de la historia
    SELECT min_jugadores, max_jugadores 
    INTO v_min_jugadores, v_max_jugadores
    FROM historias 
    WHERE story_id = p_historia_id;
    
    -- Crear nueva partida
    INSERT INTO partidas (historia_id, estado)
    VALUES (p_historia_id, 'en_curso')
    RETURNING game_id INTO v_partida_id;
    
    -- Registrar al creador como primer jugador
    INSERT INTO partidas_jugadores (partida_id, jugador_id)
    VALUES (v_partida_id, p_creador_id);
    
    -- Actualizar el historial de juegos del jugador
    UPDATE jugadores
    SET games_played = games_played || jsonb_build_array(v_partida_id)
    WHERE player_id = p_creador_id;
    
    RETURN v_partida_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Función para añadir un jugador a una partida existente y asignarle un personaje
CREATE OR REPLACE FUNCTION anadir_jugador_a_partida(
    p_partida_id UUID,
    p_jugador_id UUID,
    p_personaje_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_max_jugadores SMALLINT;
    v_jugadores_actuales INT;
BEGIN
    -- Verificar si la partida existe y está en curso
    IF NOT EXISTS (SELECT 1 FROM partidas WHERE game_id = p_partida_id AND estado = 'en_curso') THEN
        RAISE EXCEPTION 'La partida no existe o no está en curso';
    END IF;
    
    -- Verificar si el personaje existe y pertenece a la partida
    IF NOT EXISTS (SELECT 1 FROM personajes WHERE character_id = p_personaje_id AND partida_id = p_partida_id) THEN
        RAISE EXCEPTION 'El personaje no existe o no pertenece a esta partida';
    END IF;
    
    -- Verificar si el personaje ya está asignado
    IF EXISTS (SELECT 1 FROM partidas_jugadores WHERE personaje_id = p_personaje_id) THEN
        RAISE EXCEPTION 'Este personaje ya está asignado a otro jugador';
    END IF;
    
    -- Verificar si el jugador ya está en la partida
    IF EXISTS (SELECT 1 FROM partidas_jugadores WHERE partida_id = p_partida_id AND jugador_id = p_jugador_id) THEN
        -- Actualizar el personaje asignado
        UPDATE partidas_jugadores
        SET personaje_id = p_personaje_id
        WHERE partida_id = p_partida_id AND jugador_id = p_jugador_id;
    ELSE
        -- Verificar límite de jugadores
        SELECT h.max_jugadores INTO v_max_jugadores
        FROM partidas p
        JOIN historias h ON p.historia_id = h.story_id
        WHERE p.game_id = p_partida_id;
        
        SELECT COUNT(*) INTO v_jugadores_actuales
        FROM partidas_jugadores
        WHERE partida_id = p_partida_id;
        
        IF v_jugadores_actuales >= v_max_jugadores THEN
            RAISE EXCEPTION 'La partida ha alcanzado el número máximo de jugadores';
        END IF;
        
        -- Añadir jugador a la partida
        INSERT INTO partidas_jugadores (partida_id, jugador_id, personaje_id)
        VALUES (p_partida_id, p_jugador_id, p_personaje_id);
        
        -- Actualizar el historial de juegos del jugador
        UPDATE jugadores
        SET games_played = games_played || jsonb_build_array(p_partida_id)
        WHERE player_id = p_jugador_id;
    END IF;
    
    -- Actualizar timestamp de última actividad
    UPDATE partidas
    SET ultima_actividad = NOW()
    WHERE game_id = p_partida_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Función para registrar una decisión de un jugador en un nodo
CREATE OR REPLACE FUNCTION registrar_decision(
    p_partida_id UUID,
    p_jugador_id UUID,
    p_personaje_id UUID,
    p_nodo_id UUID,
    p_opcion_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_efectos JSONB;
    v_estado_actual JSONB;
    v_variable_nombre TEXT;
    v_operador TEXT;
    v_valor JSONB;
    v_valor_actual JSONB;
    v_valor_nuevo JSONB;
    v_efectos_aplicados JSONB = '[]'::JSONB;
    v_timestamp TIMESTAMP WITH TIME ZONE = NOW();
BEGIN
    -- Verificar permisos
    IF NOT EXISTS (
        SELECT 1 FROM partidas_jugadores 
        WHERE partida_id = p_partida_id 
        AND jugador_id = p_jugador_id 
        AND personaje_id = p_personaje_id
    ) THEN
        RAISE EXCEPTION 'El jugador no tiene permiso para controlar este personaje';
    END IF;
    
    -- Verificar que la opción pertenece al nodo
    IF NOT EXISTS (
        SELECT 1 FROM opciones 
        WHERE option_id = p_opcion_id 
        AND nodo_id = p_nodo_id
    ) THEN
        RAISE EXCEPTION 'La opción no pertenece a este nodo';
    END IF;
    
    -- Obtener efectos de la opción
    SELECT efectos INTO v_efectos
    FROM opciones
    WHERE option_id = p_opcion_id;
    
    -- Obtener estado actual del personaje
    SELECT estado INTO v_estado_actual
    FROM personajes
    WHERE character_id = p_personaje_id;
    
    -- Aplicar efectos
    FOR i IN 0..jsonb_array_length(v_efectos) - 1 LOOP
        v_variable_nombre := v_efectos->i->>'variable';
        v_operador := v_efectos->i->>'operador';
        v_valor := v_efectos->i->'valor';
        
        -- Obtener valor actual de la variable
        v_valor_actual := v_estado_actual->v_variable_nombre;
        
        -- Aplicar operación según el tipo
        CASE v_operador
            WHEN '=' THEN
                v_valor_nuevo := v_valor;
            WHEN '+=' THEN
                IF v_valor_actual IS NULL THEN
                    v_valor_nuevo := v_valor;
                ELSE
                    v_valor_nuevo := to_jsonb(v_valor_actual::TEXT::NUMERIC + v_valor::TEXT::NUMERIC);
                END IF;
            WHEN '-=' THEN
                IF v_valor_actual IS NULL THEN
                    v_valor_nuevo := to_jsonb(0 - v_valor::TEXT::NUMERIC);
                ELSE
                    v_valor_nuevo := to_jsonb(v_valor_actual::TEXT::NUMERIC - v_valor::TEXT::NUMERIC);
                END IF;
            WHEN '*=' THEN
                IF v_valor_actual IS NULL THEN
                    v_valor_nuevo := to_jsonb(0);
                ELSE
                    v_valor_nuevo := to_jsonb(v_valor_actual::TEXT::NUMERIC * v_valor::TEXT::NUMERIC);
                END IF;
            WHEN '/=' THEN
                IF v_valor_actual IS NULL OR v_valor::TEXT::NUMERIC = 0 THEN
                    v_valor_nuevo := v_valor_actual;
                ELSE
                    v_valor_nuevo := to_jsonb(v_valor_actual::TEXT::NUMERIC / v_valor::TEXT::NUMERIC);
                END IF;
            ELSE
                v_valor_nuevo := v_valor;
        END CASE;
        
        -- Actualizar estado
        v_estado_actual := jsonb_set(
            CASE WHEN v_estado_actual IS NULL THEN '{}'::JSONB ELSE v_estado_actual END,
            ARRAY[v_variable_nombre],
            v_valor_nuevo
        );
        
        -- Registrar efecto aplicado
        v_efectos_aplicados := v_efectos_aplicados || jsonb_build_object(
            'variable', v_variable_nombre,
            'valor_anterior', v_valor_actual,
            'valor_nuevo', v_valor_nuevo
        );
    END LOOP;
    
    -- Actualizar estado del personaje
    UPDATE personajes
    SET estado = v_estado_actual
    WHERE character_id = p_personaje_id;
    
    -- Registrar decisión en historial
    INSERT INTO historial_decisiones (
        partida_id, jugador_id, personaje_id, nodo_id, opcion_id, timestamp, efectos_aplicados
    ) VALUES (
        p_partida_id, p_jugador_id, p_personaje_id, p_nodo_id, p_opcion_id, v_timestamp, v_efectos_aplicados
    );
    
    -- Actualizar registro de decisiones en la partida
    UPDATE partidas
    SET 
        decisiones = jsonb_set(
            CASE WHEN decisiones IS NULL THEN '{}'::JSONB ELSE decisiones END,
            ARRAY[p_personaje_id::TEXT, p_nodo_id::TEXT, p_opcion_id::TEXT],
            to_jsonb(v_timestamp)
        ),
        ultima_actividad = v_timestamp
    WHERE game_id = p_partida_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Función para actualizar el estado de un personaje basado en efectos de decisión
CREATE OR REPLACE FUNCTION actualizar_estado_personaje(
    p_personaje_id UUID
) RETURNS JSONB AS $$
DECLARE
    v_estado_inicial JSONB = '{}'::JSONB;
    v_estado_actual JSONB;
    v_historial RECORD;
    v_efecto JSONB;
    v_variable_nombre TEXT;
    v_valor_nuevo JSONB;
BEGIN
    -- Obtener valores iniciales de las variables
    FOR v_historial IN (
        SELECT nombre, valor_inicial
        FROM variables
        WHERE personaje_id = p_personaje_id
    ) LOOP
        v_estado_inicial := jsonb_set(
            v_estado_inicial,
            ARRAY[v_historial.nombre],
            v_historial.valor_inicial
        );
    END LOOP;
    
    v_estado_actual := v_estado_inicial;
    
    -- Aplicar efectos de todas las decisiones en orden cronológico
    FOR v_historial IN (
        SELECT efectos_aplicados
        FROM historial_decisiones
        WHERE personaje_id = p_personaje_id
        ORDER BY timestamp
    ) LOOP
        FOR i IN 0..jsonb_array_length(v_historial.efectos_aplicados) - 1 LOOP
            v_efecto := v_historial.efectos_aplicados->i;
            v_variable_nombre := v_efecto->>'variable';
            v_valor_nuevo := v_efecto->'valor_nuevo';
            
            v_estado_actual := jsonb_set(
                v_estado_actual,
                ARRAY[v_variable_nombre],
                v_valor_nuevo
            );
        END LOOP;
    END LOOP;
    
    -- Actualizar estado del personaje
    UPDATE personajes
    SET estado = v_estado_actual
    WHERE character_id = p_personaje_id;
    
    RETURN v_estado_actual;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Función para obtener el siguiente nodo basado en la decisión
CREATE OR REPLACE FUNCTION obtener_siguiente_nodo(
    p_partida_id UUID,
    p_nodo_id UUID,
    p_opcion_id UUID
) RETURNS UUID AS $$
DECLARE
    v_nodo_destino_id UUID;
    v_tabla_decisiones_id UUID;
    v_mapeos JSONB;
    v_mapeo_por_defecto JSONB;
    v_decisiones_clave TEXT;
    v_personaje_id UUID;
BEGIN
    -- Primero intentar obtener el destino directo desde la opción
    SELECT nodo_destino_id INTO v_nodo_destino_id
    FROM opciones
    WHERE option_id = p_opcion_id;
    
    IF v_nodo_destino_id IS NOT NULL THEN
        RETURN v_nodo_destino_id;
    END IF;
    
    -- Si no hay destino directo, buscar en tablas de decisiones
    SELECT table_id, mapeos, mapeo_por_defecto INTO v_tabla_decisiones_id, v_mapeos, v_mapeo_por_defecto
    FROM tablas_decisiones
    WHERE partida_id = p_partida_id AND nodo_origen_id = p_nodo_id;
    
    IF v_tabla_decisiones_id IS NULL THEN
        RETURN NULL; -- No hay tabla de decisiones para este nodo
    END IF;
    
    -- Obtener el personaje que tomó la decisión
    SELECT personaje_id INTO v_personaje_id
    FROM historial_decisiones
    WHERE partida_id = p_partida_id AND nodo_id = p_nodo_id AND opcion_id = p_opcion_id
    ORDER BY timestamp DESC
    LIMIT 1;
    
    -- Construir clave para buscar en mapeos
    -- Aquí se implementaría la lógica para combinar decisiones de múltiples personajes
    -- Por simplicidad, usamos solo la decisión actual
    v_decisiones_clave := p_opcion_id::TEXT;
    
    -- Buscar destino en mapeos
    IF v_mapeos ? v_decisiones_clave THEN
        v_nodo_destino_id := (v_mapeos->v_decisiones_clave->>v_personaje_id::TEXT)::UUID;
    END IF;
    
    -- Si no se encuentra en mapeos, usar mapeo por defecto
    IF v_nodo_destino_id IS NULL AND v_mapeo_por_defecto IS NOT NULL THEN
        v_nodo_destino_id := (v_mapeo_por_defecto->>v_personaje_id::TEXT)::UUID;
    END IF;
    
    RETURN v_nodo_destino_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- POLÍTICAS DE SEGURIDAD RLS
-- =============================================

-- Habilitar RLS en todas las tablas
ALTER TABLE historias ENABLE ROW LEVEL SECURITY;
ALTER TABLE partidas ENABLE ROW LEVEL SECURITY;
ALTER TABLE jugadores ENABLE ROW LEVEL SECURITY;
ALTER TABLE personajes ENABLE ROW LEVEL SECURITY;
ALTER TABLE nodos ENABLE ROW LEVEL SECURITY;
ALTER TABLE opciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE tablas_decisiones ENABLE ROW LEVEL SECURITY;
ALTER TABLE variables ENABLE ROW LEVEL SECURITY;
ALTER TABLE partidas_jugadores ENABLE ROW LEVEL SECURITY;
ALTER TABLE historial_decisiones ENABLE ROW LEVEL SECURITY;
ALTER TABLE autores ENABLE ROW LEVEL SECURITY;
ALTER TABLE historias_autores ENABLE ROW LEVEL SECURITY;

-- Política: Un jugador solo debe poder ver las partidas en las que participa
CREATE POLICY partidas_visibles_para_jugadores ON partidas
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM partidas_jugadores
            WHERE partida_id = game_id AND jugador_id = auth.uid()
        )
    );

-- Política: Un jugador solo debe poder tomar decisiones para su personaje asignado
CREATE POLICY personajes_controlables_por_jugador ON personajes
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM partidas_jugadores
            WHERE personaje_id = character_id AND jugador_id = auth.uid()
        )
    );

-- Política: Las historias en estado 'borrador' solo son visibles para su creador
CREATE POLICY historias_borrador_solo_creador ON historias
    FOR SELECT
    USING (
        estado != 'borrador' OR creador_id = auth.uid()
    );

-- Política: Historias publicadas son visibles para todos
CREATE POLICY historias_publicadas_visibles ON historias
    FOR SELECT
    USING (
        estado = 'publicada'
    );

-- Política: Solo el creador puede modificar sus historias
CREATE POLICY historias_modificables_por_creador ON historias
    FOR UPDATE
    USING (
        creador_id = auth.uid()
    );

-- Política: Nodos visibles solo para jugadores en la partida
CREATE POLICY nodos_visibles_para_jugadores ON nodos
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM partidas_jugadores
            WHERE partida_id = nodos.partida_id AND jugador_id = auth.uid()
        )
    );

-- Política: Opciones visibles solo para jugadores en la partida
CREATE POLICY opciones_visibles_para_jugadores ON opciones
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM nodos n
            JOIN partidas_jugadores pj ON n.partida_id = pj.partida_id
            WHERE n.node_id = opciones.nodo_id AND pj.jugador_id = auth.uid()
        )
    );

-- Política: Historial de decisiones visible solo para jugadores en la partida
CREATE POLICY historial_visible_para_jugadores ON historial_decisiones
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM partidas_jugadores
            WHERE partida_id = historial_decisiones.partida_id AND jugador_id = auth.uid()
        )
    );

-- Política: Autores visibles para todos
CREATE POLICY autores_visibles_para_todos ON autores
    FOR SELECT
    USING (
        estado = 'activo'
    );

-- Política: Autores editables solo por el usuario que los creó
CREATE POLICY autores_edicion_por_usuario ON autores
    FOR UPDATE
    USING (
        usuario_id = auth.uid()
    );

-- Política: Autores eliminables solo por el usuario que los creó
CREATE POLICY autores_eliminacion_por_usuario ON autores
    FOR DELETE
    USING (
        usuario_id = auth.uid()
    );

-- Política: Historias-autores visibles para todos
CREATE POLICY historias_autores_visibles_para_todos ON historias_autores
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM historias h
            WHERE h.story_id = historia_id
            AND (h.estado != 'borrador' OR h.creador_id = auth.uid())
        )
    );

-- Política: Historias-autores editables solo por el creador de la historia
CREATE POLICY historias_autores_edicion_por_creador ON historias_autores
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM historias h
            WHERE h.story_id = historia_id
            AND h.creador_id = auth.uid()
        )
    );

-- =============================================
-- DATOS DE EJEMPLO
-- =============================================

-- Insertar historia de ejemplo
INSERT INTO historias (
    titulo, 
    descripcion, 
    generos, 
    dificultad, 
    imagen_portada, 
    min_jugadores, 
    max_jugadores, 
    creador_id, 
    estado
) VALUES (
    'La mansión misteriosa',
    'Un grupo de amigos decide pasar la noche en una antigua mansión con fama de estar embrujada. Lo que comienza como una aventura divertida pronto se convierte en una pesadilla cuando extraños sucesos comienzan a ocurrir.',
    ARRAY['Terror', 'Misterio', 'Aventura'],
    7,
    'https://example.com/images/mansion.jpg',
    2,
    4,
    '00000000-0000-0000-0000-000000000001', -- ID del creador (ajustar según tu sistema de autenticación)
    'publicada'
);

-- Insertar jugadores de ejemplo
INSERT INTO jugadores (player_id, nickname, nombre_real, email) VALUES
('00000000-0000-0000-0000-000000000001', 'GameMaster', 'Admin', 'admin@example.com'),
('00000000-0000-0000-0000-000000000002', 'Explorer1', 'Juan Pérez', 'juan@example.com'),
('00000000-0000-0000-0000-000000000003', 'MysteryHunter', 'Ana García', 'ana@example.com');

-- Crear una partida de ejemplo
DO $$
DECLARE
    v_historia_id UUID;
    v_partida_id UUID;
    v_personaje1_id UUID;
    v_personaje2_id UUID;
    v_nodo1_id UUID;
    v_nodo2_id UUID;
    v_opcion1_id UUID;
    v_opcion2_id UUID;
    v_opcion3_id UUID;
    v_opcion4_id UUID;
BEGIN
    -- Obtener ID de la historia
    SELECT story_id INTO v_historia_id FROM historias WHERE titulo = 'La mansión misteriosa';
    
    -- Crear partida
    v_partida_id := crear_nueva_partida(v_historia_id, '00000000-0000-0000-0000-000000000001');
    
    -- Crear personajes
    INSERT INTO personajes (partida_id, nombre, descripcion)
    VALUES (v_partida_id, 'Detective', 'Un detective privado contratado para investigar los sucesos extraños en la mansión')
    RETURNING character_id INTO v_personaje1_id;
    
    INSERT INTO personajes (partida_id, nombre, descripcion)
    VALUES (v_partida_id, 'Médium', 'Una médium con habilidades psíquicas que puede sentir presencias sobrenaturales')
    RETURNING character_id INTO v_personaje2_id;
    
    -- Asignar personajes a jugadores
    PERFORM anadir_jugador_a_partida(v_partida_id, '00000000-0000-0000-0000-000000000002', v_personaje1_id);
    PERFORM anadir_jugador_a_partida(v_partida_id, '00000000-0000-0000-0000-000000000003', v_personaje2_id);
    
    -- Crear variables para los personajes
    INSERT INTO variables (personaje_id, nombre, descripcion, tipo, valor_inicial)
    VALUES 
    (v_personaje1_id, 'coraje', 'Nivel de valentía del personaje', 'numero', '5'::JSONB),
    (v_personaje1_id, 'intuicion', 'Capacidad para detectar pistas', 'numero', '7'::JSONB),
    (v_personaje2_id, 'poder_psiquico', 'Nivel de poder psíquico', 'numero', '8'::JSONB),
    (v_personaje2_id, 'miedo', 'Nivel de miedo del personaje', 'numero', '3'::JSONB);
    
    -- Crear nodos iniciales
    INSERT INTO nodos (personaje_id, partida_id, titulo, contenido, tipo, posicion_x, posicion_y)
    VALUES (
        v_personaje1_id, 
        v_partida_id, 
        'Llegada a la mansión', 
        'Has llegado a la antigua mansión Blackwood. La estructura se alza imponente ante ti, con sus ventanas oscuras como ojos vigilantes. El viento silba entre los árboles del jardín descuidado. Tienes la sensación de que algo te observa desde las sombras.',
        'narrativo',
        100, 100
    ) RETURNING node_id INTO v_nodo1_id;
    
    INSERT INTO nodos (personaje_id, partida_id, titulo, contenido, tipo, posicion_x, posicion_y)
    VALUES (
        v_personaje2_id, 
        v_partida_id, 
        'Sensaciones extrañas', 
        'Apenas pones un pie en el terreno de la mansión, una oleada de sensaciones te invade. Voces susurrantes parecen llamarte desde el interior de la casa. Sientes presencias antiguas que han quedado atrapadas entre estos muros.',
        'narrativo',
        100, 200
    ) RETURNING node_id INTO v_nodo2_id;
    
    -- Crear opciones para el primer nodo del Detective
    INSERT INTO opciones (nodo_id, texto, efectos, orden)
    VALUES (
        v_nodo1_id, 
        'Examinar el exterior de la mansión antes de entrar', 
        '[{"variable": "intuicion", "operador": "+=", "valor": 1}]'::JSONB,
        1
    ) RETURNING option_id INTO v_opcion1_id;
    
    INSERT INTO opciones (nodo_id, texto, efectos, orden)
    VALUES (
        v_nodo1_id, 
        'Entrar directamente a la mansión', 
        '[{"variable": "coraje", "operador": "+=", "valor": 1}, {"variable": "intuicion", "operador": "-=", "valor": 1}]'::JSONB,
        2
    ) RETURNING option_id INTO v_opcion2_id;
    
    -- Crear opciones para el primer nodo de la Médium
    INSERT INTO opciones (nodo_id, texto, efectos, orden)
    VALUES (
        v_nodo2_id, 
        'Concentrarte para identificar las presencias', 
        '[{"variable": "poder_psiquico", "operador": "+=", "valor": 1}, {"variable": "miedo", "operador": "+=", "valor": 1}]'::JSONB,
        1
    ) RETURNING option_id INTO v_opcion3_id;
    
    INSERT INTO opciones (nodo_id, texto, efectos, orden)
    VALUES (
        v_nodo2_id, 
        'Ignorar las sensaciones y seguir adelante', 
        '[{"variable": "poder_psiquico", "operador": "-=", "valor": 1}, {"variable": "miedo", "operador": "-=", "valor": 1}]'::JSONB,
        2
    ) RETURNING option_id INTO v_opcion4_id;
    
    -- Crear tabla de decisiones que afecta a ambos personajes
    INSERT INTO tablas_decisiones (partida_id, nodo_origen_id, mapeos, mapeo_por_defecto)
    VALUES (
        v_partida_id,
        v_nodo1_id,
        jsonb_build_object(
            v_opcion1_id::TEXT, jsonb_build_object(
                v_personaje1_id::TEXT, v_nodo1_id -- Nodo siguiente para el Detective si elige examinar
            ),
            v_opcion2_id::TEXT, jsonb_build_object(
                v_personaje1_id::TEXT, v_nodo2_id -- Nodo siguiente para el Detective si elige entrar directamente
            )
        ),
        jsonb_build_object(
            v_personaje1_id::TEXT, v_nodo1_id -- Nodo por defecto para el Detective
        )
    );
END $$;
