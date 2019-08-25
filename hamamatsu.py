import time
import numpy

class HamamatsuMCD(object):
    """
    Class to operate Hamamatsu MCD Controller.

    Note: This is a simulation class.
    """
    HSIZE = 532
    VSIZE = 520

    def __init__(self):
        self.exposure = 1.0
        self.binx = 1
        self.biny = 1
        self.phase = 0

    def get_exposure(self):
        """
        Get the exposure time in seconds.

        If not all CCDs have the same exposure time, an error will be logged.

        :return: exposure time setting in seconds
        """
        return self.exposure

    def set_exposure(self, exposure):
        """
        Set the exposure time in seconds.

        :param float exposure: exposure time in seconds
        """
        self.exposure = exposure

    def get_bin(self):
        """
        Get the binning size.

        If not all CCDs have the same binning size, an error will be logged.

        :return: binning size in x/y direction (binx, biny)
        :rtype: tuple
        """
        return self.binx, self.biny

    def set_bin(self, binx, biny):
        """
        Set the binning size.

        :param binx: x binning size 
        :param biny: y binning size
        """
        self.binx, self.biny = binx, biny

    def acquire(self, cycles=1):
        """
        For each CCD, acquire number of cycles images and sum them up.

        :param cycles:  number of cycles
        :return: sensor images
        """
        time.sleep(self.exposure)

        sizex = self.HSIZE // self.binx
        sizey = self.VSIZE // self.biny

        centerx = sizex // 2
        centery = sizey // 2

        self.phase += 0.1

        xx, yy = numpy.meshgrid(range(sizex), range(sizey))

        images = 120 * (numpy.sin((xx-centerx)**2 + (yy-centery)**2 + self.phase) + 1)

        return images.astype(numpy.uint8)

if __name__ == '__main__':
    import pylab
    mcd = HamamatsuMCD()
    image = mcd.acquire()
    pylab.imshow(image)
    pylab.show()
