import math
import threading

import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from GUI import Ui_Form
from myVideoWidget import myVideoWidget
import sys
import time
import HandTrackingThread as GestureThread  # Modules of hand tracking
from qt_material import apply_stylesheet


class VideoThread(QThread):
    nextMedia = pyqtSignal(int)
    preMedia = pyqtSignal(int)
    like = pyqtSignal(int)
    dislike = pyqtSignal(int)
    volume = pyqtSignal(int)

    valueChange = pyqtSignal(int)

    # valueChangeSignal = pyqtSignal(int)
    def __init__(self):
        super(VideoThread, self).__init__()
        self.isPause = False
        self.isCancel = False
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.detector = GestureThread.handDetector(detectionCon=0.75)
        self.cap = cv2.VideoCapture(0)

    # 暂停
    def pause(self):
        print("线程暂停")
        self.isPause = True

    # 恢复
    def resume(self):
        print("线程恢复")
        self.isPause = False
        self.cond.wakeAll()

    # 取消
    def cancel(self):
        print("线程取消")
        self.isCancel = True

    def run(self):
        while True:
            time.sleep(1)
            self.mutex.lock()
            if self.isPause:
                self.cond.wait(self.mutex)
            if self.isCancel:
                self.valueChange.emit(1)
                break
            success, img = self.cap.read()
            img = self.detector.findHands(img)
            lm_list = self.detector.findPosition(img)
            if len(lm_list) != 0:
                finger1_x, finger1_y = lm_list[4][1], lm_list[4][2]
                finger2_x, finger2_y = lm_list[8][1], lm_list[8][2]
                finger3_x, finger3_y = lm_list[12][1], lm_list[12][2]
                finger4_x, finger4_y = lm_list[16][1], lm_list[16][2]
                finger5_x, finger5_y = lm_list[20][1], lm_list[20][2]
                if finger1_x > finger2_x and finger3_x < finger1_x and finger4_x < finger1_x and finger5_x < finger1_x:
                    if lm_list[8][1] < lm_list[6][1] and lm_list[12][1] > lm_list[10][1] and lm_list[16][1] > \
                            lm_list[14][1] and lm_list[20][1] > lm_list[18][1]:
                        self.nextMedia.emit(1)
                    elif lm_list[4][2] < lm_list[8][2]:
                        self.like.emit(1)  # show your like to the media
                    else:
                        self.dislike.emit(1)  # show your dislike to the media

                elif finger1_x < finger2_x and finger3_x > finger1_x and finger4_x > finger1_x and finger5_x > finger1_x:
                    if lm_list[8][1] > lm_list[6][1] and lm_list[12][1] < lm_list[10][1] and lm_list[16][1] < \
                            lm_list[14][1] and lm_list[20][1] < lm_list[18][1]:
                        self.preMedia.emit(1)
                    elif lm_list[8][2] < lm_list[4][2]:
                        length = math.hypot(lm_list[4][1] - lm_list[8][1], lm_list[4][2] - lm_list[8][2])
                        vol = np.interp(length, [10, 200], [0, 100])
                        self.volume.emit(vol)
            # 线程锁off
            self.mutex.unlock()


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

        self.fileRemoveAction.triggered.connect(self.removeVideoFile)
        # self.fileOpenAction.triggered.connect(self.openVideoFile)
        self.player.positionChanged.connect(self.changeSlide)  # change process slide of the video
        self.video_full_screen_widget.doubleClickedItem.connect(self.videoDoubleClicked)  # double click the video
        # self.video_area.doubleClickedItem.connect(self.videoDoubleClicked)
        self.video_process_slider.setTracking(False)
        self.video_process_slider.sliderReleased.connect(self.releaseSlider)
        self.video_process_slider.sliderPressed.connect(self.pressSlider)
        self.video_process_slider.sliderMoved.connect(self.moveSlider)

        self.gestureThread = VideoThread()
        self.gestureThread.start()
        self.gestureThread.nextMedia.connect(self.nextMedia)  # gesture to change to next video
        self.gestureThread.preMedia.connect(self.preMedia)
        self.gestureThread.like.connect(self.like)
        self.gestureThread.dislike.connect(self.dislike)
        self.gestureThread.volume.connect(self.changeVolume)

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
            self.playlist.setCurrentIndex(self.playlist.currentIndex() + 1)
            self.player.play()

        # self.play_button2.setPixmap(
        #     QPixmap('C:\\Users\\86133\\Desktop\\HCI2022-final-main (1)\\HCI2022-final-main\\assets\\pause.png'))
        self.play_button2.setPixmap(QPixmap('D:\\HCI2022\\final\\assets\\pause.png'))
        self.play_button2.clicked.connect(self.pauseVideo)
        self.player.play()

    def removeVideoFile(self):
        # mediaUrl = QFileDialog.getOpenFileUrl()[0]
        # self.player.setMedia(QMediaContent(mediaUrl))  # 选取视频文件
        # content = QListWidgetItem(mediaUrl.toString())
        # nextIndex
        # self.video_list.addItem(content)
        print(self.playlist.currentIndex())

        self.video_list.takeItem(self.playlist.currentIndex())
        self.playlist.removeMedia(self.playlist.currentIndex())
        # self.playlist.setCurrentIndex(self.playlist.nextIndex())
        self.player.setMedia(self.playlist.media(self.playlist.currentIndex()))
        print(self.playlist.currentIndex())

        self.player.play()

    def playVideo(self):
        self.player.play()
        # self.play_button2.setPixmap(
        #     QPixmap('C:\\Users\\86133\\Desktop\\HCI2022-final-main (1)\\HCI2022-final-main\\assets\\pause.png'))
        self.play_button2.setPixmap(QPixmap('D:\\HCI2022\\final\\assets\\pause.png'))
        self.play_button2.clicked.disconnect()
        self.play_button2.clicked.connect(self.pauseVideo)

    def pauseVideo(self):
        self.player.pause()
        self.play_button2.clicked.disconnect()
        # self.play_button2.setPixmap(
        #     QPixmap('C:\\Users\\86133\\Desktop\\HCI2022-final-main (1)\\HCI2022-final-main\\assets\\play-button.png'))
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
        self.player_volume.setValue(num)

    def setVideoSpeed(self, speed):
        self.player.setPlaybackRate(speed)

    def test(self):
        print('test')

    def like(self, event):
        self.gestureThread.pause()
        reply = QMessageBox.information(self, "提示", "收到您的喜欢，请重复确认！感谢您对本视频的喜欢！", QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.gestureThread.resume()

    def dislike(self, event):
        self.gestureThread.pause()
        reply = QMessageBox.information(self, "提示", "收到您的不喜欢，请重复确认！我们将努力提供更让您喜欢的内容！", QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.gestureThread.resume()

    def goAhead15s(self):
        pass

    def goBack15s(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_gui = myMainWindow()
    apply_stylesheet(app, 'dark_blue.xml')
    video_gui.show()
    sys.exit(app.exec_())
