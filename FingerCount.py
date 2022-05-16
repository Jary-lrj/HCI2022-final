import cv2
import time
import os
import HandTrackingModule as HTM

###################################
wCam, hCam = 640, 480
##################################

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = HTM.handDetector(detectionCon=0.75)

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    cv2.imshow("Image", img)
    cv2.waitKey(1)
