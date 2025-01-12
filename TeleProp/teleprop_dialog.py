# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TelePropDialog
                                 A QGIS plugin
 TelePropDialog
                             -------------------
        begin                : 2023-04-12
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Lakatos Tamás
        email                : krbg.index@igmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os

from qgis.PyQt import uic,QtGui
from qgis.PyQt.QtGui import QPen
from qgis.PyQt.QtCore import QVariant,Qt
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QAction,QMessageBox,QComboBox,QFileDialog,QInputDialog
from qgis.gui import QgsMapToolExtent
from qgis.core import (
    Qgis,QgsApplication,
    QgsProject,QgsTask,QgsFeatureRequest,
    QgsVectorLayer,QgsRasterLayer,QgsMapLayer,
    QgsFeature,
    QgsGeometry,QgsReferencedGeometry,QgsCoordinateReferenceSystem,QgsCoordinateTransform,
    QgsVectorDataProvider,QgsField,
    QgsSymbol,QgsFillSymbol,QgsLineSymbol,QgsMarkerSymbol,QgsRendererRange,QgsGraduatedSymbolRenderer,QgsStyle,
    QgsVectorLayerSimpleLabeling,QgsPalLayerSettings,QgsTextFormat,QgsTextBufferSettings,
    QgsPoint,QgsDistanceArea,QgsPointXY,QgsRegularPolygon,QgsRectangle,
    QgsMessageLog,QgsWkbTypes)
from qgis import processing
from .dataReaderTool import DataReaderTool
from .TeleDeLuxe.Propagation import Propagation
from .TeleDeLuxe.Terrain import Terrain
from .TeleDeLuxe.GeoCoord import WorldPoint
import math
import numpy as np
import csv
from .dialog_link import Dialog_Link
from .dialog_antenna import Dialog_Antenna
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'teleprop_dialog_base.ui'))

class TelePropDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self,iface,Setup,parent=None):
        """Constructor."""
        self.iface = iface
        self.Setup=Setup
        self.parent=parent
        super(TelePropDialog,self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.canvas=self.iface.mapCanvas()
        self.toolSelection=QgsMapToolExtent(self.canvas)
        self.toolSelection.extentChanged.connect(self._Selection)
        self.Layer_Ado=None
        self.Layer_Pontok=None
        self.Layer_Hatarvonal=None
        self.Layer_Terulet=None
        self.Antenna=np.empty((0,2))
        self.ral=None
        self.ral=Propagation.RadioLink()
        #self.QPushButton_SelectAdo.clicked.connect(self.QPushButton_SelectAdo_clicked)
        self.QPushButton_AdoLink_Telephely.clicked.connect(self.QPushButton_AdoLink_Telephely_clicked)
        self.QPushButton_AdoLink_Musor.clicked.connect(self.QPushButton_AdoLink_Musor_clicked)
        self.QPushButton_AdoLink_Frekvencia.clicked.connect(self.QPushButton_AdoLink_Frekvencia_clicked)
        self.QPushButton_AdoLink_ERP.clicked.connect(self.QPushButton_AdoLink_ERP_clicked)
        self.QPushButton_AdoLink_h1.clicked.connect(self.QPushButton_AdoLink_h1_clicked)
        self.QPushButton_AdoLink_Polarizacio.clicked.connect(self.QPushButton_AdoLink_Polarizacio_clicked)
        self.QPushButton_Ertekek.clicked.connect(self.QPushButton_Ertekek_clicked)
        self.QComboBox_Layer_Pontok.currentIndexChanged.connect(self.QComboBox_Layer_Pontok_currentIndexChanged)
        self.QComboBox_Layer_Hatarvonal.currentIndexChanged.connect(self.QComboBox_Layer_Hatarvonal_currentIndexChanged)
        self.QComboBox_Layer_Terulet.currentIndexChanged.connect(self.QComboBox_Layer_Terulet_currentIndexChanged)
        self.QComboBox_Modell.currentIndexChanged.connect(self.QComboBox_Modell_currentIndexChanged)
        self.QComboBox_Antenna.currentIndexChanged.connect(self.QComboBox_Antenna_currentIndexChanged)
        self.QPushButton_Antenna.clicked.connect(self.QPushButton_Antenna_clicked)
        self.QPushButton_TorolHatar.clicked.connect(self.QPushButton_TorolHatar_clicked)
        self.QPushButton_UjHatar.clicked.connect(self.QPushButton_UjHatar_clicked)
        self.QPushButton_UjPontok.clicked.connect(self.QPushButton_UjPontok_clicked)
        self.QPushButton_Beillesztes.clicked.connect(self.QPushButton_Beillesztes_clicked)
        self.QPushButton_Pontok.clicked.connect(self.QPushButton_Pontok_clicked)
        self.QPushButton_Hatarvonal.clicked.connect(self.QPushButton_Hatarvonal_clicked)
        self.QPushButton_Terulet_Kijelol.clicked.connect(self.QPushButton_Terulet_Kijelol_clicked)
        self.QPushButton_Terulet.clicked.connect(self.QPushButton_Terulet_clicked)
        self.QPushButton_Elorejelzes.clicked.connect(self.QPushButton_Elorejelzes_clicked)
        self.QTabWidget_Szamitas.currentChanged.connect(self.QTabWidget_Szamitas_currentChanged)
        self.QLineEdit_MHz.textChanged.connect(self.QLineEdit_MHz_textChanged)
        self.QLineEdit_kW.textChanged.connect(self.QLineEdit_kW_textChanged)
        self.QLineEdit_h1.textChanged.connect(self.QLineEdit_h1_textChanged)
        self.QLineEdit_h2.textChanged.connect(self.QLineEdit_h2_textChanged)
        self.QLineEdit_GridSize.textChanged.connect(self.QLineEdit_GridSize_textChanged)
        self.QComboBox_Layer_Ado.clear()
        self.QComboBox_Layer_Terulet.clear()
        self.QComboBox_Layer_Terulet.addItem("")
        self.QComboBox_Layer_Pontok.clear()
        self.QComboBox_Layer_Pontok.addItem("")
        self.QComboBox_Layer_Hatarvonal.clear()
        self.QComboBox_Layer_Hatarvonal.addItem("")
        self.QComboBox_DEM.clear()
        self.QComboBox_FED.clear()
        self.QComboBox_FED.addItem("-")
        self.QLabel_ModellNemOk.hide()
        self.QGroupBox_p.hide()
        self.progressBar_Elorejelzes.hide()
        crswgs=QgsCoordinateReferenceSystem("EPSG:4326") #WGS 84
        self.crspred=QgsCoordinateReferenceSystem("EPSG:23700")#EOV
        transformContext=QgsProject.instance().transformContext()
        self.wgstoeov=QgsCoordinateTransform(crswgs,self.crspred,transformContext)
        #self.QgsMapLayerComboBox_DEM.setProject(QgsProject.instance())
        for l in QgsProject.instance().mapLayers().values():
            if (l.type()==QgsMapLayer.LayerType.Vector):
                self.QComboBox_Layer_Ado.addItem(l.name())
            if l.name()[0:6]=="Pred.P":
                self.QComboBox_Layer_Pontok.addItem(l.name())
            if l.name()[0:6]=="Pred.L":
                self.QComboBox_Layer_Hatarvonal.addItem(l.name())
            if l.name()[0:6]=="Pred.A":
                self.QComboBox_Layer_Terulet.addItem(l.name())
            if (l.type()==QgsMapLayer.LayerType.Raster):
                if l.elevationProperties().hasElevation(): self.QComboBox_DEM.addItem(l.name())
                else: self.QComboBox_FED.addItem(l.name())
        self.QComboBox_FED.currentIndexChanged.connect(self.QComboBox_FED_currentIndexChanged)
        if self.QComboBox_FED.count()>0:
            s=self.Setup.value("FED")
            i=0
            if s!=None:
                i=self.QComboBox_FED.findText(s)
                if i==-1: i=0
            self.QComboBox_FED.setCurrentIndex(i)
        self.QComboBox_DEM.setCurrentIndex(-1)
        self.QComboBox_DEM.currentIndexChanged.connect(self.QComboBox_DEM_currentIndexChanged)
        s=self.Setup.value("DEM")
        i=0
        if s!=None: i=self.QComboBox_DEM.findText(s)
        if (self.QComboBox_DEM.count()>0) and (i>-1): self.QComboBox_DEM.setCurrentIndex(i)
        self.QComboBox_pl.setCurrentIndex(2)
        self.QComboBox_Layer_Ado.currentIndexChanged.connect(self.QComboBox_Layer_Ado_currentIndexChanged)
        if self.QComboBox_Layer_Ado.count()>0:
            i=0
            ala=self.Setup.value("SelectedAdo/AdoLayer")
            if ala!="":
                i=self.QComboBox_Layer_Ado.findText(ala)
                if i<0: i=0
            self.QComboBox_Layer_Ado.setCurrentIndex(i)
            self.QComboBox_Layer_Ado_currentIndexChanged()
        #self.QComboBox_Beepitettseg.setCurrentIndex(1)
        self.QComboBox_Layer_Pontok.setCurrentIndex(self.QComboBox_Layer_Pontok.count()-1)
        self.QComboBox_Layer_Hatarvonal.setCurrentIndex(self.QComboBox_Layer_Hatarvonal.count()-1)
        self.QComboBox_Layer_Terulet.setCurrentIndex(self.QComboBox_Layer_Terulet.count()-1)
        self.QPushButton_Hatarvonal.setEnabled(bool(self.QComboBox_Hatarvonal.count()>0))
        self.QPushButton_TorolHatar.setEnabled(bool(self.QComboBox_Hatarvonal.count()>0))
        i=self.Setup.value("Antenna/Dir")
        if i==None: i="0"
        self.QComboBox_Antenna.setCurrentIndex(int(i))
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TelePropDialog',message)
    def QPushButton_Antenna_clicked(self,item):
        da=Dialog_Antenna(self.iface,self.Setup,self.Antenna)
        da.setWindowModality(Qt.ApplicationModal)
        result=da.exec_()
        if result:
            self.ral.AntennaMaxIr=float(self.Setup.value("Antenna/Max.irany"))
            self.QComboBox_Antenna.setToolTip("{0}°".format(self.ral.AntennaMaxIr))
            self.QPushButton_Antenna.setToolTip(Dialog_Antenna.loadAntenna(self))
    def QComboBox_Antenna_currentIndexChanged(self):
        self.Setup.setValue("Antenna/Dir",self.QComboBox_Antenna.currentIndex())
        self.QPushButton_Antenna.setEnabled(self.QComboBox_Antenna.currentIndex()>0)
        #if self.QComboBox_Antenna.currentIndex()>0: 
        self.QPushButton_Antenna.setToolTip(Dialog_Antenna.loadAntenna(self))
        try:
            self.ral.AntennaMaxIr=float(self.Setup.value("Antenna/Max.irany"))
        except:
            self.ral.AntennaMaxIr=0
        self.QComboBox_Antenna.setToolTip("{0}°".format(self.ral.AntennaMaxIr))
    def createLink(self,item):
        dl=Dialog_Link(self.iface,self.Layer_Ado)
        dl.setWindowModality(Qt.ApplicationModal)
        result=dl.exec_()
        if result:
            if dl.LinkItem!=None:
                self.Setup.setValue(self.QComboBox_Layer_Ado.currentText()+"/Link/"+item,dl.LinkItem)
                self.refreshRadioLink()
    def QPushButton_AdoLink_Telephely_clicked(self):
        self.createLink("Telephely")
    def QPushButton_AdoLink_Musor_clicked(self):
        self.createLink("Musor")
    def QPushButton_AdoLink_Frekvencia_clicked(self):
        self.createLink("Frekvencia")
    def QPushButton_AdoLink_ERP_clicked(self):
        self.createLink("ERP")
    def QPushButton_AdoLink_h1_clicked(self):
        self.createLink("h1")
    def QPushButton_AdoLink_Polarizacio_clicked(self):
        self.createLink("Polarizacio")
    def QLineEdit_MHz_textChanged(self):
        try:
            v=float(self.QLineEdit_MHz.text())
            self.QLineEdit_MHz.setStyleSheet("")
            self.QLineEdit_MHz.setToolTip("")
            self.refreshRadioLink()
        except:
            #QMessageBox.critical(None,"Hiba","A beírt szöveg nem szám!")
            self.QLineEdit_MHz.setStyleSheet("border:2px solid rgba(255, 0, 0)")
            self.QLineEdit_MHz.setToolTip(self.tr("A frekvencia nem szám."))
            self.QTabWidget_Szamitas.hide()
    def QLineEdit_kW_textChanged(self):
        try:
            v=float(self.QLineEdit_kW.text())
            self.QLineEdit_kW.setStyleSheet("")
            self.QLineEdit_kW.setToolTip("")
            self.refreshRadioLink()
        except:
            #QMessageBox.critical(None,"Hiba","A beírt szöveg nem szám!")
            self.QLineEdit_kW.setStyleSheet("border:2px solid rgba(255, 0, 0)")
            self.QLineEdit_kW.setToolTip(self.tr("Az ERP nem szám."))
            self.QTabWidget_Szamitas.hide()
    def QLineEdit_h1_textChanged(self):
        try:
            v=float(self.QLineEdit_h1.text())
            self.QLineEdit_h1.setStyleSheet("")
            self.QLineEdit_h1.setToolTip("")
            self.refreshRadioLink()
        except:
            #QMessageBox.critical(None,"Hiba","A beírt szöveg nem szám!")
            self.QLineEdit_h1.setStyleSheet("border:2px solid rgba(255, 0, 0)")
            self.QLineEdit_h1.setToolTip(self.tr("Az adóantenna magassága nem szám."))
            self.QTabWidget_Szamitas.hide()
    def QLineEdit_h2_textChanged(self):
        try:
            v=float(self.QLineEdit_h2.text())
            self.QLineEdit_h2.setStyleSheet("")
            self.QLineEdit_h2.setToolTip("")
            self.refreshRadioLink()
        except:
            #QMessageBox.critical(None,"Hiba","A beírt szöveg nem szám!")
            self.QLineEdit_h2.setStyleSheet("border:2px solid rgba(255, 0, 0)")
            self.QLineEdit_h2.setToolTip(self.tr("A vevőantenna magassága nem szám."))
            self.QTabWidget_Szamitas.hide()
    def refreshRadioLink(self):
        if self.Layer_Ado!=None:
            if self.Layer_Ado.selectedFeatureCount()==1:
                ado=self.Layer_Ado.selectedFeatures()[0]
                litel=self.Setup.value(self.QComboBox_Layer_Ado.currentText()+"/Link/Telephely")
                limus=self.Setup.value(self.QComboBox_Layer_Ado.currentText()+"/Link/Musor")
                lifre=self.Setup.value(self.QComboBox_Layer_Ado.currentText()+"/Link/Frekvencia")
                lierp=self.Setup.value(self.QComboBox_Layer_Ado.currentText()+"/Link/ERP")
                lih1=self.Setup.value(self.QComboBox_Layer_Ado.currentText()+"/Link/h1")
                lipol=self.Setup.value(self.QComboBox_Layer_Ado.currentText()+"/Link/Polarizacio")
                if litel!="":
                    if litel in ado.fields().names():
                        self.QLineEdit_Telephely.setText(ado[litel])
                        self.QPushButton_AdoLink_Telephely.setStyleSheet("")
                else: self.QPushButton_AdoLink_Telephely.setStyleSheet("color:rgb(255, 0, 0)")
                if limus!="" and limus in ado.fields().names():
                    self.QLineEdit_Musor.setText(str(ado[limus]))
                    self.QPushButton_AdoLink_Musor.setStyleSheet("")
                else: self.QPushButton_AdoLink_Musor.setStyleSheet("color:rgb(255, 0, 0)")
                if lifre!="":
                    if lifre in ado.fields().names():
                        self.QLineEdit_MHz.setText(str(ado[lifre]))
                        self.QPushButton_AdoLink_Frekvencia.setStyleSheet("")
                else: self.QPushButton_AdoLink_Frekvencia.setStyleSheet("color:rgb(255, 0, 0)")
                if lierp!="":
                    if lierp in ado.fields().names():
                        self.QLineEdit_kW.setText(str(ado[lierp]))
                        self.QPushButton_AdoLink_ERP.setStyleSheet("")
                else: self.QPushButton_AdoLink_ERP.setStyleSheet("color:rgb(255, 0, 0)")
                if lih1!="":
                    if lih1 in ado.fields().names():
                        self.QLineEdit_h1.setText(str(ado[lih1]))
                        self.QPushButton_AdoLink_h1.setStyleSheet("")
                else: self.QPushButton_AdoLink_h1.setStyleSheet("color:rgb(255, 0, 0)")
                if lipol!="":
                    if lipol in ado.fields().names():
                        self.QComboBox_Pol.setCurrentIndex(self.QComboBox_Pol.findText(ado[lipol]))
                        self.QPushButton_AdoLink_Polarizacio.setStyleSheet("")
                else: self.QPushButton_AdoLink_Polarizacio.setStyleSheet("color:rgb(255, 0, 0)")
                self.QTabWidget_Szamitas.show()
                if lifre!="" and lifre!="" and lierp!="" and lih1!="" and lipol!="":
                    adopont=QgsPointXY(self.wgstoeov.transform(ado.geometry().asPoint()))
                try:
                    self.ral.f=float(self.QLineEdit_MHz.text())
                    self.QLineEdit_MHz.setToolTip("")
                except:
                    self.QLineEdit_MHz.setStyleSheet("border:2px solid rgba(255, 0, 0)")
                    self.QLineEdit_MHz.setToolTip(self.tr("A frekvencia nem szám."))
                    self.QTabWidget_Szamitas.hide()
                try:
                    self.ral.set_ERPkW(float(self.QLineEdit_kW.text()))
                    self.QLineEdit_kW.setToolTip("")
                except:
                    self.QLineEdit_kW.setStyleSheet("border:2px solid rgba(255, 0, 0)")
                    self.QLineEdit_kW.setToolTip(self.tr("Az ERP nem szám."))
                    self.QTabWidget_Szamitas.hide()
                try:
                    self.ral.Transmitter=WorldPoint(EOV=[adopont.x(),adopont.y(),0],m=float(self.QLineEdit_h1.text()))
                    self.QLineEdit_h1.setToolTip("")
                except:
                    self.QLineEdit_h1.setStyleSheet("border:2px solid rgba(255, 0, 0)")
                    self.QLineEdit_h1.setToolTip(self.tr("Az adóantenna magassága nem szám."))
                    self.QTabWidget_Szamitas.hide()
                try:
                    self.ral.Receiver=WorldPoint(EOV=[adopont.x()+100,adopont.y(),0],m=float(self.QLineEdit_h2.text()))
                    self.QLineEdit_h2.setToolTip("")
                except:
                    self.QLineEdit_h2.setStyleSheet("border:2px solid rgba(255, 0, 0)")
                    self.QLineEdit_h2.setToolTip(self.tr("A vevőantenna magassága nem szám."))
                    self.QTabWidget_Szamitas.hide()
                #self.QPushButton_Elorejelzes.setEnabled(self.ral.Terep.DEMlayer!=None)
                self.ral.Antenna=None
            else:
                QMessageBox.critical(self.iface.mainWindow(),self.tr("Hiba"),self.tr("Válassz 1 adóállomást a ")+self.Layer_Ado.name()+self.tr(" layer-on!"))
    def QComboBox_Layer_Ado_currentIndexChanged(self):
        if self.QComboBox_Layer_Ado.currentText()!="":
            self.Layer_Ado=QgsProject.instance().mapLayersByName(self.QComboBox_Layer_Ado.currentText())[0]
            self.Setup.setValue("SelectedAdo/AdoLayer",self.QComboBox_Layer_Ado.currentText())
            self.refreshRadioLink()
    def QComboBox_Layer_Pontok_currentIndexChanged(self):
        if self.QComboBox_Layer_Pontok.currentText()!="":
            self.Layer_Pontok=QgsProject.instance().mapLayersByName(self.QComboBox_Layer_Pontok.currentText())[0]
            self.QLabel_PontokSzama.setText("{0:.0f}".format(self.Layer_Pontok.featureCount()))
            self.QPushButton_Pontok.setEnabled(self.Layer_Pontok.featureCount()>0)
            self.QPushButton_UjPontok.setEnabled(self.Layer_Pontok.featureCount()==0)
            self.QPushButton_Beillesztes.setEnabled(self.Layer_Pontok.featureCount()==0)
            if self.Layer_Pontok.featureCount()==0: QMessageBox.critical(self.iface.mainWindow(),"Hiba",self.Layer_Pontok.name()+" layer-en nincsenek pontok!")
            self._Elorejelzes_setEnabled()
    def QComboBox_Layer_Hatarvonal_currentIndexChanged(self):
        if self.QComboBox_Layer_Hatarvonal.currentText()!="":
            self.Layer_Hatarvonal=QgsProject.instance().mapLayersByName(self.QComboBox_Layer_Hatarvonal.currentText())[0]
            self.QComboBox_Hatarvonal.clear()
            for fea in self.Layer_Hatarvonal.getFeatures():
                self.QComboBox_Hatarvonal.addItem(str(fea[0]))
            self.QPushButton_TorolHatar.setEnabled(bool(self.QComboBox_Hatarvonal.count()>0))
    def QComboBox_Layer_Terulet_currentIndexChanged(self):
        if self.QComboBox_Layer_Terulet.currentText()!="":
            self.Layer_Terulet=QgsProject.instance().mapLayersByName(self.QComboBox_Layer_Terulet.currentText())[0]
            if self.Layer_Terulet.featureCount()>0:
                if self.Setup.value("Terulet/Alak")=="Kijelolt":
                    extent=self.Setup.value("Terulet/Extent").split(" : ")
                    mi=extent[0].split(",")
                    ma=extent[1].split(",")
                    self.QLineEdit_GridSize.setText("~{0:.0f}".format(max(float(ma[0])-float(mi[0]),float(ma[1])-float(mi[1]))/1000))
                elif self.Setup.value("Terulet/Alak")=="Negyzetes":
                    self.QLineEdit_GridSize.setText("{0:.0f}".format(self.Layer_Terulet.extent().width()/1000))
                self.QComboBox_Resolution.setCurrentText("{0:.0f}".format(math.sqrt(self.Layer_Terulet.extent().area()/self.Layer_Terulet.featureCount())))
                self._Elorejelzes_setEnabled()
            else: QMessageBox.critical(self.iface.mainWindow(),self.tr("Hiba"),self.tr("Terület layer-t be kell állítani!"))
    def QTabWidget_Szamitas_currentChanged(self):
        self._Elorejelzes_setEnabled()
    def _Elorejelzes_setEnabled(self):
        s=""
        en=False
        if self.QTabWidget_Szamitas.currentIndex()==0:
            s="Pontok"
            en=(self.QComboBox_Layer_Pontok.currentIndex()>0)
        elif self.QTabWidget_Szamitas.currentIndex()==1:
            s="Hatarvonal"
            en=(self.QComboBox_Layer_Hatarvonal.currentIndex()>0)
        elif self.QTabWidget_Szamitas.currentIndex()==2:
            s="Terulet"
            en=(self.QComboBox_Layer_Terulet.currentIndex()>0)
        pfn=self.Setup.value(s+"/Profiles")
        en=en and ((pfn!=None) or (self.QComboBox_FED.currentIndex()==0))
        if en:
            if pfn!=None: en=(pfn!=None) and os.path.isfile(os.path.join(os.path.dirname(self.Setup.fileName()),pfn))
            if self.QComboBox_FED.currentIndex()>0:
                pfn=self.Setup.value(s+"/Fedettsegek")
                if pfn!=None: en=en and os.path.isfile(os.path.join(os.path.dirname(self.Setup.fileName()),pfn))
        self.QGroupBox_Modell.setEnabled(en)
        self.QPushButton_Elorejelzes.setEnabled(en)
    def QComboBox_DEM_currentIndexChanged(self):
        self.ral.Terep.set_DEMlayer(QgsProject.instance().mapLayersByName(self.QComboBox_DEM.currentText())[0])
        self.Setup.setValue("DEM",self.QComboBox_DEM.currentText())
        self.refreshRadioLink()
        #print(self.DEMmagassag(QgsPointXY(823814,311094)))
    def QComboBox_FED_currentIndexChanged(self):
        self.Setup.setValue("FED",self.QComboBox_FED.currentText())
        if self.QComboBox_FED.currentIndex()>0:
            self.QComboBox_Beepitettseg.hide()
            self.ral.Terep.set_FEDlayer(QgsProject.instance().mapLayersByName(self.QComboBox_FED.currentText())[0])
            self.ral.Terep.FEDvalues=[]
            s=self.Setup.value("FEDertekek")
            if s!=None:
                self._FEDertekek(s)
            else:
                self.QPushButton_Ertekek.setToolTip(self.tr("FED érték fájl nincs"))
                self.QPushButton_Ertekek.setStyleSheet("border:2px solid rgba(255, 0, 0)")
        else:
            self.ral.Terep.set_FEDlayer(None)
            self.QComboBox_Beepitettseg.show()
        self.QPushButton_Ertekek.setEnabled(self.QComboBox_FED.currentIndex()>0)
        self.refreshRadioLink()
    def _FEDertekek(self,ertekekCSV):
        if os.path.isfile(ertekekCSV):
            self.QPushButton_Ertekek.setToolTip(ertekekCSV)
            with open(ertekekCSV,encoding="cp1250",newline='') as csvfile:
                reader=csv.reader(csvfile,dialect='excel-tab')
                next(reader)
                for row in reader:
                    self.ral.Terep.FEDvalues.append([int(row[0]),int(row[1]),row[2]])
            #print(self.ral.Terep.FEDlayer.renderer().nColors())
            #print(len(self.ral.Terep.FEDvalues))
            self.QPushButton_Ertekek.setStyleSheet("")
    def QPushButton_Ertekek_clicked(self):
        fid=QFileDialog(self)
        fid.setWindowTitle("Érték fájl kijelölése")
        fid.setAcceptMode(QFileDialog.AcceptOpen)
        fid.setFileMode(QFileDialog.ExistingFile)
        fid.setViewMode(QFileDialog.Detail)
        fid.setNameFilter("Tab separeted file (*.csv)")
        if fid.exec():
            self.Setup.setValue("FEDertekek",fid.selectedFiles()[0])
            self._FEDertekek(fid.selectedFiles()[0])
    def _Colorlimits(self,layer):
        caps=layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.AddAttributes:
            res=layer.dataProvider().addAttributes([QgsField("E",QVariant.Double)])
            layer.updateFields()
            #col=[QtGui.QColor(0,0,255),QtGui.QColor(0,128,255),QtGui.QColor(0,255,255),
            #QtGui.QColor(0,255,128),QtGui.QColor(0,255,0),QtGui.QColor(128,255,0),
            #QtGui.QColor(255,255,0),QtGui.QColor(255,128,0),QtGui.QColor(255,0,0),
            #QtGui.QColor(255,0,128),QtGui.QColor(255,0,255)]
            ran=[]
            for i in range(110):
                sim=QgsSymbol.defaultSymbol(layer.geometryType())
                if type(sim)==QgsMarkerSymbol: sim.setSize(5)
                #sim.setColor(col[i])
                #sim.setOpacity(1)
                if type(sim)==QgsLineSymbol:
                    sim.symbolLayer(0).setWidth(1)
                else:
                    sim.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))
                    layer.setDisplayExpression("E")
                ran.append(QgsRendererRange(i*1.0,(i+1)*1.0,sim,"{0} - {1}".format(i*1.0,(i+1)*1.0)))
            ren=QgsGraduatedSymbolRenderer("",ran)
            sty=QgsStyle().defaultStyle()
            ramp=sty.colorRamp("Turbo")
            ren.setClassificationMethod(QgsApplication.classificationMethodRegistry().method("EqualInterval"))
            ren.setClassAttribute("E")
            ren.updateColorRamp(ramp)
            layer.setRenderer(ren)
    def QComboBox_Modell_currentIndexChanged(self):
        if self.QComboBox_Modell.currentIndex()>4: self.QGroupBox_p.show()
        else: self.QGroupBox_p.hide()
        self.QLabel_ModellNemOk.hide()
        for fea in self._SzamitasLayer().getFeatures():
            vevopont=QgsPointXY(fea.geometry().centroid().asPoint())
            self.ral.Receiver=WorldPoint(EOV=[vevopont.x(),vevopont.y(),0],m=self.ral.Receiver.m)
            self.ral.OnWorldPoint_Change()
            if self.QComboBox_Modell.currentIndex()==0:
                modell=Propagation.Freespace(RadioLink=self.ral)
            elif self.QComboBox_Modell.currentIndex()==1:
                modell=Propagation.EmpiricalTwoRay(RadioLink=self.ral)
            elif self.QComboBox_Modell.currentIndex()==2:
                modell=Propagation.COSTHata(RadioLink=self.ral)
            elif self.QComboBox_Modell.currentIndex()==3:
                modell=Propagation.Hata(RadioLink=self.ral)
            elif self.QComboBox_Modell.currentIndex()==4:
                modell=Propagation.ExtendedHata(RadioLink=self.ral)
            elif self.QComboBox_Modell.currentIndex()==5:
                modell=Propagation.ITU1546(RadioLink=self.ral)
            elif self.QComboBox_Modell.currentIndex()==6:
                modell=Propagation.ITM(RadioLink=self.ral)
            b,s=modell.CheckModel()
            if not(b):
                self.QLabel_ModellNemOk.show()
                self.QLabel_ModellNemOk.setToolTip(s)
                break
    def QPushButton_TorolHatar_clicked(self):
        self.QComboBox_Hatarvonal.removeItem(self.QComboBox_Hatarvonal.currentIndex())
        self.QPushButton_TorolHatar.setEnabled(bool(self.QComboBox_Hatarvonal.count()>0))
        self.QPushButton_Hatarvonal.setEnabled(bool(self.QComboBox_Hatarvonal.count()>0))
    def QPushButton_UjHatar_clicked(self):
        text,ok=QInputDialog().getText(self,self.tr("Határvonal beállítás"),self.tr("Térerősség határérték [dBuV/m]:"))
        if ok and text:
            try:
                v=float(text)
                self.QComboBox_Hatarvonal.addItem(str(v))
                self.QPushButton_Hatarvonal.setEnabled(True)
                self.QPushButton_TorolHatar.setEnabled(True)
            except:
                QMessageBox.critical(None,self.tr("Hiba"),self.tr("A beírt szöveg nem szám!"))
    def QPushButton_UjPontok_clicked(self):
        text,ok=QInputDialog().getText(self,self.tr("Pontok beállítása"),self.tr("Létrehozott pontok száma:"))
        if ok and text:
            try:
                v=int(text)
                self.QLabel_PontokSzama.setText(str(v))
                self.QPushButton_Pontok.setEnabled(bool(v>0))
            except:
                QMessageBox.critical(None,self.tr("Hiba"),self.tr("A beírt szöveg nem szám!"))
            if v>0:
                nfs=[]
                for i in range(v):
                    fea=QgsFeature()
                    fea.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(self.ral.Transmitter.EOV.x()+(i+1)*1000,self.ral.Transmitter.EOV.y())))
                    fea.setAttributes([i,"{0}. pont".format(i+1)])
                    nfs.append(fea)
            self._PontGyar(nfs)
    def QPushButton_Beillesztes_clicked(self):
        nfs=[]
        l=QgsApplication.clipboard().text().split("\n")
        for i in range(1,len(l)):
            s=l[i].split("\t")
            if len(s)>=3:
                fea=QgsFeature()
                po=self.wgstoeov.transform(QgsPointXY(float(s[2]),float(s[3])))
                fea.setGeometry(QgsGeometry.fromPointXY(po))
                fea.setAttributes([s[0],s[1],s[2],s[3]])
                nfs.append(fea)
        self._PontGyar(nfs)
    def _PontGyar(self,nfs):
        if self.Layer_Pontok==None:
            vl=QgsVectorLayer( "Point","Pred.P {0}".format(self.QLineEdit_Telephely.text()),"memory",crs=self.crspred)
            self.Layer_Pontok=QgsProject.instance().addMapLayer(vl)
            self.QComboBox_Layer_Pontok.addItem(vl.name())
        pr=self.Layer_Pontok.dataProvider()
        pr.addAttributes([QgsField("Mp",QVariant.Int),QgsField("Cím",QVariant.String),QgsField("Lon",QVariant.Double),QgsField("Lat",QVariant.Double)])
        self.Layer_Pontok.updateFields()
        for fea in nfs:
            pr.addFeatures([fea])
        self.Layer_Pontok.updateExtents()
        self._Colorlimits(self.Layer_Pontok)
        lls=QgsPalLayerSettings()
        lls.fieldName="@id"
        lls.placement=Qgis.LabelPlacement.OverPoint
        lls.placementSettings().setAllowDegradedPlacement(True)
        lls.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapAtNoCost)
        tef=QgsTextFormat()
        bus=QgsTextBufferSettings()
        bus.setEnabled(True)
        bus.setSize(0.6)
        tef.setBuffer(bus)
        lls.setFormat(tef)
        lls.isExpression=True
        lls.enabled=True
        self.Layer_Pontok.setLabelsEnabled(True)
        self.Layer_Pontok.setLabeling(QgsVectorLayerSimpleLabeling(lls))
        self.QComboBox_Layer_Pontok.setCurrentIndex(self.QComboBox_Layer_Pontok.count()-1)
        self.QComboBox_Layer_Pontok_currentIndexChanged()
    def QPushButton_Pontok_clicked(self):
        if self.QPushButton_Pontok.isChecked():
            if self.Layer_Pontok.featureCount()>0:
                self.Layer_Pontok.startEditing()
                self.Layer_Pontok.beginEditCommand("Elorejelzes")
                for fea in self.Layer_Pontok.getFeatures():
                    if fea["Lon"]!=None and fea["Lat"]!=None:
                        geom=QgsGeometry.fromPointXY(QgsPointXY(self.wgstoeov.transform(QgsPointXY(fea["Lon"],fea["Lat"]))))
                        fea.setGeometry(geom)
                        self.Layer_Pontok.updateFeature(fea)
                self.Layer_Pontok.endEditCommand()
                self.Layer_Pontok.commitChanges()
                self.progressBar_Elorejelzes.setValue(0)
                self.ral.clearProfiles()
                self.ral.clearFedettsegek()
                self.progressBar_Elorejelzes.show()
                self.task=ProfileTask(self.iface,self.ral,self.Layer_Pontok)
                self.task.progressChanged.connect(self.progressBar_Elorejelzes.setValue)
                self.task.taskCompleted.connect(self._ProfileTask_Completed_Pontok)
                QgsApplication.taskManager().addTask(self.task)
        else:
            if self.task!=None: self.task.cancel()
    def _ProfileTask_Completed_Pontok(self):
        self._ProfileTask_Completed_Common(self.Layer_Pontok,"Pontok")
        self.QPushButton_Pontok.setChecked(False)
    def _ProfileTask_Completed_Hatarvonal(self):
        self._ProfileTask_Completed_Common(self.Layer_Hatarvonal,"Hatarvonal")
        self.QPushButton_Hatarvonal.setChecked(False)
        self.QComboBox_Layer_Hatarvonal.setCurrentIndex(self.QComboBox_Layer_Hatarvonal.count()-1)
    def _ProfileTask_Completed_Terulet(self):
        self._ProfileTask_Completed_Common(self.Layer_Terulet,"Terulet")
        self.QPushButton_Terulet.setChecked(False)
        self.QComboBox_Layer_Terulet.setCurrentIndex(self.QComboBox_Layer_Terulet.count()-1)
    def _ProfileTask_Completed_Common(self,Layer,item):
        self.iface.messageBar().clearWidgets
        pfn="Profile "+Layer.name()+".npy"
        self.ral.saveProfiles(os.path.join(os.path.dirname(self.Setup.fileName()),pfn))
        self.Setup.setValue(item+"/Profiles",pfn)
        pfn="Fedettseg "+Layer.name()+".npy"
        self.ral.saveFedettsegek(os.path.join(os.path.dirname(self.Setup.fileName()),pfn))
        self.Setup.setValue(item+"/Fedettsegek",pfn)
        self.QGroupBox_Modell.setEnabled(True)
        self.progressBar_Elorejelzes.hide()
    def QPushButton_Hatarvonal_clicked(self):
        if self.QPushButton_Hatarvonal.isChecked():
            if self.QComboBox_Layer_Hatarvonal.currentText()!="":
                root=QgsProject.instance().layerTreeRoot()
                root.removeLayer(self.Layer_Hatarvonal)
                self.Layer_Hatarvonal=None
            vl=QgsVectorLayer("LineString","Pred.L {0}".format(self.QLineEdit_Telephely.text()),"memory",crs=self.crspred)
            self.Layer_Hatarvonal=QgsProject.instance().addMapLayer(vl)
            self._Colorlimits(self.Layer_Hatarvonal)
            self.QComboBox_Layer_Hatarvonal.addItem(self.Layer_Hatarvonal.name())
            pr=vl.dataProvider()
            #pr.addAttributes([QgsField("E",QVariant.Double)])
            #vl.updateFields()
            for i in range(self.QComboBox_Hatarvonal.count()):
                fea=QgsFeature(self.Layer_Hatarvonal.fields())
                fea.setAttribute("E",float(self.QComboBox_Hatarvonal.itemText(i)))
                dmax=1000*10**((106.9+10*math.log10(self.ral.ERPkW)-fea["E"])/20)
                poly=QgsRegularPolygon(self.ral.Transmitter.EOV,dmax,0,36,0)
                pxy=[]
                for p in poly.points():
                    pxy.append(QgsPointXY(p.x(),p.y()))
                fea.setGeometry(QgsGeometry.fromPolyline(poly.toLineString()))
                pr.addFeatures([fea])
            vl.updateExtents()
            self.progressBar_Elorejelzes.setValue(0)
            self.ral.clearProfiles()
            self.ral.clearFedettsegek()
            self.progressBar_Elorejelzes.show()
            self.task=ProfileTask(self.iface,self.ral,self.Layer_Hatarvonal)
            self.task.progressChanged.connect(self.progressBar_Elorejelzes.setValue)
            self.task.taskCompleted.connect(self._ProfileTask_Completed_Hatarvonal)
            QgsApplication.taskManager().addTask(self.task)
        else:
            if self.task!=None: self.task.cancel()
    def QLineEdit_GridSize_textChanged(self):
        try:
            v=float(self.QLineEdit_GridSize.text())
            self.QLineEdit_GridSize.setToolTip(self.tr("Négyzetes terület az adó körül"))
            self.Setup.setValue("Terulet/Alak","Negyzetes")
        except:
            self.QLineEdit_GridSize.setToolTip(self.tr("Kijelölt terület"))
            self.Setup.setValue("Terulet/Alak","Kijelolt")
    def QPushButton_Terulet_Kijelol_clicked(self):
        QgsMessageLog.logMessage(message=self.tr("A terület kijelölése két sarokponttal"),level=Qgis.Warning,)
        self.hide()
        self.canvas.setMapTool(self.toolSelection)
    def _Selection(self,extent:QgsRectangle):
        self.show()
        self.toolSelection.clearRubberBand()
        self.canvas.unsetMapTool(self.toolSelection)
        self.QLineEdit_GridSize.setText("~{0:.0f}".format(max(extent.width()/1000,extent.height()/1000)))
        self.Setup.setValue("Terulet/Extent",extent.toString(0))
    def QPushButton_Terulet_clicked(self):
        if self.QPushButton_Terulet.isChecked():
            if self.QComboBox_Layer_Terulet.currentText()!="":
                root=QgsProject.instance().layerTreeRoot()
                root.removeLayer(self.Layer_Terulet)
                self.Layer_Terulet=None
            ado=self.Layer_Ado.selectedFeatures()[0]
            adopont=ado.geometry().asPoint()
            p=QgsReferencedGeometry(ado.geometry(),self.Layer_Ado.crs())
            wgstoeov=QgsCoordinateTransform(self.Layer_Ado.crs(),self.crspred,QgsProject.instance().transformContext())
            peov=wgstoeov.transform(adopont)
            if self.Setup.value("Terulet/Alak")=="Kijelolt":
                si=self.Setup.value("Terulet/Extent").replace('"',"").split(" : ")
                mi=si[0].split(",")
                ma=si[1].split(",")
                ext=mi[0]+","+ma[0]+","+mi[1]+","+ma[1]+" [EPSG:23700]"
            elif self.Setup.value("Terulet/Alak")=="Negyzetes":
                si=500*float(self.QLineEdit_GridSize.text())
                ext=str(peov.x()-si)+","+str(peov.x()+si)+","+str(peov.y()-si)+","+str(peov.y()+si)+" [EPSG:23700]"
            res=float(self.QComboBox_Resolution.currentText())
            grid=processing.run("native:creategrid", {'TYPE':2,'EXTENT':ext,'HSPACING':res,'VSPACING':res,'HOVERLAY':0,'VOVERLAY':0,'CRS':self.crspred,'OUTPUT':'TEMPORARY_OUTPUT'})
            self.Layer_Terulet=QgsProject.instance().addMapLayer(grid['OUTPUT'])
            self.Layer_Terulet.setName("Pred.A {0}".format(self.QLineEdit_Telephely.text()))
            if self.Layer_Terulet.dataProvider().capabilities() & QgsVectorDataProvider.DeleteAttributes:
                self.Layer_Terulet.dataProvider().deleteAttributes([1,2,3,4])
                self.Layer_Terulet.dataProvider().renameAttributes({0:"Mp"})
                self.Layer_Terulet.updateFields()
            self._Colorlimits(self.Layer_Terulet)
            if self.QComboBox_Layer_Terulet.findText(self.Layer_Terulet.name())==-1: self.QComboBox_Layer_Terulet.addItem(self.Layer_Terulet.name())
            self.progressBar_Elorejelzes.setValue(0)
            self.ral.clearProfiles()
            self.ral.clearFedettsegek()
            self.progressBar_Elorejelzes.show()
            self.task=ProfileTask(self.iface,self.ral,self.Layer_Terulet)
            self.task.progressChanged.connect(self.progressBar_Elorejelzes.setValue)
            self.task.taskCompleted.connect(self._ProfileTask_Completed_Terulet)
            QgsApplication.taskManager().addTask(self.task)
        else:
            if self.task!=None: self.task.cancel()
    def _SzamitasLayer(self):
        lay=None
        if self.QTabWidget_Szamitas.currentIndex()==0:
            lay=self.Layer_Pontok
        if self.QTabWidget_Szamitas.currentIndex()==1:
            lay=self.Layer_Hatarvonal
        if self.QTabWidget_Szamitas.currentIndex()==2:
            lay=self.Layer_Terulet
        return lay
    def QPushButton_Elorejelzes_clicked(self):
        if self.QPushButton_Elorejelzes.isChecked():
            a=["Pontok","Hatarvonal","Terulet"][self.QTabWidget_Szamitas.currentIndex()]
            self.ral.loadProfiles(os.path.join(os.path.dirname(self.Setup.fileName()),self.Setup.value(a+"/Profiles")))
            self.ral.GeneralEnvironment=self.QComboBox_Beepitettseg.currentIndex()+1
            if self.QComboBox_FED.currentIndex()>0: self.ral.loadFedettsegek(os.path.join(os.path.dirname(self.Setup.fileName()),self.Setup.value(a+"/Fedettsegek")))
            self.ral.pt=int(self.QComboBox_pt.currentText()[:-1])
            self.ral.pl=int(self.QComboBox_pl.currentText()[:-1])
            self.ral.Antenna=self.Antenna
            self.progressBar_Elorejelzes.setValue(0)
            self.progressBar_Elorejelzes.show()
            self.task=PropagationTask(self.iface,self.ral,self.QComboBox_Modell.currentIndex(),self._SzamitasLayer(),self.QTabWidget_Szamitas.currentIndex(),bool(self.QComboBox_FED.currentIndex()>0))
            self.task.progressChanged.connect(self.progressBar_Elorejelzes.setValue)
            self.task.taskCompleted.connect(self._PropagationTask_Completed)
            QgsApplication.taskManager().addTask(self.task)
        else:
            if self.task!=None: self.task.cancel()
    def _PropagationTask_Completed(self):
        self.iface.messageBar().clearWidgets
        self.progressBar_Elorejelzes.hide()
        self.QPushButton_Elorejelzes.setChecked(False)
