import json
import math
import os
import subprocess
import wave
from datetime import datetime, timezone
from pathlib import Path
from fractions import Fraction

import numpy as np
from PIL import Image

OUT = Path("output")
AUDIO = OUT / "audio"
TMP = Path("/tmp/coco-render")
BASE_VIDEO = TMP / "coco-base.mp4"
FINAL_VIDEO = OUT / "Coco-Short-60s-FINAL.mp4"
OUT.mkdir(exist_ok=True)
AUDIO.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT, FPS, DURATION = 1080, 1920, 30, 60
SLOT = 5
DAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
REFERENCE = Path("coco-referencia.webp")

# 150 combinaciones de la misma premisa visual: Coco ayuda a una estrella perdida.
# El personaje invitado, el destino, el obstáculo y la solución cambian en cada episodio.
FRIENDS = [
    ("Pipo", "un pequeño robot afinador", "escuchar con atención"),
    ("Nuba", "una nube luminosa", "trabajar en equipo"),
    ("Mara", "una tortuga astronauta", "mantener la calma"),
    ("Bongo", "un zorro piloto", "ayudar a los demás"),
    ("Lila", "una flor marciana inventora", "compartir lo que tenemos"),
    ("Tito", "una lagartija piloto", "no rendirse"),
]
DESTINATIONS = [
    "el valle de los anillos",
    "la estación Arcoíris",
    "el cráter de los susurros",
    "el océano de estrellas",
    "la montaña de polvo azul",
]
VARIANTS = [
    ("una lluvia de meteoritos", "un patrón de luces detrás de una roca", "siguen el ritmo y activan una ruta luminosa", "todos celebran su regreso"),
    ("un puente de cristales", "un mapa estelar escondido en el hielo", "ordenan las piezas y abren el camino", "la ruta queda iluminada para los viajeros"),
    ("una nube de polvo brillante", "tres sonidos que llegan desde la constelación", "repiten la secuencia y encuentran la señal", "la constelación vuelve a brillar"),
    ("un cometa que cruza la ruta", "un cristal que refleja el camino correcto", "orientan el cristal hacia la constelación", "la nave recibe una señal de agradecimiento"),
    ("un campo de rocas flotantes", "una pista que aparece cuando nadie se rinde", "combinan sus ideas y despejan el camino", "el cielo recupera una luz que parecía perdida"),
]
STORY_SPECS = [
    (friend, destination, variant)
    for variant in VARIANTS
    for friend in FRIENDS
    for destination in DESTINATIONS
]


def make_story(friend, destination, variant, serial):
    friend_name, friend_description, lesson = friend
    obstacle, twist, solution, finale = variant
    title = f"La estrella perdida: misión {serial:03d}"
    lines = [
        "¡Alerta espacial! Una estrella azul perdió su camino.",
        f"Su última señal apunta hacia {destination}.",
        "Coco ajusta su gorra roja y activa su mochila cohete.",
        f"Allí conoce a {friend_name}, {friend_description}.",
        f"Pero {obstacle} bloquea la ruta de regreso.",
        "Coco respira y observa cada destello con calma.",
        f"Encuentra una pista: {twist}.",
        f"Coco y {friend_name} {solution}.",
        "Juntos guían la estrella hacia su hogar.",
        f"La estrella brilla y {finale}.",
        f"{friend_name} acompaña a Coco de regreso a la nave.",
        f"¡Misión cumplida! Hoy aprendemos a {lesson}.",
    ]
    return title, lines, friend_name, friend_description

def run(command, quiet=False):
    if quiet:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(command, check=True)


def frame_hash(path, seconds):
    return subprocess.check_output(
        ["ffmpeg", "-v", "error", "-ss", str(seconds), "-i", str(path), "-frames:v", "1", "-f", "md5", "-"],
        text=True,
    ).strip()


def stamp(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},000"


if not REFERENCE.is_file() or REFERENCE.stat().st_size == 0:
    raise RuntimeError("No se descargó coco-referencia.webp; no se puede validar la referencia visual.")
with Image.open(REFERENCE) as ref_image:
    reference_size = list(ref_image.size)
    if reference_size[0] < 100 or reference_size[1] < 100:
        raise RuntimeError("La referencia de Coco tiene dimensiones no válidas.")

run_number = int(os.environ.get("GITHUB_RUN_NUMBER", "0") or 0)
serial = run_number if run_number > 0 else int(DAY.replace("-", ""))
story_index = (serial - 1) % len(STORY_SPECS)
title, lines, friend_name, friend_description = make_story(*STORY_SPECS[story_index], serial)

