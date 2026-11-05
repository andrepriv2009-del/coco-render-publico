# Coco, el Monito Espacial — renderizador Wan 2.2

Este repositorio contiene el renderizador automático de un YouTube Short infantil de Coco. No publica en YouTube.

## Resultado esperado

- Un MP4 final: `output/Coco-Short-60s-FINAL.mp4`.
- 60 segundos, vertical 9:16, 1080×1920, 30 FPS.
- 12 escenas consecutivas de 5 segundos.
- Animación generada con **Wan 2.2 I2V 14B + Lightning LoRA**, mediante el Space público de Hugging Face `zerogpu-aoti/wan2-2-fp8da-aoti-faster`.
- Continuidad visual: el último fotograma de cada escena se usa como referencia para la siguiente.
- Voz en español mexicano con Edge TTS (Dalia), música original sintetizada y subtítulos incrustados.
- Validación final de duración, resolución, FPS y pista de audio.

## Automatización

Workflow: [Coco — Short final de 60 segundos (Wan 2.2)](.github/workflows/generate-coco-short-60s.yml)

Se ejecuta cada 8 horas mediante GitHub Actions:
- 00:30, 08:30 y 16:30, hora de Nuevo León (UTC-6).
- También se ejecuta cuando se actualiza el workflow y admite ejecución manual desde Actions.

Cada ejecución recupera el último artefacto no vencido, reutiliza las escenas válidas y genera únicamente las escenas faltantes. Si Hugging Face ZeroGPU rechaza una solicitud por cuota gratuita, el proceso registra la pausa, guarda el progreso y lo reanuda en el siguiente ciclo. La cuota gratuita es limitada: el horario programa intentos, no garantiza que cada intento pueda generar una escena.

## Secretos requeridos

En **Settings → Secrets and variables → Actions**:

- `HF_TOKEN`: token de Hugging Face con acceso de lectura, para conectarse al Space.
- `GH_READ_TOKEN`: token de GitHub con acceso de lectura al repositorio privado `andrepriv2009-del/coco-monito-espacial`, necesario para descargar la imagen de referencia `coco-referencia.webp`.

Los valores nunca deben guardarse en el código ni compartirse en mensajes.

## Archivos y seguimiento

- Generador: `scripts/generate_coco_short.py`.
- Estado de cada intento: `output/render-status.json`.
- Resumen legible: resumen del job en GitHub Actions.
- Artefacto de recuperación: `Coco-Short-60s-build` (30 días).
- Video final: `Coco-Short-60s-FINAL.mp4`.

**Importante:** una ejecución de Actions puede terminar correctamente aunque el render quede pausado por cuota. El indicador definitivo es `render-status.json` con `status: complete`, junto con la presencia del MP4 final y la validación de sus pistas.

## Límites y seguridad

- No se requiere activar facturación, comprar créditos ni habilitar R2.
- No se cambia a Blender ni a otro modelo: el generador de escenas es Wan 2.2 I2V 14B con Lightning LoRA.
- La publicación en YouTube permanece desactivada; el resultado solo se guarda como artefacto descargable.
- GitHub Actions no garantiza ejecución a una hora exacta y Hugging Face ZeroGPU tiene cuotas compartidas y limitadas.
