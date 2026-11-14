# Ownership de producción — Coco

## Repositorios oficiales

- **Producción audiovisual (principal):** `andrepriv2009-del/coco-render-publico`. Aquí viven Blender, los scripts de render, FFmpeg, los controles de calidad, los artefactos y sus workflows.
- **Backend privado:** `andrepriv2009-del/coco-monito-espacial`. Conserva Cloudflare Worker, D1, la cola de episodios, OAuth y las API. No se mueve ni se duplica dentro del repositorio público.

El repositorio audiovisual es la fuente de verdad para el archivo MP4 y su reporte técnico. El backend es la fuente de verdad para el estado remoto y la persistencia. La integración entre ambos debe ser explícita, autenticada e idempotente.

## Flujo seguro de entrega

1. Validar sintaxis Python y configuración del workflow.
2. Generar el episodio y renderizar con Blender.
3. Validar el video base y el master final mediante FFprobe.
4. Validar audio, duración, movimiento y subtítulos.
5. Guardar MP4, SRT, JSON del episodio y reporte como artefacto.
6. Solo después de pruebas de contrato y autorización separadas podrá enviarse el resultado al Worker.
7. La publicación en YouTube requiere un gate independiente. Los commits y los despliegues de desarrollo nunca deben publicar.

## Estado de calidad conocido (2026-11-13)

- El render base configurado es **720×1280 a 30 FPS**.
- El master actual es **1080×1920 a 30 FPS**, obtenido mediante escalado.
- El estándar objetivo aprobado en el backend es **2160×3840 vertical, 30 FPS, nativo y sin upscale**.
- Por tanto, el master actual **no cumple todavía el estándar 4K nativo** y no debe etiquetarse ni publicarse como 4K.
- El render 3D usa un personaje procedural; todavía no equivale a un rig de deformación completo ni a animación de estudio.

## Seguridad y presupuesto

- Mantener el Worker y D1 existentes; no ejecutar migraciones destructivas.
- No copiar secretos, tokens OAuth ni credenciales al repositorio.
- No habilitar facturación ni comprar créditos.
- Mantener la publicación automática desactivada hasta completar las pruebas de contrato y la verificación de un MP4 real.
- Si una cuota gratuita se agota o un paso falla, detenerse y conservar el estado para revisión.

## Criterios de aceptación antes de activar producción pública

- CI verde en la rama candidata.
- Render real terminado y artefacto descargable.
- FFprobe confirma resolución, FPS, duración y pistas esperadas.
- Reporte coherente con el archivo real.
- Contrato Worker probado con autenticación, rechazo de duplicados y estados de error.
- Despliegue verificado en entorno de prueba antes de cambiar el flujo de producción.
