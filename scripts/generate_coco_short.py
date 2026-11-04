import os
import subprocess
import shutil
import math
import wave
from pathlib import Path

import numpy as np
from gradio_client import Client, handle_file

ROOT = Path(".")
OUT = ROOT / "output"
PARTS = OUT / "parts"
OUT.mkdir(exist_ok=True)
PARTS.mkdir(exist_ok=True)

TOKEN = os.environ.get("HF_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("Falta el secreto HF_TOKEN.")
if not Path("coco-referencia.webp").is_file():
    raise SystemExit("No se encontró coco-referencia.webp.")

# Historia original de 60 segundos: 12 escenas consecutivas de 5 segundos.
scenes = [
    ("Coco está dentro de su nave espacial mirando por la ventana. Una pequeña estrella azul parpadea y se aleja lentamente en el espacio. Cámara suave, animación 3D infantil cinematográfica.",
     "¡Oh, no! Una estrellita se está perdiendo en el espacio."),
    ("Continuación directa. Coco se acerca a la ventana y señala la estrella brillante que flota cerca de un planeta azul. Mantener exactamente el mismo personaje, gorra roja y mochila cohete.",
     "Coco descubre que la estrella necesita regresar al cielo."),
    ("Continuación. Coco se prepara con entusiasmo, ajusta su gorra roja y revisa su mochila cohete plateada. Interior de nave espacial colorido y acogedor.",
     "Se coloca su casco y enciende su pequeña mochila cohete."),
    ("Continuación. Coco abre con cuidado la compuerta de la nave y sale flotando hacia la estrella. Movimiento lento y seguro, espacio colorido.",
     "Con mucho cuidado, sale de la nave para ayudarla."),
    ("Continuación. Coco vuela junto a la estrella a través de una nebulosa violeta y turquesa llena de destellos. Cámara acompaña el vuelo.",
     "La sigue entre nubes brillantes de polvo espacial."),
    ("Continuación. Un cometa pequeño cruza delante de Coco. Coco esquiva suavemente el cometa sin perder de vista la estrella.",
     "¡Pero un cometa travieso se cruza en su camino!"),
    ("Continuación. Coco usa un impulso corto de su mochila cohete para alcanzar la estrella. Expresión decidida y divertida, movimiento fluido.",
     "Coco acelera un poquito y logra alcanzarla."),
    ("Continuación. La estrella está atrapada dentro de un cristal de hielo transparente que flota. Coco se acerca y observa con ternura.",
     "La encuentra atrapada en un cristal de hielo espacial."),
    ("Continuación. Coco ilumina el cristal con una luz cálida de su mochila cohete. El hielo comienza a brillar y a derretirse suavemente.",
     "Con la luz de su mochila, derrite el hielo despacito."),
    ("Continuación. La estrella sale libre del cristal y brilla intensamente junto a Coco. Momento emotivo, destellos suaves.",
     "¡Lo consiguió! La estrellita vuelve a brillar con fuerza."),
    ("Continuación. La estrella asciende hacia el cielo y ocupa su lugar entre muchas estrellas. Coco la saluda feliz desde el espacio.",
     "La estrella regresa al cielo y todas celebran su regreso."),
    ("Continuación. Coco vuelve a su nave espacial, mira a cámara y saluda. La estrella brilla por la ventana detrás de él. Final cálido y alegre.",
     "Coco sonríe: ¡hasta la luz más pequeña merece ayuda!")
]

client = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster", token=TOKEN)
reference = Path("coco-referencia.webp")

def run(cmd):
    subprocess.run(cmd, check=True)

def ffprobe_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip()
    return float(out)

# Generate each five-second part. The final frame of each part guides the next one.
for idx, (prompt, narration) in enumerate(scenes, start=1):
    raw = PARTS / f"part-{idx:02d}-raw.mp4"
    normalized = PARTS / f"part-{idx:02d}.mp4"
    frame = PARTS / "next-reference.jpg"
    if idx == 1:
        image_input = reference
    else:
        image_input = frame

    # Reuse completed scenes from the previous run instead of spending GPU again.
    if normalized.is_file() and ffprobe_duration(normalized) >= 4.85:
        print(f"PART_REUSED={idx}/12", flush=True)
    else:
        print(f"GENERATING_PART={idx}/12", flush=True)
        result = client.predict(
            input_image=handle_file(str(image_input)),
            prompt=prompt + " Coco debe conservar su identidad y aspecto de la imagen de referencia: monito café, gorra roja brillante, traje espacial blanco y mochila cohete plateada con detalles rojos. Sin texto ni marcas de agua. Movimiento natural, sin deformaciones.",
            steps=4,
            negative_prompt="low quality, flicker, jitter, deformed face, extra limbs, text, watermark, changed clothes, missing red cap, missing rocket backpack, duplicate character",
            duration_seconds=5.0,
            guidance_scale=1,
            guidance_scale_2=1,
            seed=4100 + idx,
            randomize_seed=False,
            api_name="/generate_video",
        )
        video_path = result[0] if isinstance(result, (tuple, list)) else result
        if isinstance(video_path, dict):
            video_path = video_path.get("path") or video_path.get("name")
        if not video_path or not Path(video_path).is_file():
            raise RuntimeError(f"Wan 2.2 no devolvió un video válido para la parte {idx}.")
        shutil.copy2(video_path, raw)

        # Standardize every new part to portrait 9:16, exactly five seconds, 30 fps.
        run([
            "ffmpeg", "-y", "-i", str(raw), "-t", "5",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,tpad=stop_mode=clone:stop_duration=5,trim=duration=5,setsar=1,format=yuv420p",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            str(normalized)
        ])

    # Always rebuild the continuity reference from the latest completed scene.
    run(["ffmpeg", "-y", "-sseof", "-0.15", "-i", str(normalized), "-frames:v", "1", "-q:v", "2", str(frame)])
    print(f"PART_READY={idx}", flush=True)

# Concatenate the twelve normalized video parts.
concat_file = OUT / "concat.txt"
concat_file.write_text("".join(f"file '{(PARTS / f'part-{i:02d}.mp4').resolve()}'\n" for i in range(1, 13)), encoding="utf-8")
silent_video = OUT / "video-sin-audio.mp4"
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
     "-t", "60", "-c", "copy", str(silent_video)])

