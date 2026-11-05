import os, subprocess, json, math, wave, random
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT=Path("output"); FRAMES=OUT/"frames"; AUDIO=OUT/"audio"
OUT.mkdir(exist_ok=True); FRAMES.mkdir(exist_ok=True); AUDIO.mkdir(exist_ok=True)
W,H=1080,1920; FPS=30; SLOT=5
DAY=datetime.now(timezone.utc).strftime("%Y-%m-%d")
# 30 combinaciones narrativas deterministas: evita repetir cada tres días.
MYSTERIES=[
("La campana lunar","una campana que suena debajo del polvo lunar","un pequeño robot afinador","una lluvia de meteoritos","escuchar con atención"),
("El faro de cristal","un faro apagado en un planeta de hielo","una luciérnaga espacial","un puente de cristales","trabajar en equipo"),
("El bosque flotante","un bosque de árboles que viaja sin rumbo","una tortuga astronauta","una corriente de viento solar","cuidar la naturaleza"),
("El tren de cometas","un tren de cometas que perdió su estación","un zorro piloto","un cruce de caminos luminosos","mantener la calma"),
("La ciudad diminuta","una ciudad pequeñita escondida en un asteroide","una inventora marciana","una puerta demasiado pesada","ayudar sin rendirse"),
("El jardín de colores","un jardín espacial que está perdiendo sus colores","un colibrí galáctico","una nube que absorbe la luz","compartir lo que tenemos")
]
DESTINATIONS=["el valle de los anillos","la estación Arcoíris","el cráter de los susurros","el océano de estrellas","la montaña de polvo azul"]
def make_story(mystery, destination, serial):
 name, clue, friend, obstacle, lesson=mystery
 title=f"{name}: misión {serial:02d}"
 lines=[
 f"¡Alerta espacial! Coco recibe una señal sobre {clue}.",
 f"La señal marca una ruta hacia {destination}.",
 "Coco ajusta su gorra roja y revisa su mochila cohete.",
 f"Al llegar, conoce a {friend}, que necesita una mano.",
 f"Pero {obstacle} bloquea el camino y la misión parece difícil.",
 "Coco respira profundo y observa cada detalle con cuidado.",
 "Encuentra una pista brillante escondida junto a una roca.",
 "La pista muestra cómo avanzar sin poner a nadie en peligro.",
 f"Coco y su nuevo amigo resuelven juntos el misterio de {clue}.",
 "Una luz cálida recorre el lugar y todo vuelve a la calma.",
 "Su amigo celebra y acompaña a Coco de regreso a casa.",
 f"¡Misión cumplida! Hoy Coco aprende a {lesson}."
 ]
 return (title,lines)
STORIES=[make_story(MYSTERIES[i%len(MYSTERIES)],DESTINATIONS[i//len(MYSTERIES)],i+1) for i in range(30)]
idx=(int(DAY.replace("-","")))%len(STORIES)
title, lines=STORIES[idx]

ref=Image.open("coco-referencia.webp").convert("RGBA")
font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font=ImageFont.truetype(font_path,40); small=ImageFont.truetype(font_path,30)
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
 px=[850,220,780,300,900,180][i%6]; py=420+(i%4)*105
 d.ellipse((px-125,py-125,px+125,py+125),fill=(70,135,220,180),outline=(190,225,255,230),width=8)
 d.ellipse((px-165,py-42,px+165,py+42),outline=(190,220,255,180),width=9)
 character=fit(ref.copy(),([650,720,590,760][i%4], [780,860,700,900][i%4]))
 panel=Image.new("RGBA",(850,1000),(255,255,255,18))
 canvas.alpha_composite(panel,(115,650))
 cx=[130,430,80,350,210,470][i%6]; cy=[760,690,820,730,660,780][i%6]
 canvas.alpha_composite(character,(cx,cy))
 d=ImageDraw.Draw(canvas)
 d.rounded_rectangle((55,65,1025,230),radius=38,fill=(5,10,35,190),outline=(110,190,255,190),width=4)
 d.text((90,105),f"COCO • AVENTURA {i+1:02d}/12",font=small,fill=(120,225,255))
 headline=line
 d.rounded_rectangle((55,1435,1025,1850),radius=42,fill=(4,9,30,225),outline=(255,255,255,120),width=3)
 wrapped=[]; cur=""
 chosen=font
 for sz in (40,38,36,34,32,30):
  chosen=ImageFont.truetype(font_path,sz); wrapped=[]; cur=""
  for word in headline.split():
   test=(cur+" "+word).strip()
   if d.textbbox((0,0),test,font=chosen)[2] > 870:
    if cur: wrapped.append(cur)
    cur=word
   else: cur=test
  if cur: wrapped.append(cur)
  if len(wrapped)<=4: break
 yy=1480; line_h=76 if chosen.size>=36 else 68
 for part in wrapped[:4]:
  d.text((95,yy),part,font=chosen,fill="white",stroke_width=2,stroke_fill=(10,20,55)); yy+=line_h
 d.text((90,1790),"COCO, EL MONITO ESPACIAL",font=small,fill=(255,205,90))
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
(OUT/"production-report.json").write_text(json.dumps({"date":DAY,"title":title,"duration":dur,"resolution":"1080x1920","fps":v["avg_frame_rate"],"voice":"es-MX-DaliaNeural","music":"original synthesized","captions":"complete scene text burned into visuals + separate SRT","story_library":len(STORIES),"visual_variation":"30 story combinations; varied character scale and position; varied backgrounds","status":"verified"},ensure_ascii=False,indent=2))
print(f"DAILY_VIDEO_READY={final} duration={dur} title={title}")
