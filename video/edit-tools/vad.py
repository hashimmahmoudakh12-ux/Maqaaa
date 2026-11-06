import numpy as np,subprocess,json,sys
TH=float(sys.argv[1]) if len(sys.argv)>1 else -42
a=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i','a.wav','-af','highpass=f=80','-f','s16le','-'],capture_output=True).stdout,np.int16).astype(np.float32)/32768
h=160;n=len(a)//h;r=20*np.log10(np.sqrt((a[:n*h].reshape(n,h)**2).mean(1))+1e-9)
r=np.convolve(r,np.ones(5)/5,'same')
sp=r>TH; dt=h/16000
iv=[];s=None
for i,v in enumerate(sp):
    if v and s is None:s=i
    if not v and s is not None: iv.append([s*dt,i*dt]);s=None
if s is not None: iv.append([s*dt,n*dt])
m=[]
for x in iv:
    if m and x[0]-m[-1][1]<0.2: m[-1][1]=x[1]
    else: m.append(x)
m=[x for x in m if x[1]-x[0]>0.12]
print('  '.join(f"{a:.2f}-{b:.2f}" for a,b in m))
json.dump(m,open('speech.json','w'))
