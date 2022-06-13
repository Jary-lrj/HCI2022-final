import threading

import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimediaWidgets import QVideoWidget
from GUI import Ui_Form
from myVideoWidget import myVideoWidget
import sys
import HandTrackingThread as GestureThread  # Modules of hand tracking
from qt_material import apply_stylesheet


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


class QSSLoader:
    def __init__(self):
        pass

    @staticmethod
    def read_qss_file(qss_file_name):
        with open(qss_file_name, 'r', encoding='UTF-8') as file:
            return file.read()


class myMainWindow(Ui_Form, QMainWindow):
    def __init__(self):
        super(Ui_Form, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("手势识别互动多媒体播放器")
        self.video_process_slider_pressed = False
        self.video_full_screen = False
        self.video_full_screen_widget = myVideoWidget()
        self.video_full_screen_widget.setFullScreen(True)
        self.video_full_screen_widget.hide()
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video_area)
        self.playlist = QMediaPlaylist(self)
        self.player.setPlaylist(self.playlist)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.video_list.itemClicked.connect(self.playVideoFromList)
        self.previous.clicked.connect(self.preMedia)
        self.next.clicked.connect(self.nextMedia)
        self.player_volume.setValue(50)
        self.player_volume.setTickInterval(10)
        self.player_volume.setTickPosition(QSlider.TicksBelow)
        self.player_volume.valueChanged.connect(self.changeVolume)
        self.fileOpenAction.triggered.connect(self.openVideoFile)
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
            cur = QDateTime.fromMSecsSinceEpoch(video_position).toString("mm:ss")
            tot = QDateTime.fromMSecsSinceEpoch(self.player.duration()).toString("mm:ss")
            self.video_process.setText(cur + '/' + tot)

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
            cur = QDateTime.fromMSecsSinceEpoch(position).toString("mm:ss")
            tot = QDateTime.fromMSecsSinceEpoch(self.player.duration()).toString("mm:ss")
            self.video_process.setText(cur + '/' + tot)

    def openVideoFile(self):
        mediaUrl = QFileDialog.getOpenFileUrl()[0]
        self.player.setMedia(QMediaContent(mediaUrl))  # 选取视频文件
        content = QListWidgetItem(mediaUrl.toString())
        self.video_list.addItem(content)
        self.playlist.addMedia(QMediaContent(mediaUrl))
        if self.player.state() != QMediaPlayer.PlayingState:
            self.playlist.setCurrentIndex(0)
            self.player.play()

        self.play_button2.setPixmap(QPixmap('D:\\HCI2022\\final\\assets\\pause.png'))
        self.play_button2.clicked.connect(self.pauseVideo)
        self.player.play()

    def playVideo(self):
        self.player.play()
        self.play_button2.setPixmap(QPixmap('D:\\HCI2022\\final\\assets\\pause.png'))
        self.play_button2.clicked.disconnect()
        self.play_button2.clicked.connect(self.pauseVideo)

    def pauseVideo(self):
        self.player.pause()
        self.play_button2.clicked.disconnect()
        self.play_button2.setPixmap(QPixmap('D:\\HCI2022\\final\\assets\\play-button.png'))
        self.play_button2.clicked.connect(self.playVideo)

    def playVideoFromList(self, current):
        index = self.video_list.row(current)
        self.player.setMedia(self.playlist.media(index))
        self.playlist.setCurrentIndex(index)
        self.player.play()

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

    def nextMedia(self):
        self.playlist.setCurrentIndex(self.playlist.nextIndex())
        self.video_list.setCurrentRow(self.playlist.currentIndex())
        self.player.setMedia(self.playlist.media(self.playlist.currentIndex()))
        self.player.play()

    def preMedia(self):
        self.playlist.setCurrentIndex(self.playlist.previousIndex())
        self.video_list.setCurrentRow(self.playlist.currentIndex())
        self.player.setMedia(self.playlist.media(self.playlist.currentIndex()))
        self.player.play()

    def changeVolume(self, num):
        self.player.setVolume(num)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_gui = myMainWindow()
    apply_stylesheet(app, 'dark_blue.xml')
    video_gui.show()
    sys.exit(app.exec_())
