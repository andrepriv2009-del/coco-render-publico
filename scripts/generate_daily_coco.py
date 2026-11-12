import json
import math
import os
import re
import subprocess
import textwrap
import wave
from datetime import datetime
from zoneinfo import ZoneInfo
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
DAY = datetime.now(ZoneInfo("America/Monterrey")).strftime("%Y-%m-%d")
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
        "¡Coco corre por el campo, esquiva las rocas y se acerca a la señal!",
        f"Al saltar sobre una roca brillante, descubre una pista: {twist}.",
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


# La imagen privada es una referencia auxiliar, no una dependencia del render:
# Blender contiene el diseño procedural versionado de Coco y puede producir sin ella.
reference_size = None
reference_downloaded = False
if REFERENCE.is_file() and REFERENCE.stat().st_size > 0:
    try:
        with Image.open(REFERENCE) as ref_image:
            reference_size = list(ref_image.size)
            if reference_size[0] < 100 or reference_size[1] < 100:
                raise RuntimeError("La referencia de Coco tiene dimensiones no válidas.")
        reference_downloaded = True
    except Exception as exc:
        print(f"REFERENCE_WARNING={exc}; se usará el diseño procedural local.", flush=True)
        reference_size = None
else:
    print("REFERENCE_OPTIONAL=1; se usará el diseño procedural local de Blender.", flush=True)

run_number = int(os.environ.get("GITHUB_RUN_NUMBER", "0") or 0)
serial = run_number if run_number > 0 else int(DAY.replace("-", ""))
# Paso coprimo para recorrer las 150 combinaciones sin agrupar episodios por el mismo invitado/obstáculo.
STORY_ROTATION_STEP = 37
if math.gcd(STORY_ROTATION_STEP, len(STORY_SPECS)) != 1:
    raise RuntimeError("El paso de rotación debe ser coprimo con el tamaño de la biblioteca.")
story_index = ((serial - 1) * STORY_ROTATION_STEP) % len(STORY_SPECS)
title, lines, friend_name, friend_description = make_story(*STORY_SPECS[story_index], serial)

