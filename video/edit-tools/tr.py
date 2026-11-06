import json,sys,numpy as np,subprocess
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[3],device="cpu",compute_type="int8")
segs,info=m.transcribe(np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-f","s16le","-ac","1","-ar","16000","-"],capture_output=True).stdout,np.int16).astype(np.float32)/32768,word_timestamps=True,vad_filter=False,beam_size=5,initial_prompt="Assalamualaikum. Umrah, Allah, deen, Makkah, Madinah, the Ummah.",language="en")
print(info.language,info.language_probability)
out=[]
for s in segs:
    print(f"{s.start:.2f}-{s.end:.2f} {s.text}")
    for w in s.words: out.append(dict(w=w.word,s=w.start,e=w.end,p=w.probability))
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False,indent=0)
