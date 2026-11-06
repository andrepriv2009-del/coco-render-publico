# Arquitectura y recuperación de producción

## Principios

1. El archivo de Blender y los scripts de este repositorio son la fuente de verdad.
2. Los proveedores de IA son adaptadores opcionales: no pueden ser una dependencia obligatoria.
3. Un fallo de voz o de descarga de referencia no debe destruir un render visual válido.
4. Cada episodio debe ser reproducible, validado y trazable por número de ejecución.
5. No publicar, comprar créditos ni habilitar facturación automáticamente.

## Componentes

| Capa | Componente | Responsabilidad | Fallback |
|---|---|---|---|
| Personaje | `video/render_coco.py` | Modelo procedural, materiales, accesorios y animación | Diseño versionado local |
| Guion | `scripts/generate_daily_coco.py` | Historia y escenas | Biblioteca narrativa determinista |
| Render | Blender EEVEE | Video base 3D | No hay sustituto que conserve el mismo resultado; falla explícitamente |
| Voz | Edge TTS | Voz mexicana | espeak-ng local |
| Música | Síntesis NumPy/WAV | Música original | Se genera localmente |
| Montaje | FFmpeg | Escalado, mezcla, subtítulos y MP4 | Falla explícitamente si falta FFmpeg |
| Control | FFprobe + validaciones Python | Duración, pistas, resolución, FPS y audio | Nunca entregar un archivo no validado |
| Automatización | GitHub Actions | Ejecución diaria y manual | Ejecución manual local con dependencias equivalentes |

## Política de identidad

Coco debe conservar: monito café, gorra roja brillante, traje espacial blanco y mochila cohete plateada con detalles rojos. Los cambios de color, accesorios o proporciones deben pasar por una actualización explícita de la ficha de personaje y del modelo 3D. No generar versiones alternativas del personaje como si fueran Coco.

## Fallos previstos y recuperación

- **Falta GH_READ_TOKEN o falla la descarga:** usar el diseño procedural local; registrar advertencia. La referencia privada es auxiliar.
- **Edge TTS sin red, timeout o error:** cambiar a espeak-ng; registrar el motor usado en `production-report.json`.
- **Falla Blender:** detener el episodio; no crear un MP4 falso ni marcarlo como completo.
- **FFmpeg/FFprobe ausentes:** detener y mostrar el paso de instalación faltante.
- **Video sin movimiento suficiente:** rechazar el render base mediante hashes de fotogramas.
- **Audio vacío:** rechazar el master por RMS mínimo.
- **MP4 inválido:** no subir como entrega final.
- **Dos ejecuciones simultáneas:** grupo de concurrencia único con cancelación desactivada.
- **Cuota mensual de Actions agotada:** esperar al siguiente periodo o ejecutar localmente; nunca activar facturación automáticamente.
- **Artefacto vencido:** volver a generar el episodio; el estado de progreso actual no es persistente fuera del artefacto de Actions.

## Límites reales del plan gratuito

- GitHub Actions tiene minutos mensuales limitados en repositorios privados; el workflow diario puede consumir una parte importante de esa cuota según el tiempo real del render.
- El cron de Actions no garantiza puntualidad y puede retrasarse.
- Edge TTS depende de disponibilidad de red y de un servicio externo; el fallback local evita bloquear la producción, pero la voz suena menos natural.
- Blender no usa créditos, pero el render consume CPU, RAM y tiempo.
- Ningún complemento conectado ofrece generación de video IA ilimitada y garantizada sin coste. Los saldos gratuitos pueden agotarse o cambiar.

## Siguiente fase técnica (sin romper el pipeline)

1. Crear un rig esquelético real con controladores de cadera, rodillas, hombros, codos, muñecas, dedos y cuello.
2. Separar el modelo de Coco del guion: cargar una ficha de personaje y una biblioteca de acciones desde archivos versionados.
3. Crear acciones reutilizables (idle, caminar, correr, saltar, aterrizar, saludar, bailar, señalar y reaccionar) con transiciones suaves.
4. Sustituir el movimiento de boca genérico por visemas temporizados y sincronía labial.
5. Renderizar por escenas y guardar checkpoints fuera del workspace efímero; verificar la persistencia antes de confiar en una reanudación.
6. Añadir pruebas de continuidad visual, audio, safe-area de subtítulos y revisión de fotogramas.
7. Mantener un único workflow automático y proveedores externos aislados.

## Regla de entrega

Un job verde no basta. La entrega se considera lista solo cuando el artefacto incluye el MP4, el SRT, el JSON del episodio y el reporte, y el MP4 pasa FFprobe y las comprobaciones de audio/video.