class ProfileTask(QgsTask):
    def __init__(self,iface,ral:Propagation.RadioLink,Layer):
        super().__init__("Profile task",QgsTask.CanCancel)
        self.iface=iface
        self.ral=ral
        self.Layer=Layer
        self.exception: Optional[Exception] = None
    def run(self):
        try:
            pro=0
            if self.Layer.geometryType() is Qgis.GeometryType.Line:
                for fea in self.Layer.getFeatures(QgsFeatureRequest().addOrderBy("E")):
                    for p in fea.geometry().asPolyline():
                        vevopont=p
                        self.ral.Receiver=WorldPoint(EOV=[vevopont.x(),vevopont.y(),0],m=self.ral.Receiver.m)
                        self.ral.OnWorldPoint_Change()
                        self.ral.readProfile()
                        self.ral.readFedettseg()
                        pro+=1
                        self.setProgress(100*pro/len(fea.geometry().asPolyline()))
                        if self.isCanceled(): return False
                    break
            else:
                for fea in self.Layer.getFeatures(QgsFeatureRequest().addOrderBy("id")):
                    vevopont=QgsPointXY(fea.geometry().centroid().asPoint())
                    self.ral.Receiver=WorldPoint(EOV=[vevopont.x(),vevopont.y(),0],m=self.ral.Receiver.m)
                    self.ral.OnWorldPoint_Change()
                    self.ral.readProfile()
                    self.ral.readFedettseg()
                    pro+=1
                    self.setProgress(100*pro/self.Layer.featureCount())
                    if self.isCanceled(): return False
            return True
        except Exception as e:
            self.exception = e
            return False
    def finished(self, result):
        if not(self.isCanceled()):
            if not result:
                # if there was an error
                #self.iface.messageBar().pushMessage("adopont","x="+str(adopont.x())+" y:"+str(adopont.y()),level=1,duration=-1)
                QMessageBox.critical(self.iface.mainWindow(),"Error",f"The following error occurred:\n{self.exception.__class__.__name__}: {self.exception}")
    def cancel(self):
        QgsMessageLog.logMessage(message=f"Canceled profile task",level=Qgis.Warning,)
        super().cancel()
