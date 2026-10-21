"""Simulated camera sharing: no camera, threads, network, or system changes."""
from AppOS.Services.switchboard import Switchboard, SwitchboardError

if __name__ == "__main__":
    service = Switchboard()
    camera = service.register("camera.synthetic")
    camera.subscribe("preview", every_n_frames=1)
    camera.subscribe("tracker", every_n_frames=3)
    for t in range(1, 7):
        camera.publish({"synthetic_depth": t}, timestamp=float(t))
        print("frame", t, "preview", camera.take_latest("preview"),
              "tracker", camera.take_latest("tracker"))
    print("shared:", camera.status())
    try:
        camera.acquire_exclusive("calibration")
    except SwitchboardError as exc:
        print("expected conflict:", exc.code.value, str(exc))
    camera.unsubscribe("preview")
    camera.unsubscribe("tracker")
    camera.acquire_exclusive("calibration")
    print("exclusive:", camera.status())
    camera.release_exclusive("calibration")
    print("released:", camera.status())
