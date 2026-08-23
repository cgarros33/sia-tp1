# TP1 — Sistemas de Inteligencia Artificial (ITBA)

Sokoban resuelto con métodos de búsqueda clásicos. Python, sin frameworks de IA.

## Antes de tocar nada, leé estos documentos

- `docs/00_CONTEXTO.md` — qué pide la cátedra y cómo se evalúa
- `docs/01_REGLAS_DE_TRABAJO.md` — **reglas obligatorias** (git, checkpoints, resúmenes)
- `docs/02_PLAN_DE_FASES.md` — el mapa completo del proyecto
- `docs/03_NUMEROS_DE_ORO.md` — la tabla de verificación que nunca se debe romper
- `docs/fases/FASE_N_*.md` — la especificación detallada de la fase en curso

Trabajá **una fase por vez**, en orden, y sólo la fase que el usuario te indique.

## Reglas que no se negocian

1. **NUNCA ejecutes `git commit` ni `git push`.** Ni siquiera si parece obvio o
   conveniente. Podés usar `git status`, `git diff` y `git log` para leer.
   Cuando termines algo, decí qué archivos cambiaron y **esperá**. El usuario
   commitea a mano.
2. **NUNCA te agregues como co-autor.** Nada de `Co-Authored-By: Claude`,
   `Generated with Claude Code` ni firmas equivalentes en commits, mensajes,
   comentarios de código o documentación. El trabajo es de las cuatro personas
   del grupo.
3. **PARÁ y explicá antes de escribir cualquier archivo que calcule algo.**
   Heurísticas, pesos, fórmulas, métricas, estadísticas, agregaciones. Ver el
   protocolo de checkpoint en `docs/01_REGLAS_DE_TRABAJO.md`. Este proyecto se
   defiende oralmente: si el grupo no entiende una cuenta, esa cuenta no sirve.
4. **Al terminar cada fase, escribí `docs/resumenes/FASE_N_RESUMEN.md`**
   siguiendo `docs/resumenes/_PLANTILLA.md`. Es lo que lee el grupo para
   entender qué se hizo y por qué.
5. **No cambies los archivos de `niveles/`.** Están verificados contra los
   récords publicados en game-sokoban.com. Si creés que uno está mal, avisá.
6. **No agregues dependencias** más allá de las autorizadas en
   `docs/01_REGLAS_DE_TRABAJO.md` sin preguntar primero.

## Idioma

Todo en español: código, comentarios, docstrings, documentos y respuestas.
Nombres de variables y funciones también. Es el idioma en el que el grupo va a
rendir el oral.

## Estilo de código

Python 3.11+, sin dependencias externas en `src/` salvo `numpy` y `scipy`
(sólo para el matching húngaro de la Fase 4).

**El código va sin comentarios.** Se explica solo: los nombres son largos y en
castellano para eso. Las explicaciones —qué existe, por qué, qué se descartó—
van en `docs/resumenes/`, nunca en los archivos `.py`.

Se comenta sólo una cuenta que no se lee del código, o una regla que si alguien
la borra rompe algo. Los docstrings son de **una línea**. Nada de secciones
"QUÉ REPRESENTA" o "QUÉ SE DESCARTÓ" dentro del código.

El detalle y el porqué del cambio están en `docs/01_REGLAS_DE_TRABAJO.md`,
regla 8.
