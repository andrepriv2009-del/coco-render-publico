import bpy, math, os, json, re
from mathutils import Vector
from math import radians

OUT = "/tmp/coco-render"
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.eevee.use_gtao=True
scene.eevee.gtao_distance=3
scene.eevee.gtao_factor=1.35
scene.render.resolution_x=720; scene.render.resolution_y=1280; scene.render.resolution_percentage=75
# Free CPU-render profile: 540x960 at 15 fps, then upscale to 1080x1920/30 fps.
# Motion keyframes are stretched below so the animation still lasts exactly 60 seconds.
if hasattr(scene.eevee, "taa_render_samples"):
 scene.eevee.taa_render_samples=8
scene.render.fps=15; scene.frame_start=1; scene.frame_end=900
scene.render.image_settings.file_format="FFMPEG"
scene.render.ffmpeg.format="MPEG4"
scene.render.ffmpeg.codec="H264"
scene.render.ffmpeg.constant_rate_factor="MEDIUM"
scene.render.ffmpeg.ffmpeg_preset="REALTIME"
scene.render.film_transparent=False
scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.006,0.009,0.035,1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.32
scene.view_settings.view_transform="Standard"
scene.view_settings.look="Medium High Contrast"
scene.display.shading.light="STUDIO"

def mat(name,color,metal=0,rough=.45,emission=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get("Principled BSDF"); p.inputs["Base Color"].default_value=(*color,1)
 p.inputs["Metallic"].default_value=metal; p.inputs["Roughness"].default_value=rough
 if emission:
  p.inputs["Emission Color"].default_value=(*color,1); p.inputs["Emission Strength"].default_value=emission
 return m
brown=mat("Pelaje café cálido",(0.34,.13,.055),rough=.82)
beige=mat("Hocico y rostro beige",(.88,.62,.36),rough=.8)
red=mat("Gorra roja característica",(.8,.018,.035),rough=.3)
silver=mat("Mochila cohete plateada",(.48,.62,.75),metal=.72,rough=.25)
blue=mat("Cristal azul",(.03,.48,.95),metal=.3,rough=.2,emission=.5)
white=mat("Ojos blancos",(.98,.98,1),rough=.18)
black=mat("Pupilas",(.008,.012,.025),rough=.12)
gold=mat("Estrella dorada",(1,.58,.035),metal=.15,rough=.22,emission=1.4)
purple=mat("Nebulosa violeta",(.12,.035,.3),rough=.9)
planetmat=mat("Planeta turquesa",(.025,.35,.47),rough=.75)
def uv(name,loc,scale,material,segments=32):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=20,location=loc)
 o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.shade_smooth()
 if material:o.data.materials.append(material)
 return o
def cyl(name,loc,radius,depth,material,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=loc,rotation=rot)
 o=bpy.context.object;o.name=name;o.data.materials.append(material);bpy.ops.object.shade_smooth();return o
# Camera and cinematic lighting
bpy.ops.object.camera_add(location=(4,-20,1.0))
cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler(); cam.data.type="ORTHO";cam.data.ortho_scale=8.6;scene.camera=cam
def area(name,loc,power,color,size):
 bpy.ops.object.light_add(type="AREA",location=loc); l=bpy.context.object;l.name=name;l.data.energy=power;l.data.color=color;l.data.shape="DISK";l.data.size=size
 l.rotation_euler=(Vector((0,0,0))-l.location).to_track_quat("-Z","Y").to_euler()
area("Luz principal cálida",(-6,-8,8),1500,(1,.72,.48),7)
area("Relleno azul",(6,-5,1),1100,(.28,.48,1),6)
area("Rim violeta",(0,4,7),1800,(.42,.25,1),5)
# Deep-space backdrop and starfield
uv("Planeta lejano",(5,5,5),(2.8,.9,2.8),purple)
for i in range(105):
 x=((i*73)%191-95)/12; z=((i*47)%157-78)/12
 s=.025+((i*13)%8)*.009
 uv("Estrella de fondo",(x,3.5,z),(s,s,s),gold if i%11==0 else white,12)
