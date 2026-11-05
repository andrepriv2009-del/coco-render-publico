import os, subprocess, json, math, wave, random
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT=Path("output"); FRAMES=OUT/"frames"; AUDIO=OUT/"audio"
OUT.mkdir(exist_ok=True); FRAMES.mkdir(exist_ok=True); AUDIO.mkdir(exist_ok=True)
W,H=1080,1920; FPS=30; SLOT=5
DAY=datetime.now(timezone.utc).strftime("%Y-%m-%d")
STORIES=[
("La brújula de las estrellas",[
"¡Tripulación, Coco encontró una brújula que apunta a una estrella perdida!",
"Pero la brújula solo funciona cuando alguien dice la verdad.",
"Coco revisa su mochila y encuentra una pequeña pista brillante.",
"Una nube espacial cubre el camino y todo queda oscuro.",
"Entonces Coco enciende su cohete y descubre un sendero secreto.",
"Al final del sendero hay un planeta lleno de flores luminosas.",
"Una estrella pequeñita está escondida entre las flores.",
"Coco la escucha: tiene miedo de volar sola.",
"Le enseña que ser valiente también significa pedir ayuda.",
"Juntos suben despacito por el cielo violeta.",
"La estrella encuentra su lugar y enciende todo el firmamento.",
"¡Misión cumplida! Coco descubre que ayudar ilumina el universo."
]),
("El planeta que estornudaba",[
"¡Atención! Coco recibe una señal de un planeta que no deja de estornudar.",
"Cada estornudo lanza burbujas gigantes por el espacio.",
"Coco se acerca con cuidado y activa su casco protector.",
"Un remolino de burbujas lo hace girar como trompo.",
"Con paciencia, descubre que el planeta tiene polvo de cometa.",
"Coco prepara un ventilador con su mochila cohete.",
"Pero necesita encontrar la flor espacial que limpia el aire.",
"Una lucecita lo guía hasta un pequeño cráter.",
"Allí crece una flor azul que brilla con cada soplido.",
"Coco la coloca cerca del planeta y espera.",
"¡Achís! El planeta da su último estornudo y vuelve a sonreír.",
"Coco aprende que cuidar el espacio también es cuidar a los demás."
]),
("El mapa invisible",[
"Hoy Coco encuentra un mapa que solo aparece bajo la luz de las estrellas.",
"Una ruta brillante señala un lugar que nadie ha visitado.",
"Coco ajusta su gorra roja y despega con emoción.",
"El mapa cambia de forma y lo lleva entre asteroides.",
"Una roca enorme bloquea el camino.",
"Coco observa, piensa y encuentra un túnel seguro.",
"Al otro lado descubre una puerta hecha de luz.",
"El mapa revela que la llave es una sonrisa sincera.",
"Coco sonríe y la puerta se abre lentamente.",
"Detrás hay un jardín secreto flotando en el espacio.",
"Las estrellas del jardín iluminan el camino de regreso.",
"¡Qué aventura! Coco guarda el mapa para ayudar a otro explorador."
])
]
idx=(int(DAY.replace("-","")))%len(STORIES)
title, lines=STORIES[idx]
ref=Image.open("coco-referencia.webp").convert("RGBA")
font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font=ImageFont.truetype(font_path,52); small=ImageFont.truetype(font_path,34)
def gradient(top,bottom):
 im=Image.new("RGB",(W,H)); p=im.load()
 for y in range(H):
  t=y/(H-1)
  c=tuple(int(top[k]*(1-t)+bottom[k]*t) for k in range(3))
  for x in range(W): p[x,y]=c
 return im
pal=[((8,15,48),(45,20,92)),((7,35,65),(15,95,115)),((35,12,58),(105,35,95)),((9,28,62),(22,65,120))]
def fit(im,size):
 im.thumbnail(size,Image.Resampling.LANCZOS); return im