episode = {
    "id": f"coco-{serial:04d}",
    "date": DAY,
    "serial": serial,
    "story_index": story_index,
    "story_rotation_step": STORY_ROTATION_STEP,
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
base_fps = float(Fraction(base_video.get("avg_frame_rate", "0/1")))
if not (
    59.5 <= base_duration <= 60.5
    and base_video.get("width") == 720
    and base_video.get("height") == 1280
    and abs(base_fps - 15) <= 0.01
):
    raise RuntimeError(
        f"El render 3D base no cumple 60 s, 720x1280 y 15 fps: "
        f"{base_duration}s, {base_video.get('width')}x{base_video.get('height')}, {base_fps} fps"
    )
motion_hashes = [frame_hash(BASE_VIDEO, t) for t in (2, 12, 22, 32, 42, 52)]
if len(set(motion_hashes)) < 4:
    raise RuntimeError("La validación detectó muy poco cambio visual entre escenas del render 3D.")
print("BLENDER_3D_RENDER_VALIDATED=1", flush=True)

# Production profile v2 — Wan 2.2 optional hero shot + deterministic Blender fallback.
# Optional hybrid shot: one Wan 2.2 Lightning clip per daily episode.
# Hugging Face ZeroGPU has a small free daily quota, so it is deliberately
# limited to ONE short hero shot. Blender remains the reliable full-length fallback.
WAN_STATUS = "not_configured"
if os.environ.get("HF_TOKEN", "").strip():
    try:
        from gradio_client import Client, handle_file
        import shutil

        print("WAN_ENHANCEMENT_START=1", flush=True)
        wan_reference = TMP / "wan-reference.png"
        wan_raw = TMP / "wan-raw.mp4"
        wan_clip = TMP / "wan-normalized.mp4"
        original_video = BASE_VIDEO
        run(["ffmpeg", "-y", "-ss", "2", "-i", str(original_video),
             "-frames:v", "1", "-q:v", "2", str(wan_reference)], quiet=True)
        client = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster",
                        token=os.environ["HF_TOKEN"].strip())
        wan_prompt = (
            "Animate the exact same friendly brown monkey astronaut from the input image. "
            "Preserve his bright red cap, white astronaut suit and small silver rocket backpack. "
            "He turns toward the camera, smiles, waves, and makes a small joyful zero-gravity bounce. "
            "Keep the same character identity and outfit throughout, smooth natural full-body motion, "
            "cinematic stylized 3D family animation, stable camera, colorful spaceship interior."
        )
        result = client.predict(
            input_image=handle_file(str(wan_reference)),
            prompt=wan_prompt,
            steps=4,
            negative_prompt=(
                "low quality, flicker, jitter, deformed face, extra limbs, changed clothes, "
                "missing red cap, missing rocket backpack, text, watermark, scene cuts"
            ),
            duration_seconds=3.5,
            guidance_scale=1,
            guidance_scale_2=1,
            seed=serial,
            randomize_seed=False,
            api_name="/generate_video",
        )
        video_path = result[0] if isinstance(result, (tuple, list)) else result
        if isinstance(video_path, dict):
            video_path = video_path.get("path") or video_path.get("name")
        if not video_path or not Path(video_path).is_file():
            raise RuntimeError(f"Wan no devolvió un MP4 válido: {video_path!r}")
        shutil.copy2(video_path, wan_raw)

        # Replace only seconds 2.0–5.5 of the Blender master. Keep the complete
        # episode at 60 seconds and normalize all segments to the same H.264 profile.
        part_a = TMP / "hybrid-a.mp4"
        part_b = TMP / "hybrid-b.mp4"
        part_c = TMP / "hybrid-c.mp4"
        def normalize_segment(source, destination, start=None, duration=None):
            command = ["ffmpeg", "-y"]
            if start is not None:
                command += ["-ss", str(start)]
            command += ["-i", str(source)]
            if duration is not None:
                command += ["-t", str(duration)]
            command += [
                "-an", "-vf",
                "fps=30,scale=720:1280:force_original_aspect_ratio=increase,"
                "crop=720:1280,setsar=1",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart",
                str(destination),
            ]
            run(command, quiet=True)

        normalize_segment(original_video, part_a, 0, 2.0)
        normalize_segment(wan_raw, part_b, None, 3.5)
        normalize_segment(original_video, part_c, 5.5, 54.5)
        concat_list = TMP / "hybrid-list.txt"
        concat_list.write_text(
            "".join(f"file '{p.resolve()}'\n" for p in (part_a, part_b, part_c)),
            encoding="utf-8",
        )
        hybrid = TMP / "coco-base-hybrid.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
             str(concat_list), "-c", "copy", str(hybrid)], quiet=True)
        if not hybrid.is_file() or hybrid.stat().st_size < 100_000:
            raise RuntimeError("El montaje híbrido Wan + Blender no produjo un MP4 válido.")
        BASE_VIDEO = hybrid
        WAN_STATUS = "one_3.5s_wan22_lightning_shot"
        print("WAN_ENHANCEMENT_VALIDATED=1", flush=True)
    except Exception as exc:
        WAN_STATUS = f"fallback_blender: {type(exc).__name__}: {exc}"
        BASE_VIDEO = TMP / "coco-base.mp4"
        print(f"WAN_ENHANCEMENT_FALLBACK={WAN_STATUS}", flush=True)
else:
    WAN_STATUS = "skipped_no_HF_TOKEN"
    print("WAN_ENHANCEMENT_SKIPPED=HF_TOKEN no configurado; se conserva Blender.", flush=True)

# Validate the final base timeline after optional enhancement.
hybrid_probe = json.loads(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(BASE_VIDEO)],
    text=True,
))
hybrid_stream = next(st for st in hybrid_probe["streams"] if st.get("codec_type") == "video")
hybrid_duration = float(hybrid_probe["format"]["duration"])
if not (59.5 <= hybrid_duration <= 60.5 and hybrid_stream.get("width") == 720
        and hybrid_stream.get("height") == 1280):
    raise RuntimeError(f"La base final no cumple 60 s y 720x1280: {hybrid_duration}s.")