class PropagationTask(QgsTask):
    def __init__(self,iface,ral:Propagation.RadioLink,modi,Layer,tabindex,kellfed:bool):
        super().__init__("Propagation task",QgsTask.CanCancel)
        self.iface=iface
        self.ral=ral
        self.modi=modi
        self.Layer=Layer
        self.kellfed=kellfed
        self.exception: Optional[Exception] = None
    def run(self):
        try:
            self.Layer.startEditing()
            self.Layer.beginEditCommand("Elorejelzes")
            pro=0
            if self.Layer.geometryType() is Qgis.GeometryType.Line:
                for fea in self.Layer.getFeatures(QgsFeatureRequest().addOrderBy("E")):
                    poly=[]
                    for ir in range(0,360+10,10):
                        self.ral.getProfile(int(ir/10))
                        pfl=self.ral.Terep.Profile
                        if self.kellfed:
                            self.ral.getFedettseg(0)
                            fed=self.ral.Terep.Fedettseg                
                        dx=self.ral.Terep.dl*math.sin(math.radians(ir))
                        dy=self.ral.Terep.dl*math.cos(math.radians(ir))
                        self.ral.Receiver=self.ral.Transmitter
                        dstep=int(100/self.ral.Terep.dl)
                        for d in range(dstep,len(pfl),dstep):
                            vevopont=QgsPointXY(self.ral.Transmitter.EOV.x()+dx*d,self.ral.Transmitter.EOV.y()+dy*d)
                            self.ral.Receiver=WorldPoint(EOV=[vevopont.x(),vevopont.y(),0],m=self.ral.Receiver.m)
                            self.ral.OnWorldPoint_Change()
                            self.ral.Terep.Profile=pfl[:d]
                            if self.kellfed: self.ral.Fedettseg=fed[:d]
                            E=self.Modell().E()
                            if E<=fea["E"]:
                                poly.append(vevopont)
                                break
                        pro+=1
                        self.setProgress(100*pro/self.Layer.featureCount()/37)
                        if self.isCanceled(): return False
                    poly.append(poly[0])
                    self.Layer.changeGeometry(fea.id(),QgsGeometry.fromPolylineXY(poly))
            else:
                for fea in self.Layer.getFeatures(QgsFeatureRequest().addOrderBy("id")):
                    vevopont=QgsPointXY(fea.geometry().centroid().asPoint())
                    self.ral.Receiver=WorldPoint(EOV=[vevopont.x(),vevopont.y(),0],m=self.ral.Receiver.m)
                    self.ral.OnWorldPoint_Change()
                    self.ral.getProfile(fea["Mp"])
                    if self.kellfed: self.ral.getFedettseg(fea["Mp"])
                    self.Layer.changeAttributeValue(fea.id(),self.Layer.fields().indexOf("E"),round(float(self.Modell().E()),1))
                    pro+=1
                    self.setProgress(100*pro/self.Layer.featureCount())
                    if self.isCanceled(): return False
            return True
        except Exception as e:
            self.exception = e
            return False
    def finished(self,result):
        self.Layer.endEditCommand()
        self.Layer.commitChanges()
        if not(self.isCanceled()):
            if not result:
                # if there was an error
                #self.iface.messageBar().pushMessage("adopont","x="+str(adopont.x())+" y:"+str(adopont.y()),level=1,duration=-1)
                QMessageBox.critical(self.iface.mainWindow(),"Error",f"The following error occurred:\n{self.exception.__class__.__name__}: {self.exception}")
    def cancel(self):
        QgsMessageLog.logMessage(message=f"Canceled propagation task",level=Qgis.Warning,)
        super().cancel()
    def Modell(self):
        if self.modi==0:
            return Propagation.Freespace(RadioLink=self.ral)
        elif self.modi==1:
            return Propagation.EmpiricalTwoRay(RadioLink=self.ral)
        elif self.modi==2:
            return Propagation.Hata(RadioLink=self.ral)
        elif self.modi==3:
            return Propagation.COSTHata(RadioLink=self.ral)
        elif self.modi==4:
            return Propagation.ExtendedHata(RadioLink=self.ral)
        elif self.modi==5:
            return Propagation.ITU1546(RadioLink=self.ral)
        elif self.modi==6:
            return Propagation.ITM(RadioLink=self.ral)
