"""Illustrate shared leases and bounded backpressure, without physical hardware."""
from AppOS.Services.frame_pool import FramePool, PoolBusy

def main():
    pool = FramePool(capacity=2)
    pool.publish(b"depth frame A", timestamp=1)
    game = pool.acquire("game")
    tracking = pool.acquire("tracking")
    print("same immutable frame?", game.data.obj is tracking.data.obj)
    pool.publish(b"depth frame B", timestamp=2)
    research = pool.acquire("research")
    try:
        pool.publish(b"depth frame C", timestamp=3)
    except PoolBusy as e:
        print("expected backpressure:", e)
    pool.detach("game")
    pool.detach("tracking")
    pool.publish(b"depth frame C", timestamp=3)
    print("research still sees:", bytes(research.data))
    research.close()
    print(pool.status())

if __name__ == "__main__":
    main()
