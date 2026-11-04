"""Synthesised (royalty-free, self-made) UI sound effects mixed onto one track at cue times."""
import sys, json, wave, numpy as np
ev=json.load(open(sys.argv[1])); out=sys.argv[2]; SR=48000
rng=np.random.default_rng(42)
def env(n,att,dec):  # attack/decay envelope in seconds
    t=np.arange(n)/SR; e=np.minimum(1,t/max(att,1e-4))*np.exp(-t/dec); return e
def tone(freqs,dur,dec,att=0.002,amps=None):
    n=int(dur*SR); t=np.arange(n)/SR; y=np.zeros(n)
    for i,f in enumerate(freqs):
        y+= (amps[i] if amps else 1)*np.sin(2*np.pi*f*t)
    return y*env(n,att,dec)/len(freqs)
def pop(f0=1100,f1=260,dur=0.12,gain=0.9):
    n=int(dur*SR); t=np.arange(n)/SR
    f=f1+(f0-f1)*np.exp(-t/0.018); ph=2*np.pi*np.cumsum(f)/SR
    y=np.sin(ph)*env(n,0.001,0.035)
    click=rng.standard_normal(n)*np.exp(-t/0.002)*0.25
    return gain*(y+click)
def whoosh(dur=0.42,gain=0.55):
    n=int(dur*SR); t=np.arange(n)/SR; w=rng.standard_normal(n)
    # sweeping one-pole low-pass: cutoff rises then falls
    fc=300+3200*np.sin(np.pi*t/dur)**2; a=np.exp(-2*np.pi*fc/SR); y=np.zeros(n); p=0.0
    for i in range(n): p=a[i]*p+(1-a[i])*w[i]; y[i]=p
    y-= np.convolve(y,np.ones(64)/64,mode="same")*0.6   # thin the lows
    e=np.sin(np.pi*np.clip(t/dur,0,1))**1.5
    return gain*2.2*y*e/np.max(np.abs(y)+1e-9)
def chime(gain=1.0):
    notes=[1046.5,1318.5,1568.0,2093.0,2637.0]; y=np.zeros(int(1.3*SR))
    for i,f in enumerate(notes):
        s=tone([f,f*2.01,f*3.02],1.0,0.32,amps=[1,0.35,0.12]); o=int(i*0.055*SR); y[o:o+len(s)]+=s
    sh=rng.standard_normal(len(y))*np.exp(-np.arange(len(y))/SR/0.25)*0.05   # shimmer
    hp=sh-np.convolve(sh,np.ones(8)/8,mode="same")
    return gain*(y+hp*3)
def coin(f=2093,gain=0.45):
    return gain*tone([f,f*1.26,f*2.71,f*4.1],0.35,0.09,amps=[1,0.8,0.4,0.2])
def coins(gain=0.75):
    y=np.zeros(int(1.2*SR))
    for i in range(7):
        s=coin(rng.choice([1975,2093,2349,2637]),gain*rng.uniform(0.5,1)); o=int((i*0.11+rng.uniform(0,0.05))*SR); y[o:o+len(s)]+=s
    return y
def ticks(n=12,span=1.15,gain=0.32):
    y=np.zeros(int((span+0.5)*SR))
    for i in range(n):
        tt=span*(1-(1-i/n)**1.8)          # ease-out, matches the counter
        s=tone([3200,4700],0.03,0.008)*gain; o=int(tt*SR); y[o:o+len(s)]+=s
    s=coin(2637,0.55); o=int(span*SR); y[o:o+len(s)]+=s   # final "ching"
    return y
def ding(gain=0.5): return gain*tone([1568,3136,4704],0.7,0.22,amps=[1,0.3,0.1])
def boing(gain=0.55,dur=0.45):
    n=int(dur*SR); t=np.arange(n)/SR
    f=180+260*(1-np.exp(-t/0.05))+40*np.sin(2*np.pi*14*t)*np.exp(-t/0.25)   # springy glide with wobble
    y=np.sin(2*np.pi*np.cumsum(f)/SR)+0.3*np.sin(4*np.pi*np.cumsum(f)/SR)
    return gain*y*env(n,0.004,0.16)
LIB={"boing":boing,"tick_pop":lambda:pop(1900,700,0.06,0.4),"pop":lambda:pop(),"pop_small":lambda:pop(1500,500,0.08,0.55),"pop_big":lambda:pop(900,180,0.16,1.0),
     "whoosh":lambda:whoosh(),"chime":chime,"coins":coins,"ticks":ticks,"ding":ding}
N=int(ev["dur"]*SR); mix=np.zeros(N)
for t,name in ev["events"]:
    s=LIB[name](); o=max(0,int(t*SR)); e=min(N,o+len(s)); mix[o:e]+=s[:e-o]
pk=np.max(np.abs(mix)); mix=mix/pk*10**(-6/20)        # peak -6 dBFS before the composition's data-volume
st=np.stack([mix,mix],1)
with wave.open(out,"wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
print("events",len(ev["events"]),"peak_before",round(float(pk),3))