# Layered storybook space set: luminous planets, orbital rings and colorful nebulae.
uv("Planeta azul",(5,1,-4),(1.5,.6,1.5),planetmat)
uv("Luna",( -5,2,4),(.85,.45,.85),silver)
nebula_a=uv("Nebulosa coral",(-4.8,4.2,-1.0),(2.8,.22,2.0),mat("Nebulosa coral material",(.24,.035,.16),rough=1,emission=.18))
nebula_b=uv("Nebulosa azul",(4.5,4.5,1.8),(2.6,.2,1.7),mat("Nebulosa azul material",(.025,.10,.30),rough=1,emission=.22))
for name,loc,major,minor,material,rot in [("Órbita dorada",(5,1,-4),2.0,.045,gold,(radians(62),0,radians(-20))),("Órbita turquesa",(-5,1,4),1.15,.035,blue,(radians(68),0,radians(18)))]:
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=72,minor_segments=12,location=loc)
    orbit=bpy.context.object;orbit.name=name;orbit.data.materials.append(material);orbit.rotation_euler=rot
    orbit.keyframe_insert(data_path="rotation_euler",frame=1)
    orbit.rotation_euler[2]+=radians(24);orbit.keyframe_insert(data_path="rotation_euler",frame=720)
# Coco rig built from carefully layered rounded forms
root=bpy.data.objects.new("COCO_RIG",None);scene.collection.objects.link(root)
def parent(o):o.parent=root;return o
parent(uv("Cuerpo de Coco",(0,0,-1.35),(.72,.58,.9),brown))
parent(uv("Cabeza de Coco",(0,-.03,.05),(1.0,.72,1.02),brown))
# ears
for x in (-.93,.93):
 parent(uv("Oreja",(x,-.03,.15),(.34,.28,.43),brown))
 parent(uv("Interior oreja",(x,-.285,.15),(.19,.07,.27),beige))
# cheeks, muzzle and nose
parent(uv("Parche facial",(0,-.655,-.16),(.72,.19,.52),beige))
for x in (-.28,.28):
 parent(uv("Ojo",(x,-.78,.25),(.22,.12,.29),white))
 parent(uv("Pupila",(x+.035,-.89,.23),(.105,.055,.17),black))
 parent(uv("Brillo ojo",(x+.065,-.935,.31),(.045,.025,.06),white,16))
parent(uv("Hocico",(0,-.83,-.22),(.34,.15,.22),beige))
parent(uv("Nariz",(0,-.975,-.12),(.105,.06,.07),black,20))
# smile curve
def curve(name,points,bevel,material):
 c=bpy.data.curves.new(name,"CURVE");c.dimensions="3D";c.bevel_depth=bevel;c.bevel_resolution=4
 sp=c.splines.new("BEZIER");sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type="AUTO";p.handle_right_type="AUTO"
 o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.data.materials.append(material);return o
parent(curve("Sonrisa", [(-.22,-.965,-.32),(0,-1.005,-.39),(.22,-.965,-.32)],.025,black))
# Expressive face details: soft cheeks, brows and a brighter smile.
for x in (-.48,.48):
    parent(uv("Mejilla rosada",(x,-.805,-.25),(.16,.045,.10),mat("Rubor suave "+str(x),(1,.34,.29),rough=.8),20))
for x in (-.28,.28):
    brow=parent(curve("Ceja expresiva",[(x-.15,-.79,.57),(x,-.82,.63),(x+.15,-.79,.57)],.035,brown))
# Small teeth visible inside the smiling mouth.
parent(uv("Diente sonrisa",(0,-1.015,-.335),(.105,.018,.025),white,16))
# White astronaut suit layered over the torso, with red seams and chest badge.
parent(uv("Traje espacial blanco",(0,-.49,-1.40),(.68,.17,.72),white))
for x in (-.48,.48):
    parent(uv("Hombrera roja",(x,-.55,-.91),(.20,.16,.20),red))
    parent(uv("Guante espacial",(x*1.48,-.18,-1.25),(.25,.24,.22),white))
parent(uv("Panel del traje",(0,-.675,-1.34),(.27,.055,.25),silver))
parent(uv("Pantalla azul del traje",(0,-.727,-1.30),(.17,.025,.13),blue))
parent(uv("Insignia estrella",(0,-.73,-1.53),(.075,.025,.075),gold,16))
# Red suit piping down the front.
for x in (-.38,.38):
    parent(curve("Costura roja traje",[(x,-.63,-1.05),(x*1.08,-.65,-1.38),(x,-.62,-1.72)],.025,red))
