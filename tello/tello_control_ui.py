from PIL import Image
from PIL import ImageTk
import tkinter as tki
from tkinter import Toplevel, Scale
import threading
import datetime
import cv2
import os
import time
import platform
import tello
import detect as dt

from multiprocessing import Process, Pipe

DRONE = False


class TelloUI:
    """Wrapper class to enable the GUI."""

    def __init__(self, tello, outputpath):
        """
        Initial all the element of the GUI,support by Tkinter

        :param tello: class interacts with the Tello drone.

        Raises:
            RuntimeError: If the Tello rejects the attempt to enter command mode.
        """

        self.tello = tello  # videostream device
        self.outputPath = outputpath  # the path that save pictures created by clicking the takeSnapshot button
        self.frame = None  # frame read from h264decoder and used for pose recognition
        self.thread = None  # thread of the Tkinter mainloop
        self.stopEvent = None

        # control variables
        self.distance = 0.1  # default distance for 'move' cmd
        self.degree = 30  # default degree for 'cw' or 'ccw' cmd

        # if the flag is TRUE,the auto-takeoff thread will stop waiting for the response from tello
        self.quit_waiting_flag = False

        # initialize the root window and image panel
        self.root = tki.Tk()
        self.root.geometry('400x200')
        self.panel = None

        # create buttons
        self.btn_snapshot = tki.Button(self.root, text="Snapshot!",
                                       command=self.takeSnapshot)
        self.btn_snapshot.pack(side="bottom", fill="both",
                               expand="yes", padx=10, pady=5)

        self.btn_pause = tki.Button(self.root, text="Pause", relief="raised",
                                    command=self.pauseVideo)
        self.btn_pause.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        self.btn_landing = tki.Button(
            self.root, text="Open Command Panel", relief="raised", command=self.openCmdWindow)
        self.btn_landing.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        # start a thread that constantly pools the video sensor for
        # the most recently read frame

        # self.thread = threading.Thread(target=self.videoLoop, args=())
        # self.thread.start()

        # set a callback to handle when the window is closed
        self.root.wm_title("TELLO Controller")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        # define threading event
        self.stopEvent = threading.Event()
        # the sending_command will send command to tello every 5 seconds
        self.sending_command_thread = threading.Thread(target=self._sendingCommand)

        # the yolo thread will begin after receive video from tello
        self.yolo_thread_thread = threading.Thread(target=self._yoloBegin)

        # this is update state mess threading
        self.state_mess_thread_thread = threading.Thread(target=self._updateMess)
        # tello state dict
        self.tello_state = {}

        self.state_message = tki.StringVar()
        self.state_message.set("this is drone state")
        self.parent_conn, self.child_conn = Pipe()
        if DRONE:
            self.p = Process(target=dt.start_detect, args=(
                "--source udp://@0.0.0.0:11111 --weights ../weights/yolov5s.pt --conf 0.55 --classes 0".split(), self.child_conn))
        else:
            self.p = Process(target=dt.start_detect, args=("--source 0 --weights ../weights/yolov5s.pt --conf 0.55 --classes "
                                                           "0".split(), self.child_conn))

    def YoloLoop(self):
        try:
            time.sleep(0.5)
            self.yolo_thread_thread.start()
            time.sleep(0.5)
            self.state_mess_thread_thread.start()
        except RuntimeError as e:
            print(e)

    def _yoloBegin(self):
        self.p.start()
        self.p.join()
        print("chile process exit".format())

    def _sendingCommand(self):
        """
        start a while loop that sends 'command' to tello every 5 second
        """

        while True:
            self.tello.send_command('command')
            time.sleep(0.5)
            self.tello.get_battery()
            time.sleep(1)
            print(self.tello.response)
            time.sleep(3.5)

    def _setQuitWaitingFlag(self):
        """
        set the variable as TRUE,it will stop computer waiting for response from tello
        """
        self.quit_waiting_flag = True

    def _updateMess(self):
        while True:
            result = self.parent_conn.recv()
            self.setStateMessage(result)
            if (len(result) != 0):
                print(result)
                self._judge(result)
            time.sleep(0.01)

    def _judge(self, result):
        x = (result[0][0][0] + result[0][1][0]) >> 1
        y = (result[0][0][1] + result[0][1][1]) >> 1
        half_m = 240
        half_n = 320
        if x > 340:
            self.telloCW(3)
        elif x < 300:
            self.telloCCW(3)

    def setStateMessage(self, stateMess):
        mess = ''
        for i in range(len(stateMess)):
            mess = mess + "检测到的第{}个目标左上角坐标{}右下角坐标{}\n".format(i + 1, str(stateMess[i][0]), str(stateMess[i][1]))
        self.state_message.set(mess)

    def openCmdWindow(self):
        """
        open the cmd window and initial all the button and text
        """
        # begin keep live thread,either tello will take land after 15 seconds without command
        time.sleep(0.5)
        self.sending_command_thread.start()

        panel = Toplevel(self.root)
        panel.wm_title("Command Panel")

        text_state = tki.Label(panel, textvariable=self.state_message, font='Helvetica 10 bold', height=5, width=20)

        text_state.pack(side='top', fill='both', expand="yes", padx=10, pady=5)

        # create text input entry
        # text0 = tki.Label(panel,
        #                   text='This Controller map keyboard inputs to Tello control commands\n'
        #                        'Adjust the trackbar to reset distance and degree parameter',
        #                   font='Helvetica 10 bold'
        #                   )
        # text0.pack(side='top')

        # text1 = tki.Label(panel, text=
        # 'W - Move Tello Up\t\t\tArrow Up - Move Tello Forward\n'
        # 'S - Move Tello Down\t\t\tArrow Down - Move Tello Backward\n'
        # 'A - Rotate Tello Counter-Clockwise\tArrow Left - Move Tello Left\n'
        # 'D - Rotate Tello Clockwise\t\tArrow Right - Move Tello Right',
        #                   justify="left")
        # text1.pack(side="top")

        self.btn_landing = tki.Button(panel, text="Land", relief="raised", command=self.telloLanding)
        self.btn_landing.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.btn_takeoff = tki.Button(
            panel, text="Takeoff", relief="raised", command=self.telloTakeOff)
        self.btn_takeoff.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        # binding arrow keys to drone control
        self.tmp_f = tki.Frame(panel, width=100, height=2)
        self.tmp_f.bind('<KeyPress-w>', self.on_keypress_w)
        self.tmp_f.bind('<KeyPress-s>', self.on_keypress_s)
        self.tmp_f.bind('<KeyPress-a>', self.on_keypress_a)
        self.tmp_f.bind('<KeyPress-d>', self.on_keypress_d)
        self.tmp_f.bind('<KeyPress-Up>', self.on_keypress_up)
        self.tmp_f.bind('<KeyPress-Down>', self.on_keypress_down)
        self.tmp_f.bind('<KeyPress-Left>', self.on_keypress_left)
        self.tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
        self.tmp_f.pack(side="bottom")
        self.tmp_f.focus_set()

        self.btn_landing = tki.Button(
            panel, text="Flip", relief="raised", command=self.openFlipWindow)
        self.btn_landing.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.distance_bar = Scale(panel, from_=0.02, to=5, tickinterval=0.01, digits=3,
                                  label='Distance(m)',
                                  resolution=0.01)
        self.distance_bar.set(0.2)
        self.distance_bar.pack(side="left")

        self.btn_distance = tki.Button(panel, text="Reset Distance", relief="raised",
                                       command=self.updateDistancebar,
                                       )
        self.btn_distance.pack(side="left", fill="both",
                               expand="yes", padx=10, pady=5)

        self.degree_bar = Scale(panel, from_=1, to=360, tickinterval=10, label='Degree')
        self.degree_bar.set(30)
        self.degree_bar.pack(side="right")

        self.btn_distance = tki.Button(panel, text="Reset Degree", relief="raised",
                                       command=self.updateDegreebar)
        self.btn_distance.pack(side="right", fill="both",
                               expand="yes", padx=10, pady=5)

        self.btn_start_yolo = tki.Button(panel, text="start yolo", relief='raised',
                                         command=self.YoloLoop).pack(
            side="bottom", fill="both",
            expand="yes", padx=10, pady=5)

    def openFlipWindow(self):
        """
        open the flip window and initial all the button and text
        """

        panel = Toplevel(self.root)
        panel.wm_title("Gesture Recognition")

        self.btn_flipl = tki.Button(
            panel, text="Flip Left", relief="raised", command=self.telloFlip_l)
        self.btn_flipl.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        self.btn_flipr = tki.Button(
            panel, text="Flip Right", relief="raised", command=self.telloFlip_r)
        self.btn_flipr.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        self.btn_flipf = tki.Button(
            panel, text="Flip Forward", relief="raised", command=self.telloFlip_f)
        self.btn_flipf.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        self.btn_flipb = tki.Button(
            panel, text="Flip Backward", relief="raised", command=self.telloFlip_b)
        self.btn_flipb.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

    def takeSnapshot(self):
        """
        save the current frame of the video as a jpg file and put it into outputpath
        """

        # grab the current timestamp and use it to construct the filename
        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))

        p = os.path.sep.join((self.outputPath, filename))

        # save the file
        cv2.imwrite(p, cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR))
        print("[INFO] saved {}".format(filename))

    def pauseVideo(self):
        """
        Toggle the freeze/unfreze of video
        """
        if self.btn_pause.config('relief')[-1] == 'sunken':
            self.btn_pause.config(relief="raised")
            self.tello.video_freeze(False)
        else:
            self.btn_pause.config(relief="sunken")
            self.tello.video_freeze(True)

    def telloTakeOff(self):
        return self.tello.takeoff()

    def telloLanding(self):
        return self.tello.land()

    def telloFlip_l(self):
        return self.tello.flip('l')

    def telloFlip_r(self):
        return self.tello.flip('r')

    def telloFlip_f(self):
        return self.tello.flip('f')

    def telloFlip_b(self):
        return self.tello.flip('b')

    def telloCW(self, degree):
        return self.tello.rotate_cw(degree)

    def telloCCW(self, degree):
        return self.tello.rotate_ccw(degree)

    def telloMoveForward(self, distance):
        return self.tello.move_forward(distance)

    def telloMoveBackward(self, distance):
        return self.tello.move_backward(distance)

    def telloMoveLeft(self, distance):
        return self.tello.move_left(distance)

    def telloMoveRight(self, distance):
        return self.tello.move_right(distance)

    def telloUp(self, dist):
        return self.tello.move_up(dist)

    def telloDown(self, dist):
        return self.tello.move_down(dist)

    def updateTrackBar(self):
        self.my_tello_hand.setThr(self.hand_thr_bar.get())

    def updateDistancebar(self):
        self.distance = self.distance_bar.get()
        print('reset distance to %.1f' % self.distance)

    def updateDegreebar(self):
        self.degree = self.degree_bar.get()
        print('reset distance to %d' % self.degree)

    def on_keypress_w(self, event):
        print("up %d m" % self.distance)
        self.telloUp(self.distance)

    def on_keypress_s(self, event):
        print("down %d m" % self.distance)
        self.telloDown(self.distance)

    def on_keypress_a(self, event):
        print("ccw %d degree" % self.degree)
        self.tello.rotate_ccw(self.degree)

    def on_keypress_d(self, event):
        print("cw %d m" % self.degree)
        self.tello.rotate_cw(self.degree)

    def on_keypress_up(self, event):
        print("forward %d m" % self.distance)
        self.telloMoveForward(self.distance)

    def on_keypress_down(self, event):
        print("backward %d m" % self.distance)
        self.telloMoveBackward(self.distance)

    def on_keypress_left(self, event):
        print("left %d m" % self.distance)
        self.telloMoveLeft(self.distance)

    def on_keypress_right(self, event):
        print("right %d m" % self.distance)
        self.telloMoveRight(self.distance)

    def on_keypress_enter(self, event):
        if self.frame is not None:
            self.registerFace()
        self.tmp_f.focus_set()

    def onClose(self):
        """
        set the stop event, cleanup the camera, and allow the rest of

        the quit process to continue
        """
        print("[INFO] closing...")
        # self.stopEvent.set()
        del self.tello
        self.root.quit()

# drone = tello.Tello('', 8889)
# vplayer = TelloUI(drone, "./img/")
#
# # start the Tkinter mainloop
# vplayer.root.mainloop()
