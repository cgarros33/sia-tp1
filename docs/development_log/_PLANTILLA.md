# PLANTILLA — resumen de fase

Copiá esta estructura tal cual en `docs/resumenes/FASE_N_RESUMEN.md`.

Está escrita para alguien que **no vio el código**: los otros tres integrantes
lo van a leer para entender qué existe y por qué, antes de rendir el oral.
Si un archivo no justifica un párrafo de "por qué existe", probablemente no
debería existir.

---

```markdown
# FASE N — <nombre>

**Estado:** terminada · **Fecha:** <aaaa-mm-dd>

## En una frase

<Qué quedó funcionando al terminar esta fase.>

## Archivos creados

### `ruta/al/archivo.py`

**Qué hace:** <una línea.>

**Por qué existe:** <un párrafo. Qué problema resuelve, y qué pasaría si no
estuviera.>

**La decisión importante:** <la que hay que poder defender en el oral. Qué se
eligió, contra qué alternativa, y cuál fue el criterio.>

<Repetir para cada archivo nuevo. TODOS.>

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|

## Cuentas que se hacen acá

<Sólo si esta fase introduce algún cálculo. Para cada uno:>

- **Qué calcula:** <en castellano, sin código.>
- **Fórmula:** <la expresión.>
- **Por qué es correcta:** <la justificación. Si es una heurística, la
  demostración de admisibilidad en dos renglones.>
- **Qué se descartó:** <la alternativa evaluada y el motivo.>

<Si la fase no hace cuentas, escribir: "Ninguna. Esta fase no introduce
cálculos.">

## Verificación

**Cómo se comprueba que está bien:**

```
<el comando exacto>
```

**Salida obtenida:**

```
<pegar la salida real, no una versión idealizada>
```

## Números nuevos

<Toda métrica que esta fase haya medido por primera vez, en tabla. Si alguno se
congela como referencia de regresión, decirlo explícitamente.>

## Preguntas que esta fase habilita en el oral

<3 a 5 preguntas que un profesor podría hacer sobre lo construido acá, con la
respuesta en una o dos líneas. Es el banco de respuestas del grupo.>

- **¿...?** <respuesta.>

## Qué quedó pendiente

<Lo que se dejó explícitamente para fases siguientes, y en cuál.>

## Ideas para más adelante

<Cosas que surgieron trabajando y no corresponden a esta fase. Puede estar
vacío.>
```
