
import asyncio
from contextlib import asynccontextmanager
import logging
import threading
import cv2
import io
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from pyvesync import VeSync
from ultralytics import YOLO

yolo = YOLO('yolo11n.pt')

STOP_EVENT = threading.Event()

def getCameraIndex():
    all_camera_idx_available = []

    for camera_idx in range(10):
        cap = cv2.VideoCapture(camera_idx)
        if cap.isOpened():
            all_camera_idx_available.append(camera_idx)
            cap.release()
    print("using index: ", all_camera_idx_available[0])
    return all_camera_idx_available


def captureImage(cap):

    success, frame = cap.read()

    if success:
        results = yolo(frame)
        annotated_frame = results[0].plot()
        success, buffer = cv2.imencode(".jpg", annotated_frame)

        if success:
            return buffer.tobytes()

class Webcam():
    def __init__(self):
        # If you want to check all possible camera indices, use getCameraIndex()
        # For now, leaving this hardcoded to zero
        index = 0
        self.videoCapture = cv2.VideoCapture(index)
        self.videoCapture.set(3, 1280)
        self.videoCapture.set(4, 720)


    def setRes(self, x, y):
        self.videoCapture.set(3, x)
        self.videoCapture.set(4, y)

    def setIndex(self, index):
        self.videoCapture = cv2.VideoCapture(index)

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.queue = asyncio.Queue(maxsize=1)

    async def write(self, data):
        await self.queue.put(data)
        print("writing")

    async def read(self):
        data = await self.queue.get()
        print("reading")
        return data

output = StreamingOutput()

async def producer(cap: Webcam, output: StreamingOutput):
    while True:
        frame = captureImage(cap.videoCapture)
        await output.write(frame)


async def consumer(output: StreamingOutput):
    while True:
        try:
            frame = await output.read()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        except Exception as e:
            logging.error(f"Error in generate_frames: {str(e)}")
            break

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup")
    camera = Webcam()
    asyncio.create_task(producer(camera, output))  # Background task starts at app startup
    yield
    print("Application shutdown")


app = FastAPI(lifespan=lifespan)

@app.get("/image")
def get_image():
    cam = Webcam()

    imageData = captureImage(cam)

    return Response(content=imageData, media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/mjpeg")
async def stream_data():
    return StreamingResponse(consumer(output), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/toggle")
def toggleSwitch():
    manager = VeSync("REPLACEME", "REPLACEME")
    if not manager.login():
        return Response(content={"message": "Unable to login"}, status_code="404", media_type="application/json")
    manager.update()
    my_switch = manager.outlets[0]
    if(my_switch.device_status == "on"):
        my_switch.turn_off()
    else:
        my_switch.turn_on()



