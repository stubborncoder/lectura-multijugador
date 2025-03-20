from fastapi import APIRouter
from app.api.v1 import (
    historias,
    partidas,
    jugadores,
    personajes,
    nodos,
    opciones,
    tablas_decisiones,
    variables,
    partidas_jugadores,
    historial_decisiones,
    autores,
    auth
)

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)  # Auth router first for better organization
api_router.include_router(historias.router)
api_router.include_router(partidas.router)
api_router.include_router(jugadores.router)
api_router.include_router(personajes.router)
api_router.include_router(nodos.router)
api_router.include_router(opciones.router)
api_router.include_router(tablas_decisiones.router)
api_router.include_router(variables.router)
api_router.include_router(partidas_jugadores.router)
api_router.include_router(historial_decisiones.router)
api_router.include_router(autores.router)
