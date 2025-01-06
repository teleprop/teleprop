# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic,QtGui
from qgis.PyQt.QtGui import QPen
from qgis.PyQt.QtCore import QVariant,Qt,QAbstractTableModel,QTranslator,QCoreApplication
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QAction,QMessageBox,QComboBox,QFileDialog,QInputDialog
from qgis.gui import QgsMapToolIdentifyFeature,QgsMapToolIdentify,QgsMapToolEmitPoint,QgsMapTool
from qgis.core import (
    Qgis,QgsApplication,
    QgsProject,QgsTask,QgsFeatureRequest,
    QgsVectorLayer,QgsRasterLayer,QgsMapLayer,
    QgsFeature,
    QgsGeometry,QgsReferencedGeometry,QgsCoordinateReferenceSystem,QgsCoordinateTransform,
    QgsVectorDataProvider,QgsField,
    QgsSymbol,QgsLineSymbol,QgsMarkerSymbol,QgsRendererRange,QgsGraduatedSymbolRenderer,
    QgsVectorLayerSimpleLabeling,QgsPalLayerSettings,QgsTextFormat,QgsTextBufferSettings,
    QgsPoint,QgsDistanceArea,QgsPointXY,QgsRegularPolygon,
    QgsMessageLog)
from qgis import processing
from .dataReaderTool import DataReaderTool

import numpy as np
import matplotlib.pyplot as plt
import csv
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'dialog_antenna.ui'))

class Dialog_Antenna(QtWidgets.QDialog,FORM_CLASS):
    def __init__(self,iface,Setup,Antenna,parent=None):
        """Constructor."""
        self.iface=iface
        self.parent=parent
        self.Setup=Setup
        self.Antenna=Antenna
        super(Dialog_Antenna,self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.canvas=self.iface.mapCanvas()
        self.cav=FigureCanvas(Figure(figsize=(5,3)))
        # Ideally one would use self.addToolBar here, but it is slightly
        # incompatible between PyQt6 and other bindings, so we just add the
        # toolbar as a plain widget instead.
        self._main=self.QWidget_Graph#QtWidgets.QWidget()
        layout=QtWidgets.QVBoxLayout(self._main)
        layout.addWidget(NavigationToolbar(self.cav,self))
        layout.addWidget(self.cav)
        self._ax=self.cav.figure.subplots(subplot_kw={"projection":"polar"})
        self._ax.set_theta_direction(-1)
        self._ax.set_theta_zero_location("N")
        self._ax.set_rlabel_position(0)
        self._ax.tick_params(labelsize=6)
        self._ax.grid(True)
        ir1=np.arange(0,360,1)
        ir1=np.append(ir1,ir1[0])
        idB=np.zeros(361)
        self._kar,=self._ax.plot(np.radians(ir1),idB)
        #ax.set_title("H",va='bottom')
        self.cav.toolbar.setVisible(False)
        #plt.show()
        self.QLineEdit_Filename.setText(self.Setup.value("Antenna/Filename"))
        self.maxir=self.Setup.value("Antenna/Max.irany")
        if self.maxir==None: self.maxir=0
        self.QLineEdit_Irany.setText(str(self.maxir))
        self._Diagram()
        self.QPushButton_Browse.clicked.connect(self.QPushButton_Browse_clicked)
        self.QLineEdit_Irany.textChanged.connect(self.QLineEdit_Irany_textChanged)
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Dialog_Antenna',message)
    def _Diagram(self):
        try:
            ir=self.Antenna[:,0]
            dB=self.Antenna[:,1]
            ir1=np.arange(0,360,1)
            ir1=np.append(ir1,ir1[0])
            idB=np.interp(ir1,ir,dB,period=360)
            self._kar.set_data(np.radians(ir1),idB)
            #ax.set_rmax(2)
            self._ax.set_theta_offset(np.radians(90-float(self.maxir)))
            self._ax.set_rticks(np.append(np.arange(dB.min(),dB.max(),10),[-3]))
            self._ax.set_xticks(np.radians(np.arange(0,360,10)))
            self._kar.figure.canvas.draw_idle()
        except:
            pass
    def QPushButton_Browse_clicked(self):
        fid=QFileDialog(self)
        fid.setWindowTitle(self.tr("Antenna iránykarakterisztika fájl kijelölése"))
        fid.setAcceptMode(QFileDialog.AcceptOpen)
        fid.setFileMode(QFileDialog.ExistingFile)
        fid.setViewMode(QFileDialog.Detail)
        fid.setNameFilter("Tab separeted file (*.csv)")
        if fid.exec():
            fin=fid.selectedFiles()[0]
            self.Setup.setValue("Antenna/Filename",fin)
            self.QLineEdit_Filename.setText(fin)
            self.loadAntenna()
            self._Diagram()
    def loadAntenna(self):
        antennaCSV=""
        i=self.Setup.value("Antenna/Dir")
        if i==1:
            antennaCSV=self.Setup.value("Antenna/Filename")
            if antennaCSV!=None:
                self.Antenna=np.empty((0,2))
                if os.path.isfile(antennaCSV):
                    with open(antennaCSV,encoding="cp1250",newline='') as csvfile:
                        reader=csv.reader(csvfile,dialect='excel-tab')
                        next(reader)
                        for row in reader:
                            self.Antenna=np.append(self.Antenna,[[float(row[0]),float(row[1])]],axis=0)
        else:
            self.Antenna=np.hstack((np.arange(0,360,10).reshape(36,1),np.zeros(36).reshape(36,1)))
            self.maxir=0
            self.Gain=0
        return antennaCSV
    def QLineEdit_Irany_textChanged(self):
        try:
            v=float(self.QLineEdit_Irany.text())
            self.QLineEdit_Irany.setStyleSheet("")
            self.QLineEdit_Irany.setToolTip("")
            self.maxir=v
            self._Diagram()
            self.Setup.setValue("Antenna/Max.irany",self.maxir)
        except:
            self.QLineEdit_Irany.setStyleSheet("border:2px solid rgba(255, 0, 0)")
            self.QLineEdit_Irany.setToolTip(self.tr("Az irány nem szám."))