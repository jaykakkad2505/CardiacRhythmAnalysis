"""
A QStackedWidget that slides pages in/out horizontally instead of
switching instantly - gives the app the 'page swiping' animation.
"""

from PySide6.QtCore import QPoint, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve
from PySide6.QtWidgets import QStackedWidget


class SlidingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration_ms = 320
        self.easing = QEasingCurve.OutCubic
        self._animating = False
        self._anim_group = None

    def slide_to_index(self, next_index: int):
        current_index = self.currentIndex()

        if self._animating or next_index == current_index:
            return
        if next_index < 0 or next_index >= self.count():
            return

        self._animating = True

        direction = 1 if next_index > current_index else -1

        current_widget = self.widget(current_index)
        next_widget = self.widget(next_index)

        rect = self.frameRect()
        width = rect.width()
        height = rect.height()

        next_widget.setGeometry(0, 0, width, height)
        next_widget.move(direction * width, 0)
        next_widget.show()
        next_widget.raise_()

        anim_out = QPropertyAnimation(current_widget, b"pos")
        anim_out.setDuration(self.duration_ms)
        anim_out.setEasingCurve(self.easing)
        anim_out.setStartValue(QPoint(0, 0))
        anim_out.setEndValue(QPoint(-direction * width, 0))

        anim_in = QPropertyAnimation(next_widget, b"pos")
        anim_in.setDuration(self.duration_ms)
        anim_in.setEasingCurve(self.easing)
        anim_in.setStartValue(QPoint(direction * width, 0))
        anim_in.setEndValue(QPoint(0, 0))

        group = QParallelAnimationGroup(self)
        group.addAnimation(anim_out)
        group.addAnimation(anim_in)

        def on_finished():
            self.setCurrentIndex(next_index)
            current_widget.move(0, 0)
            self._animating = False

        group.finished.connect(on_finished)
        self._anim_group = group  # keep a reference so it isn't garbage collected
        group.start()
