"""Validate the delivered media and narration cue boundaries."""
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from script import SCRIPT
from assemble import probe,FF,OUT
def main():
 p=OUT/'chapter15_multiple_integrals.mp4';info=probe(p)
 video=next(s for s in info['streams'] if s['codec_type']=='video')
 audio=next(s for s in info['streams'] if s['codec_type']=='audio')
 assert video['width']==1920 and video['height']==1080
 assert video['r_frame_rate']=='30/1'
 assert any(s['codec_type']=='subtitle' for s in info['streams'])
 assert p.stat().st_size<95_000_000
 for scene in SCRIPT:
  cues=json.loads((ROOT/'media/cues'/f'{scene}.json').read_text())
  source=ROOT/'media/videos/film/1080p30'/f'{scene}.mp4'
  duration=float(probe(source)['format']['duration'])
  assert len(cues)==len(SCRIPT[scene]),scene
  for previous,current in zip(cues,cues[1:]):
   assert current['start']>=previous['start']+previous['duration']-.08,scene
  assert cues[-1]['start']+cues[-1]['duration']<=duration+.1,scene
 result=subprocess.run([str(FF),'-v','error','-i',str(p),'-map','0:v','-map','0:a','-f','null','-'],capture_output=True,text=True)
 assert result.returncode==0,result.stderr
 assert not result.stderr,result.stderr
 chapters=json.loads(subprocess.check_output([str(ROOT.parent/'.manim-env/bin/ffprobe'),'-v','error','-show_chapters','-of','json',str(p)]))['chapters']
 assert len(chapters)==len(SCRIPT)
 result={'full_audio_video_decode':'PASS','cue_timing_all_49_passages':'PASS','resolution':'1920x1080','fps':30,'duration_seconds':float(info['format']['duration']),'section_markers':len(chapters),'narration':'synthetic en-US-AndrewNeural','captions':'optional embedded English mov_text; SRT and WebVTT supplied','size_bytes':p.stat().st_size,'renderer':'Manim Community 0.22.1 / Cairo','worked_result_checks':'See math_checks.txt (nine numerical checks; original results retained in the rebuilt film).'}
 (OUT/'validation.json').write_text(json.dumps(result,indent=2))
 (OUT/'media_info.txt').write_text(json.dumps(info,indent=2))
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