# red cap: crown, brim, tiny rocket emblem
parent(uv("Gorra roja",(0,-.02,.91),(.86,.65,.34),red))
parent(uv("Visera roja",(0,-.55,.77),(.72,.38,.12),red))
parent(uv("Emblema cohete",(0,-.69,.99),(.13,.045,.17),gold,20))
# backpack and rocket details behind shoulder
parent(uv("Mochila cohete",(0,.58,-.9),(.57,.35,.72),silver))
for x in (-.4,.4):
 parent(cyl("Propulsor",(x,.59,-1.42),.16,.55,silver))
 parent(uv("Llama azul",(x,.59,-1.76),(.13,.15,.28),blue))
# Rocket backpack silhouette details and glowing exhaust rings.
for x in (-.4,.4):
    parent(cyl("Aro de propulsor",(x,.59,-1.30),.19,.10,gold))
    parent(uv("Aleta cohete",(x*1.45,.56,-.83),(.16,.20,.34),red))
# arms and hands
for x in (-.72,.72):
 arm=parent(uv("Brazo",(x*1.18,-.03,-.85),(.23,.28,.58),brown));arm.rotation_euler[1]=x*.45
 parent(uv("Mano",(x*1.38,-.1,-1.2),(.25,.25,.24),beige))
# Character acting upgrade: walk cycle, gestures, blinking and talking
# Pivot-based legs so Coco visibly walks instead of only sliding across frame.
for side, x in [("izquierda",-.38),("derecha",.38)]:
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(x,0,-1.82))
    hip=bpy.context.object; hip.name="Cadera "+side; hip.parent=root
    leg=uv("Pierna "+side,(x,0,-2.18),(.24,.30,.52),brown)
    leg.parent=hip; leg.matrix_parent_inverse=hip.matrix_world.inverted()
    boot=uv("Bota "+side,(x,-.12,-2.52),(.29,.36,.20),red)
    boot.parent=hip; boot.matrix_parent_inverse=hip.matrix_world.inverted()
    for f,a in [(1,0),(36,.42),(72,0),(108,-.42),(144,0),(180,.42),(216,0),(252,-.42),(288,0),(324,.42),(360,0),(396,-.42),(432,0),(468,.42),(504,0),(540,-.42),(576,0),(612,.42),(648,0),(684,-.42),(720,0)]:
        hip.rotation_euler[1]=a if side=="izquierda" else -a
        hip.keyframe_insert(data_path="rotation_euler",frame=f)
# Give arms a readable wave and pointing gesture.
arms=[o for o in bpy.data.objects if o.name=="Brazo"]
for idx,arm in enumerate(arms):
    base=arm.rotation_euler[1]
    for f,a in [(1,base),(72,base+(.55 if idx else -.25)),(144,base),(216,base+(.55 if idx else -.25)),(288,base),(360,base+(.55 if idx else -.25)),(432,base),(504,base+(.55 if idx else -.25)),(576,base),(648,base+(.55 if idx else -.25)),(720,base)]:
        arm.rotation_euler[1]=a; arm.keyframe_insert(data_path="rotation_euler",frame=f)
# Talking mouth: a small dark oval opens and closes in time with the narration.
mouth=uv("Boca animada",(0,-.987,-.30),(.17,.035,.045),black,20)
parent(mouth)
for f,z in [(1,.035),(24,.12),(48,.035),(72,.12),(96,.035),(120,.12),(144,.035),(168,.12),(192,.035),(216,.12),(240,.035),(264,.12),(288,.035),(312,.12),(336,.035),(360,.12),(384,.035),(408,.12),(432,.035),(456,.12),(480,.035),(504,.12),(528,.035),(552,.12),(576,.035),(600,.12),(624,.035),(648,.12),(672,.035),(696,.12),(720,.035)]:
    mouth.scale=(.17,.035,z); mouth.keyframe_insert(data_path="scale",frame=f)
# Eye blinks and curious pupil glances.
eyes=[o for o in bpy.data.objects if o.name=="Ojo"]
pupils=[o for o in bpy.data.objects if o.name=="Pupila"]
for eye in eyes:
    for f,z in [(1,.29),(90,.29),(94,.035),(98,.29),(250,.29),(254,.035),(258,.29),(430,.29),(434,.035),(438,.29),(610,.29),(614,.035),(618,.29),(720,.29)]:
        eye.scale=(.22,.12,z); eye.keyframe_insert(data_path="scale",frame=f)
for pupil in pupils:
    base_x=pupil.location.x
    for f,dx in [(1,0),(120,.055),(180,.055),(240,0),(360,-.045),(420,-.045),(480,0),(600,.04),(660,.04),(720,0)]:
        pupil.location.x=base_x+dx
        pupil.keyframe_insert(data_path="location",frame=f)