# Narration: a separate Mexican Spanish neural voice segment for each 5-second beat.
voice_rms = []
voice_engines = []
voice_list = OUT / "voice-list.txt"
for index, line in enumerate(lines):
    mp3 = AUDIO / f"voice-{index + 1:02d}.mp3"
    wav = AUDIO / f"voice-{index + 1:02d}.wav"
    engine = "edge-tts-es-MX-DaliaNeural"
    try:
        subprocess.run([
            "edge-tts", "--voice", "es-MX-DaliaNeural", "--rate=+12%",
            "--text", line, "--write-media", str(mp3),
        ], check=True, timeout=45, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if not mp3.is_file() or mp3.stat().st_size < 1000:
            raise RuntimeError("Edge TTS devolvió un archivo vacío.")
        run([
            "ffmpeg", "-y", "-i", str(mp3), "-af", "apad", "-t", str(SLOT),
            "-ar", "44100", "-ac", "2", str(wav),
        ], quiet=True)
    except (subprocess.SubprocessError, FileNotFoundError, RuntimeError) as exc:
        # Fallback offline: the episode can still render when the free cloud voice is down.
        engine = "espeak-ng-offline-es"
        fallback_wav = AUDIO / f"voice-{index + 1:02d}-offline.wav"
        run(["espeak-ng", "-v", "es", "-s", "165", "-w", str(fallback_wav), line])
        run([
            "ffmpeg", "-y", "-i", str(fallback_wav), "-af", "apad", "-t", str(SLOT),
            "-ar", "44100", "-ac", "2", str(wav),
        ], quiet=True)
        print(f"VOICE_FALLBACK=scene-{index + 1}: {exc}", flush=True)
    voice_engines.append(engine)
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

# Timed subtitles: SRT sidecar plus ASS with an explicit lower-safe-area anchor.
def ass_stamp(seconds):
    centiseconds = int(round(seconds * 100))
    hours = centiseconds // 360000
    minutes = (centiseconds // 6000) % 60
    secs = (centiseconds // 100) % 60
    fraction = centiseconds % 100
    return f"{hours}:{minutes:02d}:{secs:02d}.{fraction:02d}"

srt_entries = []
ass_entries = []
for index, line in enumerate(lines):
    caption_lines = textwrap.wrap(
        line, width=36, break_long_words=False, break_on_hyphens=False
    ) or [line]
    if len(caption_lines) > 3:
        raise RuntimeError(f"La escena {index + 1} excede tres líneas de subtítulos.")
    srt_caption = "\n".join(caption_lines)
    ass_caption = r"\N".join(caption_lines).replace("{", "\\{").replace("}", "\\}")
    srt_entries.append(
        f"{index + 1}\n{stamp(index * SLOT)} --> {stamp((index + 1) * SLOT)}\n{srt_caption}\n"
    )
    ass_entries.append(
        f"Dialogue: 0,{ass_stamp(index * SLOT)},{ass_stamp((index + 1) * SLOT)},"
        f"Coco,,0,0,0,,{{\\an2\\pos(540,1640)\\q2}}{ass_caption}"
    )

srt_path = OUT / "subtitles.srt"
srt_path.write_text("\n".join(srt_entries), encoding="utf-8")
if len([entry for entry in srt_path.read_text(encoding="utf-8").split("\n\n") if "-->" in entry]) != 12:
    raise RuntimeError("El archivo SRT no contiene las 12 escenas esperadas.")

ass_path = OUT / "subtitles.ass"
ass_header = [
    "[Script Info]",
    "ScriptType: v4.00+",
    "PlayResX: 1080",
    "PlayResY: 1920",
    "WrapStyle: 2",
    "ScaledBorderAndShadow: yes",
    "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: Coco,DejaVu Sans,42,&H00FFFFFF,&H000000FF,&H00101830,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,110,110,280,1",
    "",
    "[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
]
ass_path.write_text("\n".join(ass_header + ass_entries) + "\n", encoding="utf-8")
if len(ass_entries) != 12:
    raise RuntimeError("El archivo ASS no contiene las 12 escenas esperadas.")

# Final portrait master: 1080x1920, 30 fps, Mexican Spanish narration and original score.
# Explicit ASS positioning avoids the top-clipped SRT placement seen in the previous render.
subtitle_filter = (
    "scale=1080:1920:flags=lanczos,fps=30,"
    "subtitles=output/subtitles.ass"
)
run([
    "ffmpeg", "-y", "-i", str(BASE_VIDEO), "-i", str(voice), "-i", str(music_path),
    "-filter_complex",
    "[1:a]volume=1.0[v];[2:a]volume=0.18[m];"
    "[v][m]amix=inputs=2:duration=longest:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=7[a]",
    "-vf", subtitle_filter,
    "-map", "0:v", "-map", "[a]", "-t", str(DURATION),
    "-metadata", f"title={title}",
    "-metadata", "comment=Coco, el Monito Espacial | animación 3D diaria",
    "-c:v", "libx264", "-preset", "medium", "-crf", "17",
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

# Measure the encoded mix with EBU R128; reject a technically present but too-quiet track.
loudness_check = subprocess.run(
    ["ffmpeg", "-hide_banner", "-nostats", "-i", str(FINAL_VIDEO), "-vn",
     "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
    check=True, capture_output=True, text=True,
)
loudness_log = loudness_check.stderr
integrated_match = re.search(
    r"Integrated loudness:\s*I:\s*(-?\d+(?:\.\d+)?) LUFS", loudness_log
)
true_peak_match = re.search(
    r"True peak:\s*Peak:\s*(-?\d+(?:\.\d+)?) dBFS", loudness_log
)
if not integrated_match or not true_peak_match:
    raise RuntimeError("FFmpeg no devolvió mediciones EBU R128 completas.")
integrated_lufs = float(integrated_match.group(1))
true_peak_dbfs = float(true_peak_match.group(1))
if not -18.0 <= integrated_lufs <= -14.0:
    raise RuntimeError(f"Volumen integrado fuera del objetivo: {integrated_lufs:.1f} LUFS.")
if true_peak_dbfs > -1.0:
    raise RuntimeError(f"True peak demasiado alto: {true_peak_dbfs:.1f} dBFS.")

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
    "narration_voice": sorted(set(voice_engines)),
    "narration_segments_rms": voice_rms,
    "final_audio_rms": round(final_rms, 1),
    "integrated_loudness_lufs": round(integrated_lufs, 1),
    "true_peak_dbfs": round(true_peak_dbfs, 1),
    "loudness_target_lufs": -16.0,
    "music": "original synthesized melody; no paid or licensed track",
    "subtitles": "12 Spanish captions burned into the MP4 using positioned ASS plus separate SRT",
    "subtitle_ass": ass_path.name,
    "subtitle_layout": "bottom-center safe area at x=540,y=1640; manually wrapped to at most 3 lines",
    "animation": "Blender EEVEE procedural 3D character animation",
    "wan22_enhancement": WAN_STATUS,
    "render_source": "720x1280 at native 15 fps with 8 EEVEE temporal samples; encoded to 1080x1920 at 30 fps",
    "motion_validation": "6 sampled timestamps; at least 4 distinct frame hashes",
    "character_design": "brown monkey, bright red cap, white astronaut suit, silver rocket backpack; procedural adaptation of the official reference's key identifiers",
    "reference_image": {"file": REFERENCE.name, "dimensions": reference_size, "downloaded": reference_downloaded, "required": False},
    "identity_source": "Versioned procedural Blender character; private reference is optional.",
    "story_library": len(STORY_SPECS),
    "story_rotation": f"150 unique combinations; coprime permutation step={STORY_ROTATION_STEP} changes guest, destination, obstacle and solution between adjacent runs",
    "status": "verified",
}
(OUT / "production-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    f"DAILY_VIDEO_READY={FINAL_VIDEO} duration={duration:.3f} "
    f"resolution={WIDTH}x{HEIGHT} fps={video_stream['avg_frame_rate']} title={title}",
    flush=True,
)
