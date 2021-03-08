import tello
from tello_control_ui import TelloUI
import cv2
import detect as dt

def main():
    drone = tello.Tello('', 8889)
    vplayer = TelloUI(drone, "./img/")

    # start the Tkinter mainloop
    vplayer.root.mainloop()


if __name__ == "__main__":
    main()
