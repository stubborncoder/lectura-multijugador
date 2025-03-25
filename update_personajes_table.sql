-- Script para actualizar la tabla personajes existente
-- Primero, actualizar las referencias en otras tablas para evitar problemas de integridad referencial
-- Renombrar la columna character_id a personaje_id
ALTER TABLE personajes RENAME COLUMN character_id TO personaje_id;

-- Actualizar las referencias en otras tablas
ALTER TABLE nodos 
    DROP CONSTRAINT nodos_personaje_id_fkey,
    ALTER COLUMN personaje_id TYPE UUID USING personaje_id::uuid;

ALTER TABLE variables 
    DROP CONSTRAINT variables_personaje_id_fkey,
    ALTER COLUMN personaje_id TYPE UUID USING personaje_id::uuid;

ALTER TABLE partidas_jugadores 
    DROP CONSTRAINT partidas_jugadores_personaje_id_fkey,
    ALTER COLUMN personaje_id TYPE UUID USING personaje_id::uuid;

ALTER TABLE historial_decisiones 
    DROP CONSTRAINT historial_decisiones_personaje_id_fkey,
    ALTER COLUMN personaje_id TYPE UUID USING personaje_id::uuid;

-- Ahora modificar la tabla personajes
-- Primero, cambiar el tipo de la columna estado de JSONB a VARCHAR
ALTER TABLE personajes 
    ALTER COLUMN estado TYPE VARCHAR(50) USING '{}',
    ALTER COLUMN estado SET DEFAULT 'activo',
    ADD CONSTRAINT personajes_estado_check CHECK (estado IN ('activo', 'inactivo', 'eliminado'));

-- Hacer que partida_id sea opcional (eliminar restricción NOT NULL)
ALTER TABLE personajes ALTER COLUMN partida_id DROP NOT NULL;

-- Añadir las nuevas columnas
ALTER TABLE personajes 
    ADD COLUMN historia_id UUID,
    ADD COLUMN rol VARCHAR(100),
    ADD COLUMN habilidades TEXT[],
    ADD COLUMN nivel_poder SMALLINT,
    ADD CONSTRAINT personajes_nivel_poder_check CHECK (nivel_poder BETWEEN 1 AND 10),
    ADD COLUMN imagen_perfil VARCHAR(255),
    ADD COLUMN edad INTEGER,
    ADD COLUMN origen VARCHAR(255),
    ADD COLUMN creador_id UUID,
    ADD COLUMN fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ADD COLUMN fecha_modificacion TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Establecer la restricción de clave externa para historia_id
ALTER TABLE personajes 
    ADD CONSTRAINT personajes_historia_id_fkey 
    FOREIGN KEY (historia_id) 
    REFERENCES historias(story_id) ON DELETE CASCADE;

-- Hacer que historia_id sea NOT NULL después de la migración de datos
-- Nota: Debes migrar los datos antes de ejecutar esta línea
-- ALTER TABLE personajes ALTER COLUMN historia_id SET NOT NULL;
-- ALTER TABLE personajes ALTER COLUMN creador_id SET NOT NULL;

-- Restablecer las restricciones de clave externa en las otras tablas
ALTER TABLE nodos 
    ADD CONSTRAINT nodos_personaje_id_fkey 
    FOREIGN KEY (personaje_id) 
    REFERENCES personajes(personaje_id) ON DELETE CASCADE;

ALTER TABLE variables 
    ADD CONSTRAINT variables_personaje_id_fkey 
    FOREIGN KEY (personaje_id) 
    REFERENCES personajes(personaje_id) ON DELETE CASCADE;

ALTER TABLE partidas_jugadores 
    ADD CONSTRAINT partidas_jugadores_personaje_id_fkey 
    FOREIGN KEY (personaje_id) 
    REFERENCES personajes(personaje_id) ON DELETE SET NULL;

ALTER TABLE historial_decisiones 
    ADD CONSTRAINT historial_decisiones_personaje_id_fkey 
    FOREIGN KEY (personaje_id) 
    REFERENCES personajes(personaje_id) ON DELETE CASCADE;

-- IMPORTANTE: Después de ejecutar este script, debes migrar los datos para llenar historia_id y creador_id
-- Puedes usar una consulta como esta para migrar los datos:
/*
UPDATE personajes p
SET historia_id = (SELECT historia_id FROM partidas WHERE game_id = p.partida_id),
    creador_id = (SELECT creador_id FROM historias h JOIN partidas pa ON h.story_id = pa.historia_id WHERE pa.game_id = p.partida_id)
WHERE p.historia_id IS NULL;

-- Una vez migrados los datos, ejecuta:
ALTER TABLE personajes ALTER COLUMN historia_id SET NOT NULL;
ALTER TABLE personajes ALTER COLUMN creador_id SET NOT NULL;
*/
