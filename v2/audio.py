import asyncio, json, os, subprocess
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from script import SCRIPT
ROOT=Path(__file__).resolve().parent
async def main():
    import edge_tts
    folder=ROOT/'audio';folder.mkdir(exist_ok=True)
    sem=asyncio.Semaphore(3)
    async def one(scene,key,words):
        path=folder/f'{scene}_{key}.mp3'
        if path.exists() and path.stat().st_size>1000: return
        async with sem:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(words,'en-US-AndrewNeural',rate='-4%').save(str(path))
                    print(scene,key,flush=True);return
                except Exception:
                    if attempt==2: raise
                    await asyncio.sleep(1)
    await asyncio.gather(*(one(scene,key,words) for scene,beats in SCRIPT.items() for key,words in beats))
    ff=ROOT.parent/'.manim-env/bin/ffprobe'; durations={}
    for scene,beats in SCRIPT.items():
        for key,_ in beats:
            p=folder/f'{scene}_{key}.mp3'
            durations[f'{scene}_{key}']=float(subprocess.check_output([str(ff),'-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)],text=True).strip())
    (folder/'durations.json').write_text(json.dumps(durations,indent=2))
if __name__=='__main__':asyncio.run(main())
