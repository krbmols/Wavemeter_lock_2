import dask.dataframe as dd
import pandas as pd
import sys
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        fig.tight_layout()

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        sc = MplCanvas(self)

        # Create our pandas DataFrame with some simple
        # data and headers.
        files = "C:\Bristol\\2021-12-*.csv"
        df = dd.read_csv(files, usecols=lambda x: ('Frequency' in x or 'Timestamp' in x), assume_missing=True)
        self.dfC = df.compute()
        #self.dfC = pd.concat([self.dfC], ignore_index=True)
        self.dfC['Timestamp'] = pd.to_datetime(self.dfC['Timestamp'], format='%Y-%m-%dT%H:%M:%S.%f')

        # plot the pandas DataFrame, passing in the
        # matplotlib Canvas axes.
        self.dfC.plot(x='Timestamp',ax=sc.axes,linestyle='None',marker='.',markersize=2)

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(sc, self)


        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(sc)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.showMaximized()



app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()