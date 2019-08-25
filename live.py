#!/usr/bin/env python3
"""
Live view of Hamamatsu MCD image via EPICS
"""
import numpy
import pyqtgraph
from PyQt5 import QtCore, QtWidgets
from epicsPV import epicsPV

class MCDImages():
    """
    MCD Live Images via EPICS, assuming the same interface as areaDetector NDPluginStdArrays
    """

    def __init__(self, prefix):
        self.image_listener = None
        self.image = None

        self.sizex = epicsPV(prefix + 'ArraySizeX_RBV', wait=False)
        self.sizey = epicsPV(prefix + 'ArraySizeY_RBV', wait=False)
        self.sizez = epicsPV(prefix + 'ArraySizeZ_RBV', wait=False)
        self.array = epicsPV(prefix + 'ArrayData', wait=True)

        self.sizex.setMonitor()
        self.sizey.setMonitor()
        self.sizez.setMonitor()
        self.array.add_masked_array_event(None, 0, None, self._new_data, use_numpy=True)
        self.array.flush_io()

    def add_image_listener(self, image_listener):
        """
        subscribe for new image event
        """
        self.image_listener = image_listener

        if self.image is not None:
            self.image_listener(self.image)

    def _new_data(self, epics_args, _):
        x = self.sizex.getValue()
        y = self.sizey.getValue()
        z = self.sizez.getValue()
        array = epics_args['pv_value']

        if z == 0:
            z = 1
        if not x or not y or not z or array.size != x * y * z:
            return

        array.shape = (y, x, z)
        self.image = array

        self.image_listener(self.image)


class MCDImagesLiveViewer(QtWidgets.QMainWindow):
    """
    Main window
    """
    imageUpdated = QtCore.pyqtSignal(numpy.ndarray)

    def __init__(self, prefix):
        super(MCDImagesLiveViewer, self).__init__()

        self.imageView = pyqtgraph.ImageView(self)
        self.imageView.imageItem.setOpts(axisOrder='row-major')
        self.setCentralWidget(self.imageView)
        self.imageUpdated.connect(self._update_image)

        self.images = MCDImages(prefix)
        self.images.add_image_listener(self._new_image)

    def _new_image(self, image):
        self.imageUpdated.emit(image)

    def _update_image(self, image):
        self.imageView.setImage(image[:, :, 0])


if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='Hamamatsu MCD Live View')
    parser.add_argument('--prefix', default='iMott:',
                    help='EPICS PVs prefix')
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    win = MCDImagesLiveViewer(args.prefix)
    win.setWindowTitle('Hamamatsu C7557-1 Live View')
    win.resize(800, 600)
    win.show()
    app.exec_()
