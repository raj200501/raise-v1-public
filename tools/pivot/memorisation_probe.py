import numpy as np, torch, torch.nn as nn, time, math, json
torch.set_num_threads(4); torch.manual_seed(0)
z = np.load("data/pivot/raw_c1024.npz")
X, y = z["X"][:5000], z["y"][:5000].astype(np.int64)
rng = np.random.default_rng(0); ysh = y.copy(); rng.shuffle(ysh)
Xt = torch.from_numpy(X.astype(np.int64)); yt = torch.from_numpy(ysh)

def make(kind):
    class M(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(256, 16)
            self.conv = nn.Sequential(
                nn.Conv1d(16,64,9,padding=4), nn.ReLU(), nn.MaxPool1d(4),
                nn.Conv1d(64,96,9,padding=4), nn.ReLU(), nn.MaxPool1d(4),
                nn.Conv1d(96,128,9,padding=4), nn.ReLU())
            self.gap = nn.AdaptiveAvgPool1d(1); self.kind = kind
            self.fc = nn.Linear(128 if kind=="gap" else 128*64, 26)
        def forward(self,x):
            h = self.conv(self.emb(x).transpose(1,2))
            h = self.gap(h).squeeze(-1) if self.kind=="gap" else h.flatten(1)
            return self.fc(h)
    return M()

out={"n":len(y),"chance":round(1/26,4),"ln26":round(math.log(26),4),"arms":{}}
print(f"memorisation probe on {len(y)} fragments, SHUFFLED labels (chance {1/26:.4f})", flush=True)
for kind in ("gap","flatten"):
    m = make(kind); opt = torch.optim.Adam(m.parameters(), 1e-3); lf = nn.CrossEntropyLoss()
    n = len(yt); t=time.perf_counter(); trace=[]
    for ep in range(30):
        m.train(); perm = torch.randperm(n); tot=0.0; corr=0
        for i in range(0, n, 256):
            b = perm[i:i+256]
            o = m(Xt[b]); loss = lf(o, yt[b])
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss.detach())*len(b); corr += int((o.argmax(1)==yt[b]).sum())
        trace.append([round(tot/n,4), round(corr/n,4)])
        if ep in (0,9,19,29):
            print(f"  {kind:<8} epoch {ep+1:>2}  train loss {tot/n:.4f}  train acc {corr/n:.4f}", flush=True)
    out["arms"][kind]={"params":sum(p.numel() for p in m.parameters()),
                       "final_train_loss":trace[-1][0],"final_train_acc":trace[-1][1],
                       "seconds":round(time.perf_counter()-t,1),"trace":trace}
json.dump(out, open("/tmp/claude-0/-home-user-raise-v1/5d675fa9-5fc4-501c-b3b3-a76510397d00/scratchpad/memprobe.json","w"), indent=1)
print("done", flush=True)
