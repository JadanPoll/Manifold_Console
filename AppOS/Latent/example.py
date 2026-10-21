"""Visible demonstration of cooperative update rates (no GUI or hardware)."""
import time
from AppOS.Latent.subscriptions import Range,Scheduler

if __name__=="__main__":
    scheduler=Scheduler()
    counts={"decor":0,"simulation":0}
    scheduler.subscribe("decor",lambda:counts.__setitem__("decor",counts["decor"]+1),Range(10,30,60),Range(1,2,10),Range(1,1,5))
    scheduler.subscribe("simulation",lambda:counts.__setitem__("simulation",counts["simulation"]+1),Range(30,30,30),Range(30,30,30),Range(30,30,30))
    for profile in ("foreground","background","constrained"):
        scheduler.set_profile(profile)
        before=counts.copy()
        until=time.monotonic()+1.0
        while time.monotonic()<until:
            scheduler.tick()
            time.sleep(.005)
        print(profile, {k:counts[k]-before[k] for k in counts}, scheduler.inspect())