episode = {
    "id": f"coco-{serial:04d}",
    "date": DAY,
    "serial": serial,
    "title": title,
    "script": (
        f"FICHA DE PERSONAJE INVITADO — {friend_name}\n"
        f"DESCRIPCIÓN: {friend_description}\n"
        + "\n".join(f"COCO: {line}" for line in lines)
    ),
    "narration": lines,
}
(TMP / "episode.json").write_text(json.dumps(episode, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "episode.json").write_text(json.dumps(episode, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"EPISODE_SELECTED={title} serial={serial} library={len(STORY_SPECS)}", flush=True)

# Blender renders a real procedural 3D scene: Coco's rig, gestures, walk cycle,
# blinking, mouth movement, moving star/asteroids, camera motion and guest character.
print("BLENDER_3D_RENDER_START", flush=True)
run(["blender", "--background", "--python", "video/render_coco.py"])
if not BASE_VIDEO.is_file() or BASE_VIDEO.stat().st_size < 100_000:
    raise RuntimeError("Blender no produjo un MP4 3D válido.")
base_probe = json.loads(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(BASE_VIDEO)],
    text=True,
))
base_video = next(s for s in base_probe["streams"] if s.get("codec_type") == "video")
base_duration = float(base_probe["format"]["duration"])
if not (59.5 <= base_duration <= 60.5 and base_video.get("width") == 540 and base_video.get("height") == 960):
    raise RuntimeError(f"El render 3D base no cumple 60 s y 540x960: {base_duration}s, {base_video.get('width')}x{base_video.get('height')}")
motion_hashes = [frame_hash(BASE_VIDEO, t) for t in (2, 12, 22, 32, 42, 52)]
if len(set(motion_hashes)) < 4:
    raise RuntimeError("La validación detectó muy poco cambio visual entre escenas del render 3D.")
print("BLENDER_3D_RENDER_VALIDATED=1", flush=True)

# Narration: a separate Mexican Spanish neural voice segment for each 5-second beat.
voice_rms = []
voice_list = OUT / "voice-list.txt"
for index, line in enumerate(lines):
    mp3 = AUDIO / f"voice-{index + 1:02d}.mp3"
    wav = AUDIO / f"voice-{index + 1:02d}.wav"
    run([
        "edge-tts", "--voice", "es-MX-DaliaNeural", "--rate=+12%",
        "--text", line, "--write-media", str(mp3),
    ])
    if not mp3.is_file() or mp3.stat().st_size < 1000:
        raise RuntimeError(f"Edge TTS devolvió voz vacía en la escena {index + 1}.")
    run([
        "ffmpeg", "-y", "-i", str(mp3), "-af", "apad", "-t", str(SLOT),
        "-ar", "44100", "-ac", "2", str(wav),
    ], quiet=True)
    with wave.open(str(wav), "rb") as audio:
        samples = np.frombuffer(audio.readframes(audio.getnframes()), dtype=np.int16).astype(np.float64)
    rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    if rms < 35 or peak < 200:
        raise RuntimeError(f"La narración de la escena {index + 1} está vacía o demasiado baja (RMS={rms:.1f}).")
    voice_rms.append(round(rms, 1))

voice_list.write_text(
    "".join(f"file '{(AUDIO / f'voice-{i + 1:02d}.wav').resolve()}'\n" for i in range(len(lines))),
    encoding="utf-8",
)
voice = OUT / "voice.wav"
run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(voice_list),
    "-t", str(DURATION), "-ar", "44100", "-ac", "2", str(voice),
], quiet=True)

# Original, locally synthesized melody; no licensed track or paid music service.
sample_rate = 44100
music = np.zeros(sample_rate * DURATION, dtype=np.float32)
melody = [261.63, 293.66, 329.63, 392.00, 349.23, 329.63, 293.66, 220.00]
for note_index in range(48):
    start = note_index * 1.25
    end = min(start + 1.10, DURATION)
    first = int(start * sample_rate)
    last = int(end * sample_rate)
    local = np.arange(last - first, dtype=np.float32) / sample_rate
    envelope = np.sin(np.pi * np.clip(local / 1.10, 0, 1)) ** 2
    frequency = melody[note_index % len(melody)]
    tone = np.sin(2 * np.pi * frequency * local) + 0.28 * np.sin(2 * np.pi * (frequency / 2) * local)
    music[first:last] += (0.024 * envelope * tone).astype(np.float32)
time_axis = np.arange(sample_rate * DURATION, dtype=np.float32) / sample_rate
fade = np.minimum(time_axis / 1.5, 1.0) * np.minimum((DURATION - time_axis) / 1.5, 1.0)
music *= fade
stereo = np.stack([music, music], axis=1)
music_path = OUT / "music.wav"
with wave.open(str(music_path), "wb") as audio:
    audio.setnchannels(2)
    audio.setsampwidth(2)
    audio.setframerate(sample_rate)
    audio.writeframes((np.clip(stereo, -1, 1) * 32767).astype("<i2").tobytes())

