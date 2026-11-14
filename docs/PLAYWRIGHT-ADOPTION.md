# Playwright: criterio de uso

Este repositorio produce video mediante Blender, FFmpeg/FFprobe y herramientas de voz; no contiene una interfaz web de usuario que Playwright pueda probar de forma útil.

- Las pruebas del render deben validar archivos MP4, resolución, FPS, duración, audio y subtítulos con FFprobe y pruebas de Python.
- Playwright se incorporará aquí cuando exista una interfaz web de revisión/administración o un reproductor web propio que requiera pruebas reales de navegador.
- No se añade una dependencia de navegador sin una superficie web que probar: hacerlo aumentaría instalación y mantenimiento sin cubrir los fallos principales del renderizador.

El estándar de pruebas de navegador del ecosistema Coco está implementado en `coco-monito-espacial` para el generador web y el Worker.
