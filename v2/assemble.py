"""Assemble the finished Manim scenes with chapter markers and optional captions."""
from pathlib import Path
import subprocess, json, re, html, sys, shutil
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from script import SCRIPT
OUT=ROOT.parent/'output'
FF=ROOT.parent/'.manim-env/bin/ffmpeg'
PROBE=ROOT.parent/'.manim-env/bin/ffprobe'
TITLES={
'Volume':'15.1 · Building a double integral',
'Slices':'15.1 · Fubini: slices of a solid',
'Bounds':'15.2 · Reading bounds from a picture',
'Polar':'15.3 · Why polar area contains r',
'Density':'15.4 · Mass, balance, and density',
'SurfaceArea':'15.5 · The surface and its shadow',
'Solids':'15.6–15.7 · Triple and cylindrical integrals',
'Spherical':'15.8 · Three lengths on a spherical shell',
'Jacobian':'15.9 · The Jacobian: local area scaling',
}
def probe(p):
 return json.loads(subprocess.check_output([str(PROBE),'-v','error','-show_format','-show_streams','-of','json',str(p)]))
def stamp(t,vtt=False):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
 return f'{h:02}:{m:02}:{s:02}'+('.' if vtt else ',')+f'{ms:03}'
def main():
 OUT.mkdir(exist_ok=True)
 folder=ROOT/'media/videos/film/1080p30'
 scenes=[folder/f'{name}.mp4' for name in SCRIPT]
 assert all(p.exists() for p in scenes),[str(p) for p in scenes if not p.exists()]
 offsets=[];offset=0;captions=[];transcript=[];chapters=[]
 for name,p in zip(SCRIPT,scenes):
  info=probe(p);duration=float(info['format']['duration'])
  chapters.append({'title':TITLES[name],'start':round(offset,3),'duration':duration})
  cues=json.loads((ROOT/'media/cues'/f'{name}.json').read_text())
  for cue,(key,words) in zip(cues,SCRIPT[name]):
   assert cue['key']==key
   t=offset+cue['start'];length=cue['duration']-.35
   transcript.append(f'{stamp(t).split(",")[0]}  {TITLES[name]} / {key}\n{words}\n')
   sentences=re.split(r'(?<=[.!?])\s+',words);weight=sum(map(len,sentences));elapsed=0
   for s in sentences:
    dt=length*len(s)/weight;captions.append((t+elapsed,t+elapsed+dt,s));elapsed+=dt
  offset+=duration
 manifest=ROOT/'media/concat.txt';manifest.write_text('\n'.join(f"file '{p.resolve()}'" for p in scenes))
 metadata=ROOT/'media/chapters.ffmeta';metadata.write_text(';FFMETADATA1\ntitle=The Geometry of Multiple Integrals — Stewart Chapter 15\nartist=Original Manim educational film\n'+''.join(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c['start']*1000)}\nEND={round((c['start']+c['duration'])*1000)}\ntitle={c['title']}\n" for c in chapters))
 (OUT/'chapters.json').write_text(json.dumps(chapters,indent=2))
 (OUT/'transcript.txt').write_text('\n'.join(transcript))
 import textwrap
 (OUT/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n'+ '\n'.join(textwrap.wrap(s,90)) for i,(a,b,s) in enumerate(captions)))
 (OUT/'captions.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f'{stamp(a,True)} --> {stamp(b,True)}\n{s}' for a,b,s in captions))
 target=OUT/'chapter15_multiple_integrals.mp4'
 command=[str(FF),'-y','-v','warning','-f','concat','-safe','0','-i',str(manifest),'-i',str(metadata),'-i',str(OUT/'captions.srt'),'-map','0:v','-map','0:a','-map','2:0','-map_metadata','1','-map_chapters','1','-c:v','copy','-c:a','aac','-b:a','128k','-af','aresample=async=1:first_pts=0','-c:s','mov_text','-metadata:s:s:0','language=eng','-disposition:s:0','0','-movie_timescale','1000','-movflags','+faststart',str(target)]
 subprocess.run(command,check=True)
 if target.stat().st_size>95_000_000:raise RuntimeError('Final video exceeds Git size budget; lower target bitrate before publishing.')
 subprocess.run([str(FF),'-y','-v','error','-ss','45','-i',str(target),'-frames:v','1',str(OUT/'poster.png')],check=True)
 # A short complete opening scene is useful for reviewing the visual rebuild.
 shutil.copyfile(scenes[0],OUT/'chapter15_preview.mp4')
 buttons='\n'.join(f'<button data-time="{c["start"]}"><time>{int(c["start"]//60):02}:{int(c["start"]%60):02}</time>{html.escape(c["title"])}</button>' for c in chapters)
 page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stewart 15 · The Geometry of Multiple Integrals</title>
<style>*{box-sizing:border-box}body{margin:0;background:#0c0f14;color:#e9edf4;font:17px/1.6 system-ui}main{max-width:1440px;margin:auto;padding:40px}h1{font-size:clamp(28px,4vw,48px);line-height:1.15}p{color:#9ba9b9;max-width:80ch}.label{color:#67d9bd;letter-spacing:.15em;font-size:13px}.layout{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:28px;margin:28px 0}video{width:100%;background:#000}button{display:block;text-align:left;width:100%;background:none;color:#e9edf4;font:14px/1.5 system-ui;padding:15px 8px;border:0;border-bottom:1px solid #25303e;cursor:pointer}button:hover,button.active{color:#ffdb7d}time{display:block;color:#617184;font-size:12px}a{color:#75c8ff}section{padding:24px 0;border-top:1px solid #25303e}small{color:#617184}@media(max-width:900px){.layout{grid-template-columns:1fr}main{padding:20px}}</style>
<main><div class="label">STEWART · CHAPTER FIFTEEN · A MANIM FILM</div><h1>The geometry of multiple integrals</h1><p>Build a volume. Sweep a region. Bend a grid. Watch the geometry produce the mathematics.</p>
<div class="layout"><div><video id="film" controls poster="poster.png" preload="metadata"><source src="chapter15_multiple_integrals.mp4" type="video/mp4"><track kind="captions" src="captions.vtt" srclang="en" label="English"></video><p><a href="chapter15_multiple_integrals.mp4" download>Download full film</a> · <a href="chapter15_preview.mp4">Watch the opening</a> · <a href="transcript.txt">Transcript</a></p></div><nav aria-label="Sections within Stewart chapter 15">BUTTONS</nav></div>
<section><h2>From a piece to a total</h2><p>The film covers double and triple integrals, Fubini, integration bounds, polar area, applications of density, surface area, cylindrical and spherical coordinates, and the Jacobian. Section numbering follows Stewart’s <em>Calculus: Early Transcendentals</em>, eighth edition.</p><p>Original diagrams, animation, examples, and narration text. Rendered with Manim Community at 1080p and 30 frames per second. Synthetic narration. Captions are optional and timed within each spoken passage.</p></section>
<section><h2>Reference material</h2><p><a href="../assets/references/mit_strang_multiple_integrals.pdf">Gilbert Strang · Multiple Integrals</a><br><a href="../assets/references/mit_change_of_variables.pdf">MIT 18.02 · Changing Variables</a></p><small>Reference PDFs retain their original attribution and rights. This independent educational film is unaffiliated with Stewart, Cengage, MIT, or 3Blue1Brown.</small></section>
</main><script>let v=document.getElementById('film'),bs=[...document.querySelectorAll('button')];bs.forEach(b=>b.onclick=()=>{v.currentTime=+b.dataset.time;v.play()});v.ontimeupdate=()=>{let a=bs.filter(b=>+b.dataset.time<=v.currentTime).at(-1);bs.forEach(b=>b.classList.toggle('active',b===a))};</script></html>'''
 (OUT/'index.html').write_text(page.replace('BUTTONS',buttons))
 from PIL import Image,ImageDraw
 selected={'Volume':'product','Slices':'outer','Bounds':'reverse','Polar':'factor','Density':'result','SurfaceArea':'factor','Solids':'bounds','Spherical':'multiply','Jacobian':'det'}
 board=Image.new('RGB',(1920,1140),'#0c0f14');draw=ImageDraw.Draw(board)
 for i,(name,p) in enumerate(zip(SCRIPT,scenes)):
  cues=json.loads((ROOT/'media/cues'/f'{name}.json').read_text());cue=next(c for c in cues if c['key']==selected[name]);time=cue['start']+cue['duration']*.7
  still=ROOT/'media'/f'{name}_storyboard.png'
  subprocess.run([str(FF),'-y','-v','error','-ss',str(time),'-i',str(p),'-frames:v','1',str(still)],check=True)
  im=Image.open(still).convert('RGB').resize((640,360),Image.Resampling.LANCZOS)
  x=(i%3)*640;y=(i//3)*380;board.paste(im,(x,y));draw.text((x+20,y+361),TITLES[name],fill='#9ba9b9')
 board.save(OUT/'storyboard.jpg',quality=93)
 print(f'Finished {offset/60:.2f} min, {target.stat().st_size/1e6:.1f} MB',flush=True)
if __name__=='__main__':main()
