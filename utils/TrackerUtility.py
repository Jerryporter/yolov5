import cv2


class TrackerUtility:
    def __init__(self):
        self.tracker = cv2.TrackerCSRT_create()
        self.track_ok = None

    def init(self, frame, track_window):
        self.tracker.init(frame, track_window)

    def update(self, frame):
        track_ok, bbox = self.tracker.update(frame)
        if track_ok:
            return bbox
        else:
            return None

    def redrawTrackWindow(self, frame, track_windows):
        self.init(frame, track_windows)
