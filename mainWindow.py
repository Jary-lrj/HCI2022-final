import math
import cv2
import numpy as np
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from GUI import Ui_Form
import sys
import time
import HandTrackingThread as GestureThread  # Modules of hand tracking
from qt_material import apply_stylesheet


#########################################
# function: A override video widget
# enable double click.
#########################################
class myVideoWidget(QVideoWidget):
    doubleClickedItem = pyqtSignal(str)  # 创建双击信号

    def __init__(self, parent=None):
        super(QVideoWidget, self).__init__(parent)

    def mouseDoubleClickEvent(self, QMouseEvent):  # 双击事件
        self.doubleClickedItem.emit("double clicked")


#########################################
# function: Gesture capture, detector
# and analyze thread.
#########################################
class VideoThread(QThread):
    nextMedia = pyqtSignal(int)
    preMedia = pyqtSignal(int)
    like = pyqtSignal(int)
    dislike = pyqtSignal(int)
    volume = pyqtSignal(int)
    valueChange = pyqtSignal(int)
    speedChange = pyqtSignal(int)
    goAhead = pyqtSignal(int)
    goBack = pyqtSignal(int)

    def __init__(self):
        super(VideoThread, self).__init__()
        self.isPause = False
        self.isCancel = False
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.detector = GestureThread.handDetector(detectionCon=0.75)
        self.cap = cv2.VideoCapture(0)

    # pause the thread.
    def pause(self):
        self.isPause = True

    # resume the paused thread.
    def resume(self):
        self.isPause = False
        self.cond.wakeAll()

    # cancel the thread.
    def cancel(self):
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
                    if finger2_x < lm_list[6][1] and finger3_x > lm_list[10][1] and finger4_x > \
                            lm_list[14][1] and finger5_x > lm_list[18][1]:
                        self.nextMedia.emit(1)
                    elif finger1_y < finger2_y and finger2_x > lm_list[6][1] and finger3_x > \
                            lm_list[10][1] and finger4_x > \
                            lm_list[14][1] and finger5_x > lm_list[18][1]:
                        self.like.emit(1)  # show your like to the media
                    elif finger2_x < lm_list[6][1] and finger3_x < lm_list[10][1] and finger4_x > \
                            lm_list[14][1] and finger5_x > lm_list[18][1]:
                        self.goAhead.emit(1)
                    else:
                        self.dislike.emit(1)  # show your dislike to the media

                elif finger1_x < finger2_x and finger3_x > finger1_x and finger4_x > finger1_x and finger5_x > finger1_x:
                    if finger2_x > lm_list[6][1] and finger3_x < lm_list[10][1] and finger4_x < \
                            lm_list[14][1] and finger5_x < lm_list[18][1]:
                        self.preMedia.emit(1)
                    elif finger2_y < finger1_y:
                        length = math.hypot(finger1_x - finger2_x, finger1_y - finger2_y)
                        vol = np.interp(length, [10, 200], [0, 100])
                        self.volume.emit(vol)
                    elif finger2_x > lm_list[6][1] and finger3_x > lm_list[10][1] and finger4_x < \
                            lm_list[14][1] and finger5_x < lm_list[18][1]:
                        self.goBack.emit(1)

                elif finger2_y < finger1_y and finger2_y < finger3_y and finger2_y < finger4_y and finger2_y < finger5_y:
                    self.speedChange.emit(1)
                elif finger1_y > finger2_y > finger3_y and finger2_y < finger4_y and finger2_y < finger5_y:
                    self.speedChange.emit(2)
                elif finger1_y > finger2_y > finger3_y and finger4_y < finger1_y and finger4_y < finger5_y and finger2_y < finger5_y and finger1_y < finger5_y:
                    self.speedChange.emit(3)
                elif finger1_y > finger2_y and finger3_y < finger1_y and finger4_y < finger1_y and finger5_y < finger1_y:
                    self.speedChange.emit(4)
            # 线程锁off
            self.mutex.unlock()


