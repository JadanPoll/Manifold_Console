"""Two consumers share one published snapshot without copying it."""
from AppOS.Services.resource_views import Resource

if __name__=="__main__":
    device=Resource("synthetic.depth")
    game=device.attach("game")
    research=device.attach("research")
    payload=(12,14,18,19)  # Immutable demonstration payload
    device.publish(payload,timestamp=1.0)
    a=game.latest()
    b=research.latest()
    print("Same payload instance:",a.payload is b.payload)
    print("Independent cursors:",game.latest(),research.latest())
    print(device.describe())
    game.close();research.close()
    print(device.describe())
