# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread
import sys, time
import simple_julabo_ui as jui
import labrad
import pyqtgraph as pg




cxn = labrad.connect()
ju = cxn.julabo_lc4
ju.select_device()

class JulaboApp(QtGui.QMainWindow, jui.Ui_Dialog):
    def __init__(self, parent=None):
        pg.setConfigOption('background', (255,255,255,0)) #before loading widget
        super(JulaboApp, self).__init__(parent)
        self.setupUi(self)

        self.SetTempButton.clicked.connect(self.set_temp)
        self.upArrow.clicked.connect(self.temp_up)
        self.downArrow.clicked.connect(self.temp_down)

        self.temp_thread = getTempsThread(ju)
        self.connect(self.temp_thread, QtCore.SIGNAL("temp_read(float)"),self.update_temp)
        self.connect(self.temp_thread, QtCore.SIGNAL("sp_read(float)"),self.update_sp)

        self.connect(self.temp_thread,QtCore.SIGNAL("plot_now"),self.update_plot)

        self.temp_thread.start()

        self.ts = MaxSizeList(1000)
        self.tsets = MaxSizeList(1000)

        self.times1 = MaxSizeList(1000)
        self.times2 = MaxSizeList(1000)
        self.t0 = time.time()

        self.pen1 = pg.mkPen(color='r', width = 3)
        self.pen2 = pg.mkPen(color='b', width = 3)

        self.tempPlot.setLabel('bottom','time','s')
        self.tempPlot.setLabel('left','T','°C')
        self.tempPlot.addLegend()

    def set_temp(self):
        t_update = float(self.setPointEdit.text())
        try:
            ju.set_temp(t_update)
        except:
            print('oops')

    def print_temps(self, v):
        print v

    def update_temp(self,t):
        self.t = t
        self.ts.append(t)
        self.currentTempBox.display(t)

        self.times1.append(time.time()-self.t0)

    def update_sp(self,tset):
        self.tset = tset
        self.tsets.append(tset)
        self.currentSetPointBox.display(self.tset)

        self.times2.append(time.time()-self.t0)

    def update_plot(self):
        self.tempPlot.plotItem.legend.items = []
        self.tempPlot.plot(self.times1.get(),self.ts.get(),clear = True,pen = self.pen1, name='Temperature')
        self.tempPlot.plot(self.times2.get(),self.tsets.get(),clear = False,pen = self.pen2, name='Setpoint')

    def temp_up(self):
        self.tset = self.tset + 1.0
        ju.set_temp(self.tset)
        self.currentSetPointBox.display(self.tset)

    def temp_down(self):
        self.tset = self.tset - 1.0
        ju.set_temp(self.tset)
        self.currentSetPointBox.display(self.tset)

#This thread runs constantly while the GUI is open, and attempts to read the t
#he temperature and set point every 5 seconds. Threading prevents hang ups in
#serial communication to freeze the GUI, which is nice.
class getTempsThread(QThread):
    def __init__(self, jul):
        QThread.__init__(self)
        self.ju = jul

    def __del__(self):
        self.wait()

    def _get_temps(self):
        gotten = False
        while not gotten:
            try:
                temp = float(self.ju.get_temp())
                tset = float(self.ju.get_setpoint())
                gotten = True
            except:
                gotten = False

        return temp, tset


    def run(self):
        self.running = True
        while self.running:
            temp,tset= self._get_temps()
            self.emit(QtCore.SIGNAL("temp_read(float)"),temp)
            self.emit(QtCore.SIGNAL("sp_read(float)"),tset)
            time.sleep(0.5)
            self.emit(QtCore.SIGNAL("plot_now"))
            time.sleep(2)

class MaxSizeList(object):

    def __init__(self, max_length):
        self.max_length = max_length
        self.ls = []

    def append(self, st):
        if len(self.ls) == self.max_length:
            self.ls.pop(0)
        self.ls.append(st)

    def get(self):
        return self.ls


def main():
    app = QtGui.QApplication(sys.argv)
    form = JulaboApp()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
