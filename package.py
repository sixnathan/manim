"""Build a local video player, transcript, and source manifest."""
from pathlib import Path
import html, json
from lesson import SCENES

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'

def build():
    chapters=json.loads((OUT/'chapters.json').read_text())
    transcript=[]; buttons=[]
    for scene,ch in zip(SCENES,chapters):
        start=ch['start']; ts=f'{int(start//60):02d}:{int(start%60):02d}'
        transcript.append(f'{ts}  {scene[0]}\n\n{scene[3]}\n\nFormula (LaTeX): {scene[2]}\n')
        buttons.append(f'<button data-time="{start}"><span>{ts}</span>{html.escape(scene[0])}</button>')
    (OUT/'transcript.txt').write_text('\n\n'.join(transcript))
    srt=(OUT/'captions.srt').read_text()
    import re
    vtt='WEBVTT\n\n'+re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})',r'\1.\2',srt)
    (OUT/'captions.vtt').write_text(vtt)
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Geometry of Adding · Stewart Chapter 15</title>
<style>
*{box-sizing:border-box}body{background:#101722;color:#e9eff6;font:17px/1.6 system-ui;margin:0}main{max-width:1400px;margin:auto;padding:36px}h1{font-size:clamp(28px,4vw,48px);line-height:1.2;margin:10px 0}p{color:#afbdca;max-width:80ch}small,.eyebrow{color:#58dec7}.layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:24px;margin:28px 0}video{width:100%;border-radius:14px;background:#080d15}nav{max-height:600px;overflow:auto}button{display:block;width:100%;text-align:left;border:0;border-bottom:1px solid #2a3c50;background:#172332;color:#e9eff6;padding:13px;cursor:pointer;font:14px/1.5 system-ui}button:hover,button.active{background:#264253}button span{display:inline-block;min-width:50px;color:#58dec7}a{color:#62c4ff}section{border-top:1px solid #2a3c50;padding:20px 0}h2{font-size:24px}li{margin:8px 0}details{background:#172332;padding:16px;border-radius:10px;margin:10px 0}summary{cursor:pointer;color:#ffdc80}code{color:#ffdc80}footer{color:#98a9ba;font-size:14px;margin:28px 0}@media(max-width:900px){.layout{grid-template-columns:1fr}main{padding:20px}nav{max-height:280px}}
</style><main><div class="eyebrow">A VISUAL GUIDE TO MULTIPLE INTEGRALS</div>
<h1>The Geometry of Adding</h1><p>Stewart, chapter 15 · original animated explanation · 720p, 24 fps · narrated in English</p>
<div class="layout"><div><video id="video" controls preload="metadata" poster="poster.png"><source src="chapter15_multiple_integrals.mp4" type="video/mp4"><track kind="captions" src="captions.vtt" srclang="en" label="English"></video>
<p><a href="chapter15_multiple_integrals.mp4" download>Download video</a> · <a href="transcript.txt">Transcript</a> · <a href="captions.srt">Captions</a> · <a href="storyboard.jpg">Storyboard</a></p></div><nav aria-label="Video chapters">BUTTONS</nav></div>
<section><h2>The picture to keep</h2><p>A multiple integral adds local contributions across a region. Before calculating, draw a representative piece, find its physical area or volume, and sweep it through the region to read the bounds.</p>
<ul><li>Rectangular tiles: dA = dx dy.</li><li>Polar tiles: dA = r dr dθ. The angular edge has length r dθ.</li><li>Cylindrical blocks: dV = r dr dθ dz.</li><li>Spherical blocks: dV = ρ² sinφ dρ dφ dθ. Here φ is measured down from +z.</li><li>General transformations: multiply by the absolute Jacobian determinant.</li><li>Surface graphs: dS = √(1 + fₓ² + fᵧ²) dA.</li></ul></section>
<section><h2>Pause and try</h2>
<details><summary>1. Reverse the bounds: 0 ≤ x ≤ 1, x² ≤ y ≤ x.</summary><p>0 ≤ y ≤ 1, y ≤ x ≤ √y. Draw a horizontal strip; the line is the left edge and the parabola is the right edge.</p></details>
<details><summary>2. Find the volume below z = 1 − x² − y² above the unit disk.</summary><p>Use polar coordinates. Integrate (1 − r²)r for 0 ≤ r ≤ 1 and 0 ≤ θ ≤ 2π. Answer: π/2.</p></details>
<details><summary>3. Find the surface area of z = x + y above the unit square.</summary><p>Both partial derivatives are 1, so the area multiplier is √3. Multiply by the base area of 1: √3.</p></details>
<details><summary>4. A unit square has density 1 + x. Where does it balance?</summary><p>Mass is 3/2. The x moment numerator is 5/6, so x̄ = 5/9. Symmetry in y gives ȳ = 1/2.</p></details>
<details><summary>5. Why is there sinφ in spherical volume?</summary><p>At polar angle φ the latitude circle has radius ρ sinφ, so its short angular edge has length ρ sinφ dθ. Multiply by ρ dφ and dρ.</p></details></section>
<section><h2>Scope and references</h2><p>The section numbering follows <em>Stewart, Calculus: Early Transcendentals, eighth edition</em>. Your edition has not been confirmed. This is a conceptual guide to all nine sections, with selected original examples; use your textbook for its full exercises and theorem details.</p>
<ul><li><a href="https://advise.chem.umn.edu/sites/advise.chem.umn.edu/files/files/math_1271-1272-2263_text_toc_stewart_calculus_early_transcendentals_8th_ed.pdf">University of Minnesota: Stewart eighth-edition contents</a> — section alignment.</li>
<li><a href="../assets/references/mit_strang_multiple_integrals.pdf">MIT: Gilbert Strang, Calculus, chapter 14, Multiple Integrals</a> — downloaded reference PDF.</li>
<li><a href="../assets/references/mit_change_of_variables.pdf">MIT 18.02: Changing Variables in Multiple Integrals</a> — downloaded reference PDF.</li></ul></section>
<footer>Original script, examples, diagrams, and animation source. Inspired by geometric mathematical exposition; unaffiliated with 3Blue1Brown, Stewart, or the publishers. Synthetic narration: Microsoft Edge TTS, en-GB-RyanNeural. Captions are paced to each scene's narration and may have small timing offsets. Downloaded references retain their original rights and attribution.</footer>
</main><script>const v=document.querySelector('video'),bs=[...document.querySelectorAll('button[data-time]')];bs.forEach(b=>b.onclick=()=>{v.currentTime=Number(b.dataset.time);v.play()});v.ontimeupdate=()=>{let active=bs.filter(b=>Number(b.dataset.time)<=v.currentTime).at(-1);bs.forEach(b=>b.classList.toggle('active',b===active))};</script></html>'''
    (OUT/'index.html').write_text(page.replace('BUTTONS','\n'.join(buttons)))
    print('Player, transcript, and WebVTT captions written.')

if __name__=='__main__': build()