# Cinematic camera push-in and pull-back during the adventure.
for f,scale in [(1,8.6),(96,8.2),(216,7.9),(360,8.2),(504,7.9),(624,8.2),(720,8.5)]:
    cam.data.ortho_scale=scale; cam.data.keyframe_insert(data_path="ortho_scale",frame=f)
# Animate root movement and gentle bob
for f,loc in [(1,(-.65,0,-.15)),(144,(-.4,0,.05)),(288,(.45,0,.12)),(432,(.65,0,-.08)),(576,(0,0,.05)),(720,(-.15,0,0))]:
 root.location=loc;root.keyframe_insert(data_path="location",frame=f)
 root.rotation_euler[1]=.05*math.sin(f/70);root.keyframe_insert(data_path="rotation_euler",frame=f)
# Animated asteroids and a ringed planet make the environment feel alive.
for idx,(x,z,sz) in enumerate([(-4.4,2.2,.42),(4.5,-1.5,.55),(-3.8,-3.1,.30),(3.8,3.0,.34)]):
    rock=uv("Asteroide viajero "+str(idx),(x,2.0,z),(sz,sz*.7,sz*.85),silver,20)
    for f,dx in [(1,0),(240,.65),(480,-.35),(720,0)]:
        rock.location.x=x+dx
        rock.rotation_euler[1]=dx*.35
        rock.keyframe_insert(data_path="location",frame=f)
        rock.keyframe_insert(data_path="rotation_euler",frame=f)
# Saturn-like ring in the distance.
bpy.ops.mesh.primitive_torus_add(major_radius=1.15,minor_radius=.055,major_segments=64,minor_segments=12,location=(-5,1.5,4))
ring=bpy.context.object; ring.name="Anillo del planeta"; ring.data.materials.append(gold)
ring.rotation_euler=(radians(68),0,radians(-18))
# floating lost star with orbit trail
star=uv("ESTRELLA PERDIDA",(2.6,-1.4,1.8),(.42,.12,.42),gold)
for f,loc in [(1,(2.7,-1.4,1.8)),(144,(3.6,-1.2,2.1)),(288,(1.6,-1.5,1.2)),(432,(-2,-1.4,1.8)),(576,(0,-1.3,2.8)),(720,(2.4,-1.4,1.8))]:
 star.location=loc;star.keyframe_insert(data_path="location",frame=f)
 star.scale=(.42,.12,.42);star.keyframe_insert(data_path="scale",frame=f)
# Gold particles / path
for i in range(15):
 x=-4.5+i*.65
 uv("Destello de ruta",(x,-2.0,(-1)**i*.45),(.045,.045,.045),gold,12)
# Animated light pulses on rocket flame
for obj in [o for o in bpy.data.objects if o.name=="Llama azul"]:
 for f,s in [(1,.7),(36,1.25),(72,.7),(108,1.3),(144,.7),(180,1.2),(216,.7),(252,1.25),(288,.7),(324,1.2),(360,.7),(396,1.25),(432,.7),(468,1.2),(504,.7),(540,1.25),(576,.7),(612,1.2),(648,.7),(684,1.25),(720,.7)]:
  obj.scale=(.13*s,.15*s,.28*s);obj.keyframe_insert(data_path="scale",frame=f)
# Smooth interpolation for cinematic motion
for obj in bpy.data.objects:
 if obj.animation_data and obj.animation_data.action:
  for fc in obj.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation="BEZIER"

# EPISODE-AWARE VISUALS: load the current episode and build its guest character.
episode_path=OUT+"/episode.json"
episode={}
if os.path.exists(episode_path):
    with open(episode_path,encoding="utf-8") as f:
        episode=json.load(f)
episode_title=str(episode.get("title","Una nueva aventura espacial"))[:36]
episode_script=str(episode.get("script",""))
guest_match=re.search(r"FICHA DE PERSONAJE INVITADO\s*[—-]\s*([^\n]+)",episode_script,re.I)
guest_name=guest_match.group(1).strip()[:24] if guest_match else "Amigo espacial"
guest_key=guest_name.lower()
# Episode title and guest label are rendered into the actual 3D scene.
def scene_text(name,body,location,size,material):
    data=bpy.data.curves.new(name,"FONT")
    data.body=body
    data.size=size
    data.align_x="CENTER"
    data.extrude=.004
    obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(radians(90),0,0)
    obj.data.materials.append(material)
    return obj