# Create one Spanish voice segment per scene and fit each segment into its five-second slot.
voice_segments = []
srt_lines = []
for idx, (_, narration) in enumerate(scenes, start=1):
    mp3 = OUT / f"voice-{idx:02d}.mp3"
    wav = OUT / f"voice-{idx:02d}.wav"
    run(["edge-tts", "--voice", "es-MX-DaliaNeural", "--rate=+8%", "--text", narration, "--write-media", str(mp3)])
    run(["ffmpeg", "-y", "-i", str(mp3), "-af", "atempo=1.08,apad", "-t", "5",
         "-ar", "44100", "-ac", "2", str(wav)])
    voice_segments.append(wav)
    start = (idx - 1) * 5
    end = idx * 5
    def stamp(seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02},000"
    srt_lines.append(f"{idx}\n{stamp(start)} --> {stamp(end - 1)}\n{narration}\n")
(OUT / "subtitles.srt").write_text("\n".join(srt_lines), encoding="utf-8")

audio_concat = OUT / "voice-concat.txt"
audio_concat.write_text("".join(f"file '{p.resolve()}'\n" for p in voice_segments), encoding="utf-8")
voice_wav = OUT / "voice.wav"
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_concat), "-t", "60", str(voice_wav)])

# Compose a gentle, original synthesized space-music bed (no copyrighted recording).
sr = 44100
t = np.arange(sr * 60, dtype=np.float32) / sr
music = np.zeros_like(t)
chords = [
    (261.63, 329.63, 392.00), (220.00, 261.63, 329.63),
    (174.61, 220.00, 261.63), (196.00, 246.94, 293.66)
]
for bar in range(4):
    mask = (t >= bar * 15) & (t < (bar + 1) * 15)
    local = t[mask] - bar * 15
    env = np.minimum(local / 2.0, 1.0) * np.minimum((15.0 - local) / 2.0, 1.0)
    chord = chords[bar]
    layer = sum(np.sin(2 * np.pi * f * local) for f in chord) / 3.0
    music[mask] += 0.055 * layer * env
music = np.clip(music, -0.2, 0.2)
stereo = np.stack([music, music], axis=1)
music_wav = OUT / "music-original.wav"
with wave.open(str(music_wav), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    wf.writeframes((stereo * 32767).astype("<i2").tobytes())

# Burn Spanish subtitles, mix narration with original background music, and encode final MP4.
final_video = OUT / "Coco-Short-60s-FINAL.mp4"
subtitle_filter = "subtitles=output/subtitles.srt:force_style='FontName=DejaVu Sans,FontSize=22,Outline=2,Shadow=1,Alignment=2,MarginV=120'"
run([
    "ffmpeg", "-y", "-i", str(silent_video), "-i", str(voice_wav), "-i", str(music_wav),
    "-filter_complex", f"[0:v]{subtitle_filter}[v];[1:a]volume=1.0[voice];[2:a]volume=0.18[music];[voice][music]amix=inputs=2:duration=longest:dropout_transition=0,alimiter=limit=0.95[a]",
    "-map", "[v]", "-map", "[a]", "-t", "60",
    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
    "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    str(final_video)
])

duration = ffprobe_duration(final_video)
if abs(duration - 60.0) > 0.15:
    raise RuntimeError(f"El video final no dura 60 segundos: {duration:.3f}")
print(f"FINAL_VIDEO={final_video}", flush=True)
print(f"FINAL_DURATION={duration:.3f}", flush=True)