# Timed subtitles are both burned into the video and delivered as a separate SRT.
srt_entries = []
for index, line in enumerate(lines):
    srt_entries.append(
        f"{index + 1}\n{stamp(index * SLOT)} --> {stamp((index + 1) * SLOT)}\n{line}\n"
    )
srt_path = OUT / "subtitles.srt"
srt_path.write_text("\n".join(srt_entries), encoding="utf-8")
if len([entry for entry in srt_path.read_text(encoding="utf-8").split("\n\n") if "-->" in entry]) != 12:
    raise RuntimeError("El archivo SRT no contiene las 12 escenas esperadas.")

# Final portrait master: 1080x1920, 30 fps, Mexican Spanish narration and original score.
subtitle_filter = (
    "scale=1080:1920:flags=lanczos,fps=30,"
    "subtitles=output/subtitles.srt:"
    "force_style='FontName=DejaVu Sans,FontSize=10,PrimaryColour=&H00FFFFFF,"
    "OutlineColour=&H00101830,BorderStyle=1,Outline=2,Shadow=1,"
    "Alignment=2,MarginV=190,MarginL=110,MarginR=110'"
)
run([
    "ffmpeg", "-y", "-i", str(BASE_VIDEO), "-i", str(voice), "-i", str(music_path),
    "-filter_complex",
    "[1:a]volume=1.0[v];[2:a]volume=0.18[m];"
    "[v][m]amix=inputs=2:duration=longest:dropout_transition=0,alimiter=limit=0.95[a]",
    "-vf", subtitle_filter,
    "-map", "0:v", "-map", "[a]", "-t", str(DURATION),
    "-metadata", f"title={title}",
    "-metadata", "comment=Coco, el Monito Espacial | animación 3D diaria",
    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
    "-r", str(FPS), "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
    str(FINAL_VIDEO),
])

probe = json.loads(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(FINAL_VIDEO)],
    text=True,
))
video_stream = next(s for s in probe["streams"] if s.get("codec_type") == "video")
audio_stream = next(s for s in probe["streams"] if s.get("codec_type") == "audio")
duration = float(probe["format"]["duration"])
fps = float(Fraction(video_stream["avg_frame_rate"]))
if not (59.8 <= duration <= 60.2):
    raise RuntimeError(f"Duración final incorrecta: {duration}s.")
if video_stream.get("width") != WIDTH or video_stream.get("height") != HEIGHT:
    raise RuntimeError("La resolución final no es 1080x1920.")
if abs(fps - FPS) > 0.01:
    raise RuntimeError(f"El video final no es 30 fps: {video_stream['avg_frame_rate']}.")
if not audio_stream or FINAL_VIDEO.stat().st_size < 500_000:
    raise RuntimeError("El MP4 final no contiene una pista de audio o es demasiado pequeño.")
final_audio = subprocess.check_output(
    ["ffmpeg", "-v", "error", "-i", str(FINAL_VIDEO), "-vn", "-f", "s16le", "-ac", "2", "-ar", "44100", "-"],
)
final_samples = np.frombuffer(final_audio, dtype=np.int16).astype(np.float64)
final_rms = float(np.sqrt(np.mean(final_samples * final_samples))) if final_samples.size else 0.0
if final_rms < 100:
    raise RuntimeError(f"La pista de audio final parece vacía (RMS={final_rms:.1f}).")

report = {
    "date": DAY,
    "episode_serial": serial,
    "title": title,
    "duration_seconds": round(duration, 3),
    "resolution": f"{WIDTH}x{HEIGHT}",
    "fps": video_stream["avg_frame_rate"],
    "video_codec": video_stream.get("codec_name"),
    "audio_codec": audio_stream.get("codec_name"),
    "audio_sample_rate": audio_stream.get("sample_rate"),
    "narration_voice": "es-MX-DaliaNeural",
    "narration_segments_rms": voice_rms,
    "final_audio_rms": round(final_rms, 1),
    "music": "original synthesized melody; no paid or licensed track",
    "subtitles": "12 Spanish captions burned into the MP4 plus separate SRT",
    "animation": "Blender EEVEE procedural 3D character animation",
    "render_source": "540x960 at 15 fps; upscaled to 1080x1920 at 30 fps",
    "motion_validation": "6 sampled timestamps; at least 4 distinct frame hashes",
    "character_design": "brown monkey, bright red cap, white astronaut suit, silver rocket backpack; procedural adaptation of the official reference's key identifiers",
    "reference_image": {"file": REFERENCE.name, "dimensions": reference_size, "downloaded": True},
    "story_library": len(STORY_SPECS),
    "story_rotation": "150 narrative combinations before rotation; serial is unique per workflow run",
    "status": "verified",
}
(OUT / "production-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    f"DAILY_VIDEO_READY={FINAL_VIDEO} duration={duration:.3f} "
    f"resolution={WIDTH}x{HEIGHT} fps={video_stream['avg_frame_rate']} title={title}",
    flush=True,
)