# No floating labels: narration/subtitles carry the story without covering Coco.
guest_root=bpy.data.objects.new("INVITADO DEL EPISODIO — "+guest_name,None)
scene.collection.objects.link(guest_root)
guest_root.location=(2.05,-.55,-.65)
def guest_part(obj):
    obj.parent=guest_root
    return obj
def guest_ball(name,loc,scale,material):
    return guest_part(uv(name,loc,scale,material,24))
cyan=mat("Turquesa invitado",(0.02,.62,.67),rough=.48)
lilac=mat("Lila invitado",(.62,.35,.82),rough=.72)
lime=mat("Verde lagartija",(.34,.78,.08),rough=.62)
mint=mat("Menta tortuga",(.35,.78,.64),rough=.72)
orange=mat("Naranja invitado",(1,.29,.055),rough=.62)
leaf=mat("Verde planta",(.12,.58,.16),rough=.72)
guest_palette=cyan
if "nuba" in guest_key: guest_palette=lilac
elif "tito" in guest_key: guest_palette=lime
elif "mara" in guest_key: guest_palette=mint
elif "bongo" in guest_key: guest_palette=orange
elif "lila" in guest_key: guest_palette=leaf
# Every episode gets a distinct guest silhouette, palette and animated entrance.
if "pipo" in guest_key:
    guest_ball("Pipo cuerpo robot",(0,0,0),(.48,.38,.58),cyan)
    guest_ball("Pipo cabeza pantalla",(0,-.04,.52),(.46,.30,.38),silver)
    guest_ball("Pipo pantalla",(0,-.315,.52),(.32,.035,.23),blue)
    for ex in (-.13,.13):
        guest_ball("Ojo pantalla Pipo",(ex,-.36,.54),(.045,.025,.06),white)
    guest_part(cyl("Antena Pipo",(0,0,.98),.045,.34,gold))
    guest_ball("Punta antena Pipo",(0,0,1.17),(.10,.10,.10),gold)
elif "nuba" in guest_key:
    for loc,sc in [((0,0,0),(.48,.35,.38)),((-.28,0,.18),(.32,.30,.34)),((.28,0,.18),(.32,.30,.34)),((0,0,.35),(.34,.29,.31))]:
        guest_ball("Nube Nuba",loc,sc,lilac)
    for ex in (-.13,.13):
        guest_ball("Ojo Nuba",(ex,-.31,.10),(.045,.025,.065),black)
    guest_ball("Mejilla Nuba",(-.25,-.30,-.05),(.09,.025,.055),red)
    guest_ball("Mejilla Nuba",(.25,-.30,-.05),(.09,.025,.055),red)
elif "tito" in guest_key:
    guest_ball("Cuerpo Tito",(0,0,0),(.52,.32,.30),lime)
    guest_ball("Cabeza Tito",(.30,-.03,.27),(.30,.27,.28),lime)
    guest_part(curve("Cola espiral Tito",[(.35,.05,-.12),(.72,.05,-.28),(1.0,.05,-.02),(.82,.05,.18)],.075,orange))
    for ex in (.20,.42):
        guest_ball("Ojo Tito",(ex,-.28,.42),(.07,.04,.08),white)
elif "mara" in guest_key:
    guest_ball("Caparazón Mara",(0,.02,0),(.53,.40,.43),lilac)
    guest_ball("Cuerpo Mara",(0,-.02,-.18),(.40,.32,.25),mint)
    guest_ball("Cabeza Mara",(0,-.06,.38),(.27,.25,.27),mint)
    for ex in (-.13,.13):
        guest_ball("Ojo Mara",(ex,-.285,.43),(.045,.025,.06),black)
    for ex in (-.35,.35):
        guest_ball("Pata Mara",(ex,-.02,-.42),(.15,.19,.16),mint)
elif "bongo" in guest_key:
    guest_ball("Cuerpo Bongo",(0,0,0),(.50,.38,.55),orange)
    for ex in (-.30,.30):
        ear=guest_ball("Oreja Bongo",(ex,0,.48),(.14,.16,.40),orange)
        ear.rotation_euler[1]=ex*.7
        guest_ball("Bota Bongo",(ex,-.02,-.52),(.19,.28,.16),blue)
    for ex in (-.15,.15):
        guest_ball("Ojo Bongo",(ex,-.34,.16),(.06,.03,.08),white)