#########################################
# function: main GUI
#########################################
class myMainWindow(Ui_Form, QMainWindow):
    def __init__(self):
        super(Ui_Form, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("手势识别互动多媒体播放器")
        self.setWindowIcon(QIcon("./assets/logo.ico"))
        self.video_process_slider_pressed = False
        self.video_full_screen = False
        self.video_full_screen_widget = myVideoWidget(self)
        self.video_full_screen_widget.setFullScreen(True)
        self.video_full_screen_widget.hide()
        self.video_full_screen_widget.doubleClickedItem.connect(self.videoDoubleClicked)  # double click the video
        self.video_area.doubleClickedItem.connect(self.videoDoubleClicked)
        self.player = QMediaPlayer()
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
        self.player.positionChanged.connect(self.changeSlide)  # change process slide of the video
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
        self.gestureThread.goAhead.connect(self.goAhead)
        self.gestureThread.goBack.connect(self.goBack)
        self.gestureThread.speedChange.connect(self.setVideoSpeed)

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

    ###################################
    # function: release the process slider
    ###################################

    def releaseSlider(self):
        self.video_process_slider_pressed = False

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

    #########################################
    # function: open a video file and play it.
    #########################################
    def openVideoFile(self):
        mediaUrl = QFileDialog.getOpenFileUrl()[0]
        self.player.setMedia(QMediaContent(mediaUrl))  # 选取视频文件
        content = QListWidgetItem(mediaUrl.toString())
        self.video_list.addItem(content)
        self.playlist.addMedia(QMediaContent(mediaUrl))
        if self.player.state() != QMediaPlayer.PlayingState:
            self.playlist.setCurrentIndex(self.playlist.currentIndex() + 1)
            self.player.play()
        self.play_button2.setPixmap(QPixmap('D:\\HCI2022\\final\\assets\\pause.png'))
        self.play_button2.clicked.connect(self.pauseVideo)
        self.player.play()

    #########################################
    # function: remove the selected video from video list and playlist.
    #########################################
    def removeVideoFile(self):
        print(self.playlist.currentIndex())
        self.video_list.takeItem(self.playlist.currentIndex())
        self.playlist.removeMedia(self.playlist.currentIndex())
        self.player.setMedia(self.playlist.media(self.playlist.currentIndex()))
        print(self.playlist.currentIndex())
        self.player.play()

    #########################################
    # function: play the video.
    #########################################
    def playVideo(self):
        self.player.play()
        self.play_button2.setPixmap(QPixmap('D:\\HCI2022\\final\\assets\\pause.png'))
        self.play_button2.clicked.disconnect()
        self.play_button2.clicked.connect(self.pauseVideo)

    #########################################
    # function: pause the video.
    #########################################
    def pauseVideo(self):
        self.player.pause()
        self.play_button2.clicked.disconnect()
        self.play_button2.setPixmap(QPixmap('D:\\HCI2022\\final\\assets\\play-button.png'))
        self.play_button2.clicked.connect(self.playVideo)

    ####################################################################
    # function: select an existed video and play it  from the video list
    ####################################################################
    def playVideoFromList(self, current):
        index = self.video_list.row(current)
        self.player.setMedia(self.playlist.media(index))
        self.playlist.setCurrentIndex(index)
        self.player.play()

    ####################################################################
    # function: switch from full screen to a window form
    ####################################################################
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

    #################################################
    # function: play the next video in the video list.
    #################################################
    def nextMedia(self):
        self.playlist.setCurrentIndex(self.playlist.nextIndex())
        self.video_list.setCurrentRow(self.playlist.currentIndex())
        self.player.setMedia(self.playlist.media(self.playlist.currentIndex()))
        self.player.play()

    ######################################################
    # function: play the previous video in the video list.
    ######################################################
    def preMedia(self):
        self.playlist.setCurrentIndex(self.playlist.previousIndex())
        self.video_list.setCurrentRow(self.playlist.currentIndex())
        self.player.setMedia(self.playlist.media(self.playlist.currentIndex()))
        self.player.play()

    ###########################################
    # function: change the volume of the player
    ###########################################
    def changeVolume(self, num):
        self.player.setVolume(num)
        self.player_volume.setValue(num)

    ###############################################
    # function: set the playing speed of the video.
    ##############################################
    def setVideoSpeed(self, speed):
        self.player.setPlaybackRate(speed)

    #########################################
    # function: user likes the media.
    #########################################
    def like(self, event):
        self.gestureThread.pause()
        reply = QMessageBox.information(self, "提示", "收到您的喜欢！感谢您对本视频的喜欢！", QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.gestureThread.resume()

    #########################################
    # function: user dislikes the media.
    #########################################
    def dislike(self, event):
        self.gestureThread.pause()
        reply = QMessageBox.information(self, "提示", "收到您的不喜欢！我们将努力提供更让您喜欢的内容！", QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.gestureThread.resume()

    ############################################
    # function: make the video go ahead for 5sec
    ############################################
    def goAhead(self):
        if self.player.duration() > 0 and self.player.duration() - self.player.position() < 5000:  # 不足5秒
            self.player.setPosition(self.player.duration())
        else:
            self.player.setPosition(self.player.position() + 5000)
        cur = QDateTime.fromMSecsSinceEpoch(self.player.position()).toString("mm:ss")
        tot = QDateTime.fromMSecsSinceEpoch(self.player.duration()).toString("mm:ss")
        self.video_process.setText(cur + '/' + tot)

    ###########################################
    # function: make the video go back for 5sec
    ###########################################
    def goBack(self):
        if self.player.duration() > 0 and self.player.position() < 5000:  # 不足5秒
            self.player.setPosition(0)
        else:
            self.player.setPosition(self.player.position() - 5000)
        cur = QDateTime.fromMSecsSinceEpoch(self.player.position()).toString("mm:ss")
        tot = QDateTime.fromMSecsSinceEpoch(self.player.duration()).toString("mm:ss")
        self.video_process.setText(cur + '/' + tot)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_gui = myMainWindow()
    apply_stylesheet(app, 'dark_blue.xml')  # set a set of stylesheet.
    video_gui.show()
    sys.exit(app.exec_())
