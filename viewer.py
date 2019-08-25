#!/usr/bin/python3
"""
HDF5 File Viewer, with processing options for Hamamatsu MCD
"""
import os
import difflib
import itertools

import h5py
import numpy
import scipy.signal

from PyQt5 import QtCore, QtWidgets, QtQuick, QtQuickWidgets
import pyqtgraph as pg

class FileListModel(QtCore.QAbstractListModel):
    """
    Model to list files under given path
    """
    def __init__(self, parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.fileRootPath = QtCore.QDir()
        self.fileInfoList = []
        self.fileTime = QtCore.QFileInfo(self.fileRootPath.absolutePath()).lastModified()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateFiles)
        self.timer.start(2000)

    def rowCount(self, parent):
        """
        Reimplemented from QAbstractListModel
        """
        return len(self.fileInfoList)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Reimplemented from QAbstractListModel
        """
        if not index.isValid():
            return QtCore.QVariant()

        if index.row() >= len(self.fileInfoList) or index.row() < 0:
            return QtCore.QVariant()

        if role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.fileInfoList[index.row()].fileName())
        else:
            return QtCore.QVariant()

    def rootPath(self):
        """
        root path, to which the files are searched
        """
        return self.fileRootPath.absolutePath()

    def setRootPath(self, path):
        """
        change the root path
        """
        self.fileRootPath.setPath(path)
        self.beginResetModel()
        self.fileInfoList = self.fileRootPath.entryInfoList()
        self.fileTime = QtCore.QFileInfo(self.fileRootPath.absolutePath()).lastModified()
        self.endResetModel()

    def filePath(self, index):
        """
        file path part of the file referenced by index
        """
        return self.fileInfoList[index.row()].filePath()

    def fileName(self, index):
        """
        file name part of the file referenced by index
        """
        return self.fileInfoList[index.row()].fileName()

    def filter(self):
        """
        filter applied to root path, see QDir.filter
        """
        return self.fileRootPath.filter()

    def setFilter(self, filter):
        """
        filter applied to root path, see QDir.filter
        """
        self.beginResetModel()
        self.fileRootPath.setFilter(filter)
        self.fileInfoList = self.fileRootPath.entryInfoList()
        self.endResetModel()

    def nameFilters(self):
        """
        name filter applied to root path, see QDir.nameFilters
        """
        return self.fileRootPath.nameFilters()

    def setNameFilters(self, filters):
        """
        name filter applied to root path, see QDir.nameFilters
        """
        self.beginResetModel()
        self.fileRootPath.setNameFilters(filters)
        self.fileInfoList = self.fileRootPath.entryInfoList()
        self.endResetModel()

    def updateFiles(self):
        """
        Update files list, only when the last modified timestamp if newer.
        It makes small insert/remove by inspecting the incremental difference.
        """
        fileTime = QtCore.QFileInfo(self.fileRootPath.absolutePath()).lastModified()
        if self.fileTime >= fileTime:
            return
        self.fileTime = fileTime

        self.fileRootPath.refresh()
        fileInfoList = self.fileRootPath.entryInfoList()

        fileListOld = [fi.fileName() for fi in self.fileInfoList]
        fileListNew = [fi.fileName() for fi in fileInfoList]
        difflist = list(difflib.ndiff(fileListOld, fileListNew))

        i = 0
        for k,g in itertools.groupby(difflist, key=lambda x: x[0]):
            g = list(v[2:] for v in g)
            if k == ' ':
                i += len(g)
            elif k == '-':
                self.beginRemoveRows(QtCore.QModelIndex(), i, i + len(g))
                self.fileInfoList[i:i+len(g)] = []
                self.endRemoveRows()
            elif k == '+':
                self.beginInsertRows(QtCore.QModelIndex(), i, i + len(g))
                self.fileInfoList[i:i] = fileInfoList[i:i+len(g)]
                i += len(g)
                self.endInsertRows()


class FileViewer(QtWidgets.QWidget):
    def __init__(self, filepath, parent=None):
        super(FileViewer, self).__init__(parent)

        self.images = None

        self.listModel = FileListModel()
        self.listModel.setFilter(QtCore.QDir.Files)
        self.listModel.setNameFilters(['*.h5'])

        mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(mainLayout)

        layout = QtWidgets.QHBoxLayout()
        button = QtWidgets.QPushButton('...')
        button.setFixedWidth(80)
        button.clicked.connect(self.browseFolder)
        layout.addWidget(button)
        self.editDir = QtWidgets.QLineEdit()
        self.editDir.editingFinished.connect(self.setPath)
        layout.addWidget(self.editDir)

        mainLayout.addLayout(layout)

        layout = QtWidgets.QHBoxLayout()
        listWidget = QtWidgets.QListView()
        listWidget.setFixedWidth(120)
        listWidget.setModel(self.listModel)
        listWidget.activated.connect(self.itemActivated)

        layout.addWidget(listWidget)

        vlayout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(QtWidgets.QLabel('Processing: '))
        self.checkProcess = QtWidgets.QCheckBox('Enable')
        hlayout.addWidget(self.checkProcess)
        hlayout.addWidget(QtWidgets.QLabel('Median filter size: '))
        self.editKernSize = QtWidgets.QSpinBox()
        self.editKernSize.setRange(3, 10)
        hlayout.addWidget(self.editKernSize)
        self.comboDeriv = QtWidgets.QComboBox()
        self.comboDeriv.addItems(['Pos', 'Neg', 'Both', 'Original'])
        hlayout.addWidget(self.comboDeriv)
        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding))
        hlayout.addWidget(QtWidgets.QLabel('Select'))
        self.comboFrame = QtWidgets.QComboBox()
        self.comboFrame.currentIndexChanged.connect(self.frameChanged)
        hlayout.addWidget(self.comboFrame)
        vlayout.addLayout(hlayout)

        self.imageView = pg.ImageView()
        self.imageView.imageItem.setOpts(axisOrder='row-major')
        self.imageView.scene.sigMouseMoved.connect(self.mouseMoved)
        vlayout.addWidget(self.imageView)

        self.infoLabel = QtWidgets.QLabel()
        vlayout.addWidget(self.infoLabel)

        layout.addLayout(vlayout)

        mainLayout.addLayout(layout)

        self.editDir.setText(filepath)
        self.setPath()
        
    def browseFolder(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self,
                    'Brow Image Folder',
                    self.editDir.text(),
                    QtWidgets.QFileDialog.DontResolveSymlinks | QtWidgets.QFileDialog.ShowDirsOnly)
        if not directory:
            return
        self.editDir.setText(directory)
        self.setPath()

    def setPath(self):
        if not os.path.exists(os.path.dirname(self.editDir.text())):
            return
        filepath = self.editDir.text()
        self.listModel.setRootPath(filepath)

    def frameChanged(self, index):
        if index < 0:
            return

        image = self.images[:,:,index] if len(self.images.shape) > 2 else self.images

        if self.checkProcess.isChecked():
            size= self.editKernSize.value()
            image = scipy.signal.medfilt2d(image.astype(float), size)
            image = numpy.gradient(image, axis=1)
            deriv = self.comboDeriv.currentIndex()
            if deriv == 0:
                image[image<0] = 0
            elif deriv == 1:
                image[image>0] = 0
                negatives = image<0
                image[negatives] = -1 * image[negatives]
            elif deriv == 2:
                negatives = image<0
                image[negatives] = -1 * image[negatives]
            else:
                pass
            image = image.astype(numpy.int32)

        self.imageView.setImage(image)

    def itemActivated(self, index):
        filepath = self.listModel.filePath(index)
        filename = self.listModel.fileName(index)

        try:
            f = h5py.File(filepath, 'r')
        except:
            QtWidgets.QMessageBox.warning(self, "HDF5 Viewer", "Unable to open file %s" % filename)
            return

        self.images = f['/entry/instrument/detector/data'].value
        self.comboFrame.clear()
        if len(self.images.shape) > 2:
            for i in range(self.images.shape[2]):
                self.comboFrame.addItem('%d' % (i+1))
        else:
            self.comboFrame.addItem('1')

    def mouseMoved(self, pos):
        if self.imageView.image is None:
            return
        data = self.imageView.image # or use a self.data member
        nrows, ncols = data.shape

        scenePos = self.imageView.getImageItem().mapFromScene(pos)
        row, col = int(scenePos.y()), int(scenePos.x())

        if (0 <= row < nrows) and (0 <= col < ncols):
            value = data[row, col]
            self.infoLabel.setText("pos = ({:d}, {:d}), value = {!r}".format(row, col, value))
        else:
            self.infoLabel.setText('')


if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='Hamamatsu MCD File View')
    parser.add_argument('filepath', nargs='?', default='.',
                    help='File Path')
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    viewer = FileViewer(args.filepath)
    viewer.setWindowTitle('HDF5 Image Viewer')
    viewer.resize(800, 600)
    viewer.show()

    app.exec_()