elif "lila" in guest_key:
    guest_part(cyl("Tallo Lila",(0,0,.05),.10,.72,leaf))
    for ex in (-.32,.32):
        leaf_obj=guest_ball("Hoja Lila",(ex,0,.22),(.30,.12,.15),leaf)
        leaf_obj.rotation_euler[1]=ex
    guest_ball("Flor Lila",(0,0,.52),(.23,.18,.22),gold)
    guest_ball("Centro flor Lila",(0,-.17,.52),(.09,.04,.09),orange)
else:
    guest_ball("Amigo espacial",(0,0,0),(.48,.38,.52),guest_palette)
    guest_ball("Cara amigo",(0,-.33,.12),(.28,.06,.22),beige)
    for ex in (-.12,.12):
        guest_ball("Ojo amigo",(ex,-.39,.18),(.045,.025,.06),black)
# A small story prop changes with the episode theme.
if "brújula" in episode_title.lower() or "brujula" in episode_title.lower():
    bpy.ops.mesh.primitive_torus_add(major_radius=.38,minor_radius=.055,major_segments=32,minor_segments=8,location=(-2.05,-.45,.15))
    prop=bpy.context.object; prop.name="Brújula espacial del episodio"; prop.data.materials.append(gold)
elif "nuba" in guest_key:
    guest_ball("Orbe de colores",(0,.1,-.9),(.25,.25,.25),blue)
elif "tito" in guest_key:
    guest_ball("Cristal del eco",(-.55,.1,-.55),(.30,.30,.40),blue)
elif "mara" in guest_key:
    guest_ball("Estrella sincronizada",(-.55,.1,-.55),(.28,.12,.28),gold)
elif "bongo" in guest_key:
    guest_ball("Sol gemelo",(-.55,.1,-.55),(.28,.12,.28),gold)
elif "lila" in guest_key:
    guest_ball("Semilla viajera",(-.55,.1,-.55),(.18,.18,.18),gold)
for frame,loc in [(1,(2.7,-.55,-.85)),(120,(2.05,-.55,-.65)),(360,(1.9,-.55,-.52)),(540,(2.15,-.55,-.62)),(720,(2.05,-.55,-.65))]:
    guest_root.location=loc
    guest_root.keyframe_insert(data_path="location",frame=frame)
# The guest reacts to the adventure instead of remaining a static prop.
for frame,angle,scale in [(1,-.12,.88),(90,.10,1.0),(180,-.08,1.04),(270,.14,.98),(360,-.10,1.03),(450,.12,.98),(540,-.08,1.04),(630,.10,1.0),(720,-.12,.92)]:
    guest_root.rotation_euler[1]=angle
    guest_root.keyframe_insert(data_path="rotation_euler",frame=frame)
    guest_root.scale=(scale,scale,scale)
    guest_root.keyframe_insert(data_path="scale",frame=frame)
if guest_root.animation_data and guest_root.animation_data.action:
    for fc in guest_root.animation_data.action.fcurves:
        for key in fc.keyframe_points:
            key.interpolation="BEZIER"

# Stretch all keyed actions from the original 12 fps timeline to 15 fps,
# preserving the same 60-second motion beats at the higher render rate.
for action in bpy.data.actions:
    for fcurve in action.fcurves:
        for key in fcurve.keyframe_points:
            key.co.x *= 1.25
            key.handle_left.x *= 1.25
            key.handle_right.x *= 1.25
        fcurve.update()


# STORY-DIRECTED ANIMATION PASS — actions and staging are driven by each narration beat.
# The episode is split into 12 five-second shots; each line selects a physical action.
narration = episode.get("narration", [])
if not narration:
    narration = [line.replace("COCO: ", "") for line in episode_script.splitlines() if line.startswith("COCO:")]
narration = (narration + ["Coco mira a su alrededor"] * 12)[:12]

# Build a readable alien meadow/field in the foreground, while preserving the space setting.
field_mat = mat("Pradera alienígena", (.055,.24,.16), rough=.92)
field = bpy.data.objects.new("Campo alienígena — suelo", bpy.data.meshes.new("Campo alienígena — malla"))
scene.collection.objects.link(field)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-2.92))
field = bpy.context.object
field.name = "Campo alienígena — suelo"
field.data.materials.append(field_mat)
# Distant rolling mounds and tufts give the camera parallax and establish a real place.
mound_mat = mat("Lomas verde esmeralda",(.08,.34,.23),rough=1)
grass_mat = mat("Hierba luminosa",(.18,.62,.25),rough=.85,emission=.12)
rock_mat = mat("Rocas del campo",(.22,.31,.39),metal=.12,rough=.82)
for i in range(18):
    x = -8.5 + i * 1.0
    z = -2.72 + ((i * 7) % 5) * .035
    mound = uv("Loma del campo",(x,3.5,z),(1.35,.45,.34),mound_mat,20)
