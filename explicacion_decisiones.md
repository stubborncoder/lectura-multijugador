# Gestión de Decisiones en el Sistema de Historias Interactivas Multijugador

## Explicación Detallada

En este sistema de historias interactivas multijugador, la gestión de decisiones es un componente central que permite que las elecciones de un jugador afecten tanto su propia narrativa como la de otros jugadores. A continuación, se explica en detalle cómo funciona este mecanismo:

## 1. Estructura Básica de Decisiones

Cada decisión en el sistema sigue este flujo:

1. Un jugador controla un personaje que se encuentra en un nodo narrativo específico
2. El nodo ofrece múltiples opciones (decisiones posibles)
3. El jugador selecciona una opción
4. La opción tiene efectos que modifican el estado del personaje
5. La decisión determina el siguiente nodo en la narrativa

## 2. Almacenamiento de Decisiones

Las decisiones se almacenan en tres lugares:

- **Tabla `historial_decisiones`**: Registro cronológico detallado de todas las decisiones
- **Campo `decisiones` en la tabla `partidas`**: Estructura JSONB que mapea personajes, nodos y opciones
- **Campo `estado` en la tabla `personajes`**: Almacena el estado actual resultante de todas las decisiones

## 3. Efectos de las Decisiones

Cuando un jugador toma una decisión, ocurren varios efectos:

### a) Efectos Directos en el Personaje

Las opciones pueden modificar las variables del personaje mediante operadores:
- `=` (asignación directa)
- `+=` (incremento)
- `-=` (decremento)
- `*=` (multiplicación)
- `/=` (división)

Por ejemplo, elegir "Examinar el exterior de la mansión" incrementa la variable "intuición" del Detective.

### b) Registro en el Historial

La función `registrar_decision` guarda cada decisión en la tabla `historial_decisiones`, incluyendo:
- Quién tomó la decisión (jugador_id)
- Qué personaje utilizó (personaje_id)
- En qué nodo estaba (nodo_id)
- Qué opción eligió (opcion_id)
- Cuándo la tomó (timestamp)
- Qué efectos se aplicaron (efectos_aplicados)

Este registro es crucial para reconstruir el estado de un personaje y para implementar mecánicas de "viaje en el tiempo" o bifurcaciones narrativas.

## 4. Interacción entre Personajes

La verdadera complejidad y riqueza del sistema viene de la interacción entre las decisiones de diferentes personajes:

### a) Tablas de Decisiones

Las `tablas_decisiones` son el mecanismo principal para que las decisiones de un personaje afecten a otros:

```json
{
  "combinacion_decisiones": {
    "personaje_id1": "nodo_destino_id1",
    "personaje_id2": "nodo_destino_id2"
  }
}
```

Esto permite escenarios como:
- Si el Detective elige "examinar el exterior" y la Médium elige "concentrarse", ambos descubren una entrada secreta
- Si el Detective elige "entrar directamente" y la Médium elige "ignorar las sensaciones", ambos caen en una trampa

### b) Contenido Condicional

Los nodos pueden mostrar contenido alternativo basado en decisiones previas de cualquier personaje:

```json
[
  {
    "contenido": "Notas que la puerta que el Detective forzó anteriormente ahora está abierta",
    "condiciones": [
      {"variable": "puerta_forzada", "operador": "==", "valor": true}
    ]
  }
]
```

Esto permite que la narrativa refleje las acciones de otros personajes.

### c) Condiciones de Visibilidad

Tanto los nodos como las opciones tienen condiciones de visibilidad que pueden depender del estado de cualquier personaje:

```json
[
  {"variable": "intuicion", "operador": ">", "valor": 5},
  {"variable": "miedo", "operador": "<", "valor": 8}
]
```

Esto permite que ciertas rutas narrativas solo estén disponibles si otros personajes han tomado determinadas decisiones.

## 5. Ejemplo Práctico: La Mansión Misteriosa

En nuestro ejemplo de "La mansión misteriosa":

1. El Detective y la Médium llegan a la mansión en diferentes nodos iniciales
2. Si el Detective elige "examinar el exterior", aumenta su intuición
3. Si la Médium elige "concentrarse", aumenta su poder psíquico pero también su miedo
4. Dependiendo de estas decisiones iniciales:
   - Si ambos son cautelosos (examinar/concentrarse), pueden descubrir secretos ocultos
   - Si ambos son impulsivos (entrar directamente/ignorar), pueden avanzar más rápido pero perder pistas
   - Si toman decisiones mixtas, la narrativa se adapta a esta combinación

## 6. Implementación Técnica

La función `obtener_siguiente_nodo` es clave en este proceso:

1. Primero intenta obtener el destino directo desde la opción
2. Si no existe, busca en las tablas de decisiones
3. Construye una clave basada en las decisiones de todos los personajes relevantes
4. Busca esta combinación en los mapeos
5. Si no encuentra una coincidencia exacta, usa el mapeo por defecto

Esta función permite que el sistema determine dinámicamente el siguiente nodo para cada personaje basado en las decisiones colectivas.

## 7. Ventajas del Sistema

Este enfoque ofrece varias ventajas:

- **Narrativas entrelazadas**: Las historias de los personajes no son independientes, sino que se influyen mutuamente
- **Emergencia narrativa**: Surgen situaciones no explícitamente programadas de la combinación de decisiones
- **Rejugabilidad**: Diferentes combinaciones de decisiones llevan a diferentes experiencias
- **Colaboración y conflicto**: Los jugadores pueden ayudarse o entorpecerse mutuamente

## 8. Consideraciones para Diseñadores de Historias

Al crear historias para este sistema, los diseñadores deben:

1. Pensar en cómo las decisiones de un personaje afectan el mundo compartido
2. Crear nodos con contenido condicional que refleje las acciones de otros personajes
3. Diseñar tablas de decisiones que combinen las elecciones de múltiples personajes
4. Balancear la autonomía individual con la influencia colectiva

## Conclusión

El sistema de gestión de decisiones implementado permite crear experiencias narrativas verdaderamente multijugador, donde cada jugador tiene agencia sobre su personaje pero también influye en la historia de los demás. Esta interconexión crea una experiencia narrativa rica y dinámica que va más allá de las historias interactivas tradicionales de un solo jugador.
