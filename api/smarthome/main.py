from fastapi import FastAPI
from fastapi.responses import Response

from pyvesync import VeSync


app = FastAPI()

@app.get("/toggle")
def toggleSwitch():
    manager = VeSync("REPLACE ME", "REPLACE ME")
    if not manager.login():
        return Response(content={"message": "Unable to login"}, status_code="404", media_type="application/json")
    manager.update()
    my_switch = manager.outlets[0]
    if(my_switch.device_status == "on"):
        my_switch.turn_off()
    else:
        my_switch.turn_on()