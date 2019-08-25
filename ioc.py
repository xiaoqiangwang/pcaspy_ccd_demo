#!/usr/bin/env python3
"""
PCASpy application for Hamamatsu MCD C7557-1
"""
import h5py
import numpy
import os
import time
import threading

from pcaspy import Driver, SimpleServer, Severity
from pcaspy.tools import ServerThread

from hamamatsu import HamamatsuMCD

pvdb = {
    # acquisition control and status
    'Acquire': {
        'type': 'enum',
        'enums': ['Stop', 'Start'],
        'asyn': True
    },
    'DetectorState_RBV': {
        'type': 'enum',
        'enums': ['Idle', 'Acquire', 'Saving', 'Un-initialized'],
        'states': [Severity.NO_ALARM, Severity.MINOR_ALARM, Severity.MINOR_ALARM, Severity.MAJOR_ALARM]
    },
    'AcquireTime':              {'units': 's', 'prec':  2, 'value': 1.12},
    'NumExposures':             {'type': 'int', 'value': 1},
    'NumExposuresCounter_RBV':  {'type': 'int', 'value': 0},

    'BinX': {'type': 'int', 'value': 1},
    'BinY': {'type': 'int', 'value': 1},

    # image data descriptors, areaDetector NDPluginStdArrays compatible
    'NDimensions_RBV': {'type': 'int', 'value': 3},
    'Dimensions_RBV':  {'type': 'int', 'count': 3},
    'DataType_RBV':    {'type': 'enum', 'enums': ['Int8','UInt8','Int16','UInt16','Int32','UInt32'], 'value': 1},
    'ArraySizeX_RBV':  {'type': 'int'},
    'ArraySizeY_RBV':  {'type': 'int'},
    'ArraySizeZ_RBV':  {'type': 'int'},
    'ArrayData':       {'type': 'char', 'count': 800000},
    'ColorMode_RBV':   {'type': 'enum', 'enums': ['Mono'], 'value': 0},

    # file saving control, areaDetector NDFile compatible
    'WriteFile':          {'type': 'enum', 'enums': ['None', 'Save']},
    'FilePath':           {'type': 'char', 'count': 128},
    'FileName':           {'type': 'char', 'count': 128},
    'FileNumber':         {'type': 'int'},
    'FileTemplate':       {'type': 'str', 'value': '%s_%04d.h5'},
    'AutoIncrement':      {'type': 'enum', 'enums': ['No', 'Yes'], 'value': 1},
    'AutoSave':           {'type': 'enum', 'enums': ['No', 'Yes'], 'value': 1},
    'FullFileName_RBV':   {'type': 'char', 'count': 256},
    'FilePathExists_RBV': {'type': 'enum', 'enums': ['No', 'Yes'],
        'states': [Severity.MAJOR_ALARM, Severity.NO_ALARM]
    },
}


class HamamatsuMCDriver(Driver):
    def __init__(self):
        Driver.__init__(self)
        self.tid = None
        self.images = None
        self.mcd = HamamatsuMCD()

    def write(self, reason, value):
        status = True
        # take proper actions
        if reason == 'Acquire':
            self.setParam(reason, value)
            if self.tid is None and value == 1:
                self.tid = threading.Thread(target=self.runAcquisition)
                self.tid.start()
        elif reason == 'WriteFile':
            if self.images is not None:
                self.openFile()
        elif reason == 'AcquireTime':
            self.mcd.set_exposure(value)
        elif reason == 'BinX':
            self.mcd.set_bin(value, self.getParam('BinY'))
        elif reason == 'BinY':
            self.mcd.set_bin(self.getParam('BinX'), value)
        elif reason == 'FilePath':
            self.setParam('FilePathExists_RBV',
                    os.path.exists(value) and os.access(value, os.W_OK))
        elif reason.endswith('_RBV'):
            status = False

        # store the values
        if status:
            self.setParam(reason, value)

        self.updatePVs()
        return status

    def runAcquisition(self):
        cycles = self.getParam('NumExposures')
        auto_save = self.getParam('AutoSave')
        # acquire
        self.images = None
        for cycle in range(cycles):
            # check for abort
            if not self.getParam('Acquire'):
                break

            self.setParam('DetectorState_RBV', 1)
            self.updatePVs()

            if self.images is None:
                self.images = self.mcd.acquire()
            else:
                self.images += self.mcd.acquire()

            # areaDetector describes image as column, row, layer
            shape = list(self.images.shape)[::-1]
            self.setParam('NDimensions_RBV', len(shape))
            self.setParam('Dimensions_RBV', shape)
            self.setParam('ArrayData', self.images)
            self.setParam('ArraySizeX_RBV', shape[0])
            self.setParam('ArraySizeY_RBV', shape[1])
            self.setParam('ArraySizeZ_RBV', shape[2] if len(shape) > 2 else 0)
            self.setParam('NumExposuresCounter_RBV', cycle + 1)
            self.updatePVs()

            if auto_save:
                self.setParam('DetectorState_RBV', 2)
                if cycle == 0:
                    self.openFile()
                else:
                    self.saveFile()
                self.updatePVs()

        self.setParam('Acquire', 0)
        self.callbackPV('Acquire')

        self.setParam('DetectorState_RBV', 0)
        self.updatePVs()
        self.tid = None

    def openFile(self):
        path = self.getParam('FilePath')
        name = self.getParam('FileName')
        number = self.getParam('FileNumber')
        template = self.getParam('FileTemplate')
        increment = self.getParam('AutoIncrement')
        fullFileName = os.path.join(path, template % (name, number))

        self.setParam('FullFileName_RBV', fullFileName)

        f = h5py.File(fullFileName, 'w')
        f.create_dataset('/entry/instrument/detector/data', data=self.images)
        f.create_dataset('/entry/instrument/NDAttributes/AcquireTime', data=self.getParam('AcquireTime'))
        f.create_dataset('/entry/instrument/NDAttributes/NumExposures', data=self.getParam('NumExposuresCounter_RBV'))

        if increment:
            self.setParam('FileNumber', number+1)

    def saveFile(self):
        fullFileName = self.getParam('FullFileName_RBV')
        f = h5py.File(fullFileName, 'r+')
        f['/entry/instrument/NDAttributes/NumExposures'].write_direct(numpy.array(self.getParam('NumExposuresCounter_RBV')))
        f['/entry/instrument/detector/data'].write_direct(self.images)
        f.close()


if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='Hamamatsu MCD Control')
    parser.add_argument('--prefix', default='iMott:',
                    help='EPICS PVs prefix')
    parser.add_argument('--gui', action='store_true', default=False,
                    help='start QtQuick GUI')
    args = parser.parse_args()

    server = SimpleServer()
    server.createPV(args.prefix, pvdb)
    driver = HamamatsuMCDriver()

    if args.gui:
        server_thread = ServerThread(server)
        server_thread.start()

        from PyQt5 import QtCore, QtGui, QtQuick
        app = QtGui.QGuiApplication(sys.argv)
        view = QtQuick.QQuickView()
        view.setResizeMode(QtQuick.QQuickView.SizeRootObjectToView)
        view.setSource(QtCore.QUrl.fromLocalFile('mcd.qml'))
        view.setTitle('Hamamatsu C7557-1 Control')
        view.show()

        app.lastWindowClosed.connect(server_thread.stop)
        app.exec_()
    else:
        while True:
            server.process(0.1)