for i,line in enumerate(lines):
 top,bottom=pal[i%len(pal)]; canvas=gradient(top,bottom).convert("RGBA"); d=ImageDraw.Draw(canvas)
 random.seed(i+int(DAY[-2:]))
 for _ in range(95):
  x=random.randrange(W); y=random.randrange(H); r=random.choice([2,3,4,6])
  d.ellipse((x-r,y-r,x+r,y+r),fill=(210,230,255,random.randrange(90,230)))
 px=850 if i%2==0 else 220; py=520+(i%3)*90
 d.ellipse((px-125,py-125,px+125,py+125),fill=(70,135,220,180),outline=(190,225,255,230),width=8)
 d.ellipse((px-165,py-42,px+165,py+42),outline=(190,220,255,180),width=9)
 character=fit(ref.copy(),(760,900))
 panel=Image.new("RGBA",(850,1000),(255,255,255,18))
 canvas.alpha_composite(panel,(115,650))
 canvas.alpha_composite(character,((W-character.width)//2,700+(i%2)*25))
 d=ImageDraw.Draw(canvas)
 d.rounded_rectangle((55,65,1025,230),radius=38,fill=(5,10,35,190),outline=(110,190,255,190),width=4)
 d.text((90,105),f"COCO • AVENTURA {i+1:02d}/12",font=small,fill=(120,225,255))
 words=line.split(); headline=" ".join(words[:8])
 d.rounded_rectangle((55,1510,1025,1845),radius=42,fill=(4,9,30,220),outline=(255,255,255,100),width=3)
 wrapped=[]; cur=""
 for word in headline.split():
  test=(cur+" "+word).strip()
  if d.textbbox((0,0),test,font=font)[2] > 870:
   wrapped.append(cur); cur=word
  else: cur=test
 if cur: wrapped.append(cur)
 yy=1580
 for part in wrapped[:3]:
  d.text((95,yy),part,font=font,fill="white",stroke_width=2,stroke_fill=(10,20,55)); yy+=78
 d.text((90,1770),"COCO, EL MONITO ESPACIAL",font=small,fill=(255,205,90))
 canvas.convert("RGB").save(FRAMES/f"scene-{i+1:02d}.jpg",quality=94)
clips=[]
for i in range(12):
 src=FRAMES/f"scene-{i+1:02d}.jpg"; dst=OUT/f"clip-{i+1:02d}.mp4"
 subprocess.run(["ffmpeg","-y","-loop","1","-i",str(src),"-t","5","-vf","zoompan=z='min(zoom+0.00035,1.055)':d=150:s=1080x1920:fps=30,format=yuv420p","-an","-c:v","libx264","-preset","veryfast","-crf","20",str(dst)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 clips.append(dst)
concat=OUT/"concat.txt"; concat.write_text("".join(f"file '{p.resolve()}'\n" for p in clips))
silent=OUT/"silent.mp4"
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for i,line in enumerate(lines):
 subprocess.run(["edge-tts","--voice","es-MX-DaliaNeural","--rate=+12%","--text",line,"--write-media",str(AUDIO/f"v{i:02d}.mp3")],check=True)
 subprocess.run(["ffmpeg","-y","-i",str(AUDIO/f"v{i:02d}.mp3"),"-af","apad","-t","5","-ar","44100","-ac","2",str(AUDIO/f"v{i:02d}.wav")],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
lst=OUT/"voice-list.txt"; lst.write_text("".join(f"file '{(AUDIO/f'v{i:02d}.wav').resolve()}'\n" for i in range(12)))
voice=OUT/"voice.wav"
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),"-t","60",str(voice)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
sr=44100; t=np.arange(sr*60,dtype=np.float32)/sr; music=np.zeros_like(t)
for f in (220.0,261.63,329.63,392.0): music += np.sin(2*np.pi*f*t).astype(np.float32)*0.012
env=np.minimum(t/2,1)*np.minimum((60-t)/2,1); music*=env
st=np.stack([music,music],axis=1)
with wave.open(str(OUT/"music.wav"),"wb") as f:
 f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr); f.writeframes((np.clip(st,-1,1)*32767).astype("<i2").tobytes())
srt=[]
for i,line in enumerate(lines):
 def stamp(s): return f"00:{s//60:02d}:{s%60:02d},000"
 srt.append(f"{i+1}\n{stamp(i*5)} --> {stamp((i+1)*5)}\n{line}\n")
(OUT/"subtitles.srt").write_text("\n".join(srt),encoding="utf-8")
final=OUT/"Coco-Short-60s-FINAL.mp4"
subprocess.run(["ffmpeg","-y","-i",str(silent),"-i",str(voice),"-i",str(OUT/"music.wav"),
 "-filter_complex","[1:a]volume=1.0[v];[2:a]volume=0.16[m];[v][m]amix=inputs=2:duration=longest:dropout_transition=0,alimiter=limit=0.95[a]",
 "-map","0:v","-map","[a]","-t","60","-metadata",f"title={title}","-metadata","comment=Coco, el Monito Espacial | episodio diario","-c:v","libx264","-preset","medium","-crf","19","-c:a","aac","-b:a","192k","-pix_fmt","yuv420p","-movflags","+faststart",str(final)],check=True)
probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(final)],text=True))
v=next(s for s in probe["streams"] if s["codec_type"]=="video"); a=next(s for s in probe["streams"] if s["codec_type"]=="audio")
dur=float(probe["format"]["duration"])
assert 59.8<=dur<=60.2 and v["width"]==1080 and v["height"]==1920 and a
(OUT/"production-report.json").write_text(json.dumps({"date":DAY,"title":title,"duration":dur,"resolution":"1080x1920","fps":v["avg_frame_rate"],"voice":"es-MX-DaliaNeural","music":"original synthesized","captions":"scene text burned into visuals + separate SRT","status":"verified"},ensure_ascii=False,indent=2))
print(f"DAILY_VIDEO_READY={final} duration={dur} title={title}")
