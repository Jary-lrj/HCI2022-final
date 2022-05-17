import threading

import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimediaWidgets import QVideoWidget
from GUI import Ui_Form
from myVideoWidget import myVideoWidget
import sys
import HandTrackingThread as GestureThread  # Modules of hand tracking


class VideoThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.detector = GestureThread.handDetector(detectionCon=0.75)

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            success, img = cap.read()
            img = self.detector.findHands(img)
            lm_list = self.detector.findPosition(img)
            if len(lm_list) != 0:
                print(lm_list[0])


class myMainWindow(Ui_Form, QMainWindow):
    def __init__(self):
        super(Ui_Form, self).__init__()
        self.setupUi(self)
        self.video_process_slider_pressed = False
        self.video_full_screen = False
        self.video_full_screen_widget = myVideoWidget()
        self.video_full_screen_widget.setFullScreen(True)
        self.video_full_screen_widget.hide()
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_area)
        self.file_button.clicked.connect(self.openVideoFile)  # function of open a file
        self.play_button.clicked.connect(self.playVideo)  # play video
        self.pause_button.clicked.connect(self.pauseVideo)  # pause video
        self.player.positionChanged.connect(self.changeSlide)  # change process slide of the video
        self.video_full_screen_widget.doubleClickedItem.connect(self.videoDoubleClicked)  # double click the video
        # self.video_area.doubleClickedItem.connect(self.videoDoubleClicked)
        self.video_process_slider.setTracking(False)
        self.video_process_slider.sliderReleased.connect(self.releaseSlider)
        self.video_process_slider.sliderPressed.connect(self.pressSlider)
        self.video_process_slider.sliderMoved.connect(self.moveSlider)
        self.test_thread = VideoThread()
        self.test_thread.setDaemon(True)  # it will close when the parent process closes.
        self.test_thread.start()

    ###################################
    # function: move the process slider
    ###################################

    def moveSlider(self, position):
        if self.player.duration() > 0:
            video_position = int((position / 100) * self.player.duration())
            self.player.setPosition(video_position)
            self.video_process.setText(str(round(position, 2)) + '%')

    ###################################
    # function: press the process slider
    ###################################

    def pressSlider(self):
        self.video_process_slider_pressed = True
        print("pressed")

    ###################################
    # function: release the process slider
    ###################################

    def releaseSlider(self):
        self.video_process_slider_pressed = False
        print("released")

    ###################################
    # function: change the process slider
    ###################################

    def changeSlide(self, position):
        if not self.video_process_slider_pressed:
            self.video_length = self.player.duration() + 0.1
            self.video_process_slider.setValue(round((position / self.video_length) * 100))
            self.video_process.setText(str(round((position / self.video_length) * 100, 2)) + '%')

    def openVideoFile(self):
        self.player.setMedia(QMediaContent(QFileDialog.getOpenFileUrl()[0]))  # 选取视频文件
        self.player.play()  # 播放视频

    def playVideo(self):
        self.player.play()

    def pauseVideo(self):
        self.player.pause()

    def videoDoubleClicked(self, text):
        if self.player.duration() > 0:
            if self.video_full_screen:
                self.player.pause()
                self.video_full_screen_widget.hide()
                self.player.setVideoOutput(self.video_area)
                self.player.play()
                self.video_full_screen = False
            else:
                self.player.pause()
                self.video_full_screen_widget.show()
                self.player.setVideoOutput(self.video_full_screen_widget)
                self.player.play()
                self.video_full_screen = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_gui = myMainWindow()
    video_gui.show()
    sys.exit(app.exec_())
