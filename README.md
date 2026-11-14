# Coco, el Monito Espacial — producción 3D gratuita

Este repositorio es la fuente de verdad de la producción audiovisual y del renderizador 3D de Coco. El repositorio privado `coco-monito-espacial` conserva exclusivamente el backend (Worker + D1), episodios y servicios. El workflow de producción genera y valida el MP4, pero **no publica en YouTube**. No se compran créditos ni se activa facturación.

## Perfil de entrega

- **Resolución objetivo obligatoria:** 2160 × 3840 píxeles, vertical 4K nativo.
- **Frecuencia:** 30 fps.
- **Duración:** 60 segundos.
- **Render:** Blender EEVEE a 2160 × 3840, porcentaje de resolución 100 %, 8 muestras.
- **Integridad:** no se permite reducir ni ampliar la resolución, insertar clips de menor resolución ni etiquetar como 4K un vídeo reescalado.
- **Vídeo:** FFmpeg / FFprobe, H.264, CRF 17, audio AAC.
- **Voz:** Edge TTS es-MX-DaliaNeural; respaldo local espeak-ng.
- **Música:** melodía original sintetizada localmente.
- **Subtítulos:** SRT y ASS incrustados con zona segura vertical.
- **Publicación:** desactivada. Los MP4 quedan como artefactos para revisión.

El código y las pruebas ahora exigen 2160 × 3840 y 30 fps desde la salida de Blender hasta el MP4 final. **La primera ejecución 4K todavía debe terminar y producir un artefacto válido para considerar el estándar verificado.** No se declarará terminado solo porque el código o el workflow estén configurados.

## Producción automática

Workflow único: [Coco — Producción diaria automática](.github/workflows/coco-daily-production.yml).

- Un intento diario a las 00:30, hora de Nuevo León (UTC-6).
- Ejecución manual disponible desde GitHub Actions.
- Concurrencia serializada: no cancela un render activo ni inicia dos producciones simultáneas.
- Límite por ejecución: 180 minutos.
- Artefactos conservados 30 días.
- Sin paso de publicación ni subida automática a YouTube.

El horario es un intento, no una garantía de render terminado. El render 4K consume CPU y puede exceder el tiempo disponible del runner gratuito. No se activa facturación automáticamente. Si el runner gratuito no completa el render nativo, se documentará el bloqueo y no se sustituirá por una salida de menor resolución.

## Flujo de producción

1. Recupera el código y la referencia visual privada opcional.
2. Valida sintaxis y dependencias.
3. Genera un episodio con identidad diaria estable.
4. Renderiza 1800 fotogramas a 2160 × 3840 nativos y 30 fps con Blender.
5. Comprueba duración, resolución, FPS y variación visual del render base.
6. Genera voz mexicana; usa espeak-ng local si Edge TTS no responde.
7. Sintetiza música original y prepara subtítulos.
8. Monta el MP4 sin filtro de escalado.
9. FFprobe verifica dimensiones, duración, FPS, audio y códec; se comprueba loudness.
10. Guarda MP4, SRT, episodio y reporte como artefactos de revisión.

## Salidas

- `output/Coco-Short-60s-FINAL.mp4`: master vertical 2160 × 3840, 30 fps, 60 segundos.
- `output/subtitles.srt`: subtítulos editables.
- `output/episode.json`: guion y metadatos.
- `output/production-report.json`: resolución real, FPS, duración, audio y resultado de validación.

La evidencia definitiva es el MP4 descargable y su reporte FFprobe. Un job exitoso sin el artefacto esperado no cuenta como entrega.

## Referencia y privacidad

La referencia privada `coco-referencia.webp` es opcional: el diseño procedural versionado conserva los identificadores visuales de Coco (gorra roja, traje espacial y mochila cohete plateada). Si se usa `GH_READ_TOKEN`, se configura únicamente como secreto de Actions. No guardar tokens ni claves en el repositorio.

## Archivos principales

- `video/render_coco.py`: escena, personaje y animación 3D nativa.
- `scripts/generate_daily_coco.py`: episodio, voz, música, subtítulos, montaje y controles de calidad.
- `.github/workflows/coco-daily-production.yml`: producción diaria y manual, sin publicación.
- `.github/workflows/production-ci.yml`: sintaxis y pruebas del contrato de producción.
- `docs/PRODUCTION-ARCHITECTURE.md`: arquitectura, límites y recuperación.

## Límites conocidos

- Coco se construye con formas 3D procedurales y controles de actuación; todavía no tiene una malla de producción con rig completo de deformación y sincronía labial fonética.
- La voz de respaldo es más robótica que la voz neural.
- El perfil nativo 4K requiere una ejecución completa de Blender. Hasta que esa ejecución produzca un artefacto 2160 × 3840/30 fps comprobado, el resultado se considera pendiente, no final.
