# Coco, el Monito Espacial — producción 3D gratuita

Este repositorio produce episodios infantiles de Coco con Blender, FFmpeg y herramientas gratuitas. Tras validar el MP4, el workflow diario lo publica en YouTube mediante el Worker privado; no requiere activar facturación ni comprar créditos.

## Fuente de verdad técnica

- **Motor principal:** Blender EEVEE con personaje procedural, actuación dirigida por cada escena y keyframes a 30 FPS.
- **Calidad de render:** 720×1280 nativos, 24 muestras temporales EEVEE y sombras suaves cuando la versión de Blender lo permite; master final 1080×1920 con codificación H.264 CRF 17.
- **Montaje y control:** FFmpeg / FFprobe.
- **Voz principal:** Edge TTS, voz mexicana es-MX-DaliaNeural.
- **Voz de respaldo:** espeak-ng local, si Edge TTS no responde o no tiene conexión.
- **Música:** melodía original sintetizada localmente; no depende de una biblioteca comercial.
- **Subtítulos:** SRT y subtítulos incrustados en el MP4.
- **Generación IA externa:** opcional. Wan 2.2/Hugging Face se conserva como flujo manual experimental, nunca como requisito del render diario.
- **Publicación:** automática tras superar las validaciones del MP4; una identidad estable por fecha local, un bloqueo atómico en D1 y una huella SHA-256 única del MP4 impiden publicar dos veces el mismo episodio o archivo.

## Producción automática

Workflow único: [Coco — Producción diaria automática](.github/workflows/coco-daily-production.yml).

- Programado una vez al día: 00:30, hora de Nuevo León (UTC-6).
- Ejecución manual disponible desde GitHub Actions.
- Solo se ejecuta por horario diario o lanzamiento manual; los commits de desarrollo no inician producciones ni publicaciones.
- Concurrencia serializada: no cancela un render activo ni permite dos producciones simultáneas.
- Todas las ejecuciones de una misma fecha de Monterrey comparten el mismo `episode_id`; el productor calcula SHA-256 del MP4 y el Worker rechaza archivos idénticos aunque cambie el ID del episodio o la fecha. Los reintentos posteriores a una subida confirmada reciben respuesta de duplicado y no vuelven a subir el MP4.
- Límite máximo por ejecución: 90 minutos.
- Los artefactos se conservan 30 días.

**Importante sobre el plan gratuito:** el horario es un intento, no una garantía de ejecución ni de render terminado. GitHub Actions tiene cuotas mensuales y el render 3D consume CPU. No existe una opción de nube gratuita, ilimitada y garantizada. Si la cuota de Actions se agota, la producción se reanuda cuando se restablezca; no se activa facturación automáticamente.

## Flujo de producción

1. Recupera el código y, si está disponible, la referencia privada de Coco.
2. Valida sintaxis, dependencias y recursos.
3. Crea el episodio a partir de la biblioteca narrativa.
4. Renderiza la escena 3D con Blender.
5. Comprueba duración, resolución, variación visual y tamaño del render.
6. Genera voz. Si Edge TTS falla, utiliza espeak-ng sin conexión.
7. Sintetiza música original y prepara subtítulos.
8. Ensambla el MP4 vertical y valida video, audio, duración y FPS.
9. Guarda el MP4, SRT, episodio y reporte de producción como artefacto.
10. Publica el episodio una sola vez por fecha local mediante el Worker privado; si el mismo ID ya está subido o reservado, la segunda solicitud se bloquea.

## Salidas

- `output/Coco-Short-60s-FINAL.mp4`: master vertical 1080×1920, 30 FPS, 60 segundos.
- `output/subtitles.srt`: subtítulos editables.
- `output/episode.json`: guion y metadatos del episodio.
- `output/production-report.json`: validación técnica, motores usados y referencia disponible.

La señal definitiva de éxito es que el MP4 exista y pase las validaciones; que GitHub Actions marque el job como exitoso por sí solo no demuestra que el archivo sea correcto.

## Referencia visual y secretos

La referencia privada `coco-referencia.webp` es **opcional**: el render diario conserva la identidad mediante el diseño procedural versionado en `video/render_coco.py`. Si existe `GH_READ_TOKEN`, el workflow intenta descargarla con reintentos. Si no está disponible, no bloquea el render.

No guardar tokens, contraseñas ni claves en el repositorio. Si se utiliza el flujo manual de Hugging Face, `HF_TOKEN` debe configurarse como secreto solo si el usuario decide usar ese servicio.

## Mejora híbrida opcional con Wan 2.2

El flujo diario admite un plano de acción generado con **Wan 2.2 I2V 14B + Lightning LoRA (4 pasos)**. Cuando el secreto de repositorio `HF_TOKEN` está configurado y Hugging Face acepta la solicitud, el pipeline sustituye un tramo de 3.5 segundos del render Blender por un clip animado Wan, normaliza el resultado a 720×1280/30 FPS y vuelve a validar la duración total de 60 segundos. Si falta el token, el Space está ocupado, se agota la cuota o falla la generación, se conserva el render Blender y la producción continúa.

Se limita intencionalmente a **un clip Wan por episodio**: la cuota gratuita de ZeroGPU es de 5 minutos de GPU al día para cuentas gratuitas, no permite prometer 12 clips ni tres videos diarios. El pipeline no compra créditos ni cambia hardware. El reporte `production-report.json` registra el estado en `wan22_enhancement`.

Para activar la mejora, crear en Settings → Secrets and variables → Actions del repositorio el secreto `HF_TOKEN` con un token de Hugging Face. No escribir el token en archivos ni compartirlo en el chat. La referencia del personaje se extrae del propio render 3D, por lo que este paso no necesita acceso al repositorio privado.

## Archivos principales

- `video/render_coco.py`: escena, materiales, personaje y animación 3D.
- `scripts/generate_daily_coco.py`: guion, render, voz, música, subtítulos, montaje y control de calidad.
- `.github/workflows/coco-daily-production.yml`: único workflow automático, limitado a horario diario y ejecución manual; no se activa con commits.
- `.github/workflows/generate-huggingface-video.yml`: herramienta manual experimental Wan 2.2, no usada por el pipeline diario.
- `docs/PRODUCTION-ARCHITECTURE.md`: decisiones técnicas, riesgos y recuperación.

## Límites conocidos y próximos hitos

- El personaje actual está construido con formas 3D procedurales y controles de actuación; todavía no es un rig de deformación completo con malla, dedos articulados y sincronía labial fonética. El estilo sigue siendo animación 3D estilizada, no fotorealismo.
- La boca actual es una animación simple, no lip-sync real por fonemas.
- La voz es generada por red cuando Edge TTS funciona; el respaldo local es más robótico.
- La resolución final se renderiza primero a 720×1280 y se amplía a 1080×1920; el escalado final no añade detalle geométrico real.
- El render puede tardar más que la ventana de Actions. La prioridad futura es guardar escenas y estado intermedio de forma persistente, para no repetir trabajo.
- No se promete IA generativa ilimitada gratuita. Los modelos externos son reemplazables y nunca deben bloquear el motor principal.