for i in range(42):
    x = ((i * 37) % 170 - 85) / 10
    y = -1.0 + ((i * 19) % 65) / 10
    h = .18 + ((i * 11) % 7) * .035
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=.10, radius2=.015, depth=h, location=(x,y,-2.84+h/2))
    blade = bpy.context.object
    blade.name = "Hierba del campo"
    blade.data.materials.append(grass_mat)
    blade.rotation_euler[1] = ((i % 5)-2) * .12
for i in range(10):
    x = -7.5 + i * 1.65
    rock = uv("Piedra del sendero",(x,-.2,-2.78),(.28+(i%3)*.08,.22,.16+(i%2)*.08),rock_mat,16)

# Re-parent arms and hands to shoulder pivots so gestures rotate from the shoulder, not the center.
arm_objects = [o for o in bpy.data.objects if o.name == "Brazo"]
hand_objects = [o for o in bpy.data.objects if o.name == "Mano"]
shoulders = []
for idx, arm in enumerate(arm_objects):
    side = -1 if idx == 0 else 1
    pivot = bpy.data.objects.new("Control hombro " + str(idx), None)
    scene.collection.objects.link(pivot)
    pivot.parent = root
    pivot.location = (side*.72, -.03, -.85)
    arm_world = arm.matrix_world.copy()
    arm.parent = pivot
    arm.matrix_world = arm_world
    if idx < len(hand_objects):
        hand = hand_objects[idx]
        hand_world = hand.matrix_world.copy()
        hand.parent = pivot
        hand.matrix_world = hand_world
    shoulders.append(pivot)

hips = [bpy.data.objects.get("Cadera izquierda"), bpy.data.objects.get("Cadera derecha")]
def key_root(frame, x, z, tilt=0.0):
    root.location = (x, 0, z)
    root.rotation_euler[1] = tilt
    root.keyframe_insert(data_path="location", frame=frame)
    root.keyframe_insert(data_path="rotation_euler", frame=frame)

# Every 5-second narration beat becomes a distinct acting beat, with anticipation and follow-through.
for beat, raw_line in enumerate(narration):
    line = str(raw_line).lower()
    start = 1 + beat * 75
    mid = start + 37
    end = min(start + 74, 900)
    running = any(w in line for w in ["corre","corriendo","correr","bloquea","meteorito","cometa","despeja","siguen","guían","guian","regreso","ruta"])
    jumping = any(w in line for w in ["salta","saltar","brinca","puente","cruza","cruzar"])
    celebrating = any(w in line for w in ["celebran","misión cumplida","brilla","agradecimiento","hogar"])
    pointing = any(w in line for w in ["pista","señal","senal","encuentra","observa","mira","descubre"])
    activating = any(w in line for w in ["activa","ajusta","mochila","prepara"])
    greeting = any(w in line for w in ["conoce","acompaña","amigo","juntos"])
    searching = any(w in line for w in ["perdió","perdio","camino","escuchar","sonidos","buscan"])
    if running:
        # Run cycle: opposing legs and arms, torso bounce, forward lean, and actual travel.
        for f, phase in [(start,0),(start+9,1),(start+18,0),(start+27,-1),(mid,0),(mid+9,1),(mid+18,0),(mid+27,-1),(end,0)]:
            if hips[0]:
                hips[0].rotation_euler[1] = .72 * phase
                hips[0].keyframe_insert(data_path="rotation_euler",frame=f)
            if hips[1]:
                hips[1].rotation_euler[1] = -.72 * phase
                hips[1].keyframe_insert(data_path="rotation_euler",frame=f)
            for j, shoulder in enumerate(shoulders):
                shoulder.rotation_euler[1] = (.68 * phase) * (1 if j == 0 else -1)
                shoulder.keyframe_insert(data_path="rotation_euler",frame=f)
            bob = .10 if phase == 0 else .22
            key_root(f, -.65 + (f-start)/74*1.3, bob, -.13)
    elif jumping:
        key_root(start,-.25,0,0)
        key_root(start+12,-.25,.72,-.08)
        key_root(mid,.15,.95,.06)
        key_root(end,.35,0,0)
        for j, shoulder in enumerate(shoulders):
            for f,a in [(start,0),(start+12,-1.0),(mid,-.8),(end,.15)]:
                shoulder.rotation_euler[1] = a if j == 0 else -a
                shoulder.keyframe_insert(data_path="rotation_euler",frame=f)
    elif celebrating:
        key_root(start,0,0,0)
        for f,a in [(start,0),(start+12,-.85),(mid,-.95),(end,-.10)]:
            for j, shoulder in enumerate(shoulders):
                shoulder.rotation_euler[1] = a if j == 0 else -a
                shoulder.keyframe_insert(data_path="rotation_euler",frame=f)
            root.location.z = .10 if f == mid else 0
            root.keyframe_insert(data_path="location",frame=f)
    elif pointing or activating:
        key_root(start,0,0,0)
        for j, shoulder in enumerate(shoulders):
            vals = [(start,0),(start+12, -.95 if j == 1 else .15),(mid,-.85 if j == 1 else .10),(end,0)]
            for f,a in vals:
                shoulder.rotation_euler[1] = a
                shoulder.keyframe_insert(data_path="rotation_euler",frame=f)
        # Look toward the clue with a slight head/body turn.
        for f,a in [(start,0),(start+15,.16),(mid,.20),(end,0)]:
            root.rotation_euler[2] = a
            root.keyframe_insert(data_path="rotation_euler",frame=f)
    elif greeting or searching:
        key_root(start,0,0,0)
        for j, shoulder in enumerate(shoulders):
            for f,a in [(start,0),(start+15,.62 if j == 1 else -.25),(mid,.48 if j == 1 else -.15),(end,0)]:
                shoulder.rotation_euler[1] = a
                shoulder.keyframe_insert(data_path="rotation_euler",frame=f)
        for f,a in [(start,0),(start+15,-.12),(mid,.12),(end,0)]:
            root.rotation_euler[2] = a
            root.keyframe_insert(data_path="rotation_euler",frame=f)
    else:
        # Listening / reacting: settle, glance, blink, and breathe rather than loop a walk.
        key_root(start,0,0,0)
        for f,z in [(start,0),(start+18,.08),(mid,.02),(end,0)]:
            root.location.z = z
            root.keyframe_insert(data_path="location",frame=f)
        for f,a in [(start,0),(start+18,.12),(mid,-.10),(end,0)]:
            root.rotation_euler[2] = a
            root.keyframe_insert(data_path="rotation_euler",frame=f)

