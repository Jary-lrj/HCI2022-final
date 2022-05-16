import cv2
import time
import numpy as np
import HandTrackingModule as HTM
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
# volume.GetMute()
# volume.GetMasterVolumeLevel()
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]
###################################
wCam, hCam = 640, 480
##################################

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

detector = HTM.handDetector(detectionCon=0.7)

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lm_list = detector.findPosition(img, draw=False)
    if len(lm_list) != 0:
        x1, y1 = lm_list[4][1], lm_list[4][2]
        x2, y2 = lm_list[8][1], lm_list[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        print(length)

        if length < 10:
            cv2.circle(img, (cx, cy), 15, (0, 255, 255), cv2.FILLED)
        # Hand range 50 - 300
        vol = np.interp(length, [10, 300], [minVol, maxVol])

        volume.SetMasterVolumeLevel(vol, None)
        # volume range -45.0 - 0
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    cv2.putText(img, f'FPS:{int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)
    cv2.imshow("监控", img)
    cv2.waitKey(1)
