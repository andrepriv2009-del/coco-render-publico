# Coco — renderizador público

Este repositorio contiene únicamente el renderizador técnico de videos. El proyecto principal y el código del Worker permanecen en el repositorio privado.

## Qué hace
- Consulta un episodio pendiente en el Worker mediante `/render-feed`.
- Renderiza la escena 3D con Blender.
- Genera voz en español con espeak-ng, música original procedural y subtítulos.
- Ensambla un MP4 vertical 720×1280 de 60 segundos.
- Guarda el MP4 como artefacto de GitHub Actions.
- Confirma el renderizado mediante `/render-complete`.

## Configuración necesaria
En **Settings → Secrets and variables → Actions → New repository secret**, crea:

- `GENERATOR_TOKEN`: el mismo valor del secreto `GENERATOR_TOKEN` configurado en el Worker de Cloudflare.

Nunca publiques ese valor ni lo escribas en el código. No se requiere tarjeta, R2 ni activar servicios de pago.

## Ejecución
El flujo está programado cada 8 horas (UTC) y también puede iniciarse desde **Actions → Renderizar video 3D de Coco → Run workflow**.

La publicación en YouTube no está implementada ni activada. El MP4 queda como artefacto descargable de la ejecución y se conserva 30 días.

## Límites
La programación de GitHub Actions no garantiza hora exacta ni ejecución ininterrumpida. Si no hay episodios pendientes, el ciclo termina sin error y no genera un video.