# Camera follows the action and changes scale slightly between story beats.
for beat, raw_line in enumerate(narration):
    line = str(raw_line).lower()
    start = 1 + beat * 75
    mid = start + 37
    end = min(start + 74, 900)
    is_run = any(w in line for w in ["corre","corriendo","correr","bloquea","meteorito","cometa","despeja","ruta"])
    is_jump = any(w in line for w in ["salta","brinca","puente","cruza"])
    cam.data.ortho_scale = 7.6 if is_run or is_jump else (8.2 if beat % 2 == 0 else 8.6)
    cam.data.keyframe_insert(data_path="ortho_scale",frame=start)
    cam.data.keyframe_insert(data_path="ortho_scale",frame=mid)
    cam.data.keyframe_insert(data_path="ortho_scale",frame=end)
    cam.location.x = 3.5 if is_run else (4.2 if beat % 2 else 3.8)
    cam.location.z = 1.15 if is_jump else (1.0 if is_run else .85)
    cam.keyframe_insert(data_path="location",frame=start)
    cam.keyframe_insert(data_path="location",frame=mid)
    cam.keyframe_insert(data_path="location",frame=end)

# Foreground rocks slide past during running shots to make speed and travel legible.
for idx, obj in enumerate([o for o in bpy.data.objects if o.name.startswith("Piedra del sendero")]):
    for beat, raw_line in enumerate(narration):
        line = str(raw_line).lower()
        if any(w in line for w in ["corre","corriendo","correr","ruta","despeja"]):
            a = 1 + beat*75
            b = min(a+74,900)
            base_x = obj.location.x
            obj.location.x = base_x + 1.8
            obj.keyframe_insert(data_path="location",frame=a)
            obj.location.x = base_x - 2.2
            obj.keyframe_insert(data_path="location",frame=b)

# Make action beats feel intentional: smooth arcs, but retain crisp contact and take-off timing.
for obj in bpy.data.objects:
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for key in fc.keyframe_points:
                key.interpolation = "BEZIER"

scene.render.filepath=OUT+"/coco-base.mp4"
scene.frame_set(1)
bpy.ops.render.render(animation=True)
print("RENDER_COMPLETE",OUT)
