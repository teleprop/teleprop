# -*- coding: utf-8 -*-
from .GeoCoord import WorldPoint
import math
import numpy as np

from .itmlogic.misc.qerfi import qerfi
from .itmlogic.preparatory_subroutines.qlrpfl import qlrpfl
from .itmlogic.statistics.avar import avar
from .Py1546 import P1546
from qgis.core import (
    QgsProject,QgsPointXY,QgsPoint,
    QgsCoordinateReferenceSystem,QgsCoordinateTransform)
class Propagation(object):
    class RadioLink(object):
        class Terep(object):
            def __init__(self,ownerRadioLink):
                self.RadioLink=ownerRadioLink
                self.DEMlayer=None
                self.FEDlayer=None
                self.FEDvalues=None
                self.Profile=[]
                self.Fedettseg=[]
                self.ClutterHeight=[]
                self.dx=0
                self.dy=0
                self.dl=0
                self._eovtodem=None
                self._eovtofed=None
            def set_DEMlayer(self,newDEMlayer):
                self.DEMlayer=newDEMlayer
                eovcrs=QgsCoordinateReferenceSystem("EPSG:23700")
                self._eovtodem=QgsCoordinateTransform(eovcrs,self.DEMlayer.crs(),QgsProject.instance().transformContext())
            def set_FEDlayer(self,newFEDlayer):
                self.FEDlayer=newFEDlayer
                if self.FEDlayer!=None:
                    eovcrs=QgsCoordinateReferenceSystem("EPSG:23700")
                    self._eovtofed=QgsCoordinateTransform(eovcrs,self.FEDlayer.crs(),QgsProject.instance().transformContext())
            def _readProfile(self):
                if self.DEMlayer!=None:
                    self.dl=min(self.DEMlayer.rasterUnitsPerPixelX(),self.DEMlayer.rasterUnitsPerPixelY())
                    self.dx=self.dl*math.sin(math.radians(self.RadioLink.ir))
                    self.dy=self.dl*math.cos(math.radians(self.RadioLink.ir))
                    self.Profile=[]
                    p=QgsPointXY(self.RadioLink.Transmitter.EOV.x(),self.RadioLink.Transmitter.EOV.y())
                    d=0
                    while d<self.RadioLink.d:
                        self.Profile.append(self._EOVmagassag(p))
                        p.setX(p.x()+self.dx)
                        p.setY(p.y()+self.dy)
                        #if Foldgorbulet: self.Profile[-1] += self.MagKorr((self.RadioLink.d / self.get_Resolution_m()) * self.get_Resolution_m(), i * self.get_Resolution_m()))
                        d+=self.dl
            def _readFedettseg(self):
                if self.FEDlayer!=None:
                    self.Fedettseg=[]
                    self.ClutterHeight=[]
                    p=QgsPointXY(self.RadioLink.Transmitter.EOV.x(),self.RadioLink.Transmitter.EOV.y())
                    d=0
                    while d<self.RadioLink.d:
                        fed=self._EOVfedettseg(p)
                        self.Fedettseg.append(fed)
                        self.ClutterHeight.append(self._fedHeight(fed))
                        p.setX(p.x()+self.dx)
                        p.setY(p.y()+self.dy)
                        d+=self.dl
            def _fedHeight(self,fedValue):
                res=next((sub for sub in self.FEDvalues if sub[0]==fedValue),None)
                return res[1]
            def _EOVmagassag(self,EOV:QgsPoint):
                pdem=self._eovtodem.transform(QgsPointXY(EOV.x(),EOV.y()))
                return self.DEMlayer.dataProvider().sample(pdem,1)[0]
            def _EOVfedettseg(self,EOV:QgsPoint):
                pfed=self._eovtofed.transform(QgsPointXY(EOV.x(),EOV.y()))
                fed=self.FEDlayer.dataProvider().sample(pfed,1)[0]
                if math.isnan(fed): fed=0
                return int(fed)
        kToDipol=2.14
        #EEnvironment={"Open":0,"Rural":1,"Suburban":2,"Urban_Small":3,"Urban_Large":4}
        EEnvironment=["Sea","Rural","Suburban","Urban","Dense Urban"]
        ETransmitterSystem={"Analog":0,"Digital":1}
        EService={"Broadcast":0,"Mobile":1}
        EPol={"H":0,"V":1}
        def __init__(self, **kwargs):
            """
            Rádió összeköttetés
            kwargs:
            MHz = 30..3000 MHz Operating frequency, default=100
            Transmitter = Adó QgsPoint EOV
            Receiverer = Vevő QgsPoint EOV
            dkm = Összeköttetés távolsága km-ben<1000 Horizontal path length
            TransmitterSystem = ETransmitterSystem = {"Analog":0,"Digital":1}, default=Digital
            LocationPecentage = 1..50 Percentage location, default=50 %
            TimePecentage = 1..50 Percentage time, default=50 %
            BWMHz = deafult=8
            GeneralEnvironment = beépítettség EEnvironment=["Sea","Rural","Suburban","Urban","Dense Urban"]
            Service = Szolgálat jellege EService = {"Broadcast":0,"Mobile":1}
            Pol = EPol Polarizáció - csak ITM-nél számít
            """
            self.ir=None
            if "MHz" in kwargs: self.f=kwargs["MHz"]
            else: self.f=100
            if "Transmitter" in kwargs:self.Transmitter=kwargs["Transmitter"]
            else: self.Transmitter=WorldPoint()
            if "Receiver" in kwargs: self.Receiver=kwargs["Receiver"]
            else: self.Receiver=WorldPoint()
            if "TransmitterSystem" in kwargs: self.TransmitterSystem=kwargs["TransmitterSystem"]
            else: self.TransmitterSystem=self.ETransmitterSystem["Digital"]
            if "LocationPecentage" in kwargs: self.pl=kwargs["LocationPecentage"]
            else: self.pl=50
            if "TimePecentage" in kwargs: self.pt=kwargs["TimePecentage"]
            else: self.pt=50
            if "BWMHz" in kwargs: self.Bt=kwargs["BWMHz"]
            else: self.Bt=8
            if "GeneralEnvironment" in kwargs: self.GeneralEnvironment=self.EEnvironment.index(kwargs["GeneralEnvironment"])
            else: self.GeneralEnvironment=self.EEnvironment.index("Rural")
            if "Service" in kwargs: self.Service=kwargs["Service"]
            else: self.Service=self.EService["Broadcast"]
            if "Pol" in kwargs: self.Pol=kwargs["Pol"]
            else: self.Pol=self.EPol["H"]
            if "ERPkW" in kwargs: self.ERPkW=kwargs["ERPkW"]
            else: self.ERPkW=1
            self.Antenna=None
            self.AntennaMaxIr=0
            self.voltERPkW=self.ERPkW
            self.Terep=Propagation.RadioLink.Terep(self)
            if "dkm" in kwargs: self.set_dkm(kwargs["dkm"])
            else: self.OnWorldPoint_Change()
            self._Profiles=[]
            self._Fedettsegek=[]
        def readProfile(self):
            self.Terep._readProfile()
            self._Profiles.append(self.Terep.Profile)
        def clearProfiles(self):
            self._Profiles=[]
        def saveProfiles(self,filename):
            np.save(filename,[self.Terep.dl,np.array(self._Profiles)],allow_pickle=True)
        def loadProfiles(self,filename):
            self.clearProfiles()
            self.Terep.dl,self._Profiles=np.load(filename,allow_pickle=True)
        def getProfile(self,mp):
            self.Terep.Profile=self._Profiles[mp-1]
        def readFedettseg(self):
            self.Terep._readFedettseg()
            self._Fedettsegek.append(self.Terep.Fedettseg)
            self._ClutterHeights.append(self.Terep.ClutterHeight)
        def clearFedettsegek(self):
            self._Fedettsegek=[]
            self._ClutterHeights=[]
        def saveFedettsegek(self,filename):
            np.save(filename,np.array([self._Fedettsegek,self._ClutterHeights]),allow_pickle=True)
        def loadFedettsegek(self,filename):
            self.clearFedettsegek()
            self._Fedettsegek,self._ClutterHeights=np.load(filename,allow_pickle=True)
        def getFedettseg(self,mp):
            self.Terep.Fedettseg=self._Fedettsegek[mp-1]
            self.Terep.ClutterHeight=self._ClutterHeights[mp-1]
        def set_dkm(self,value):
            self.dkm=value
            self.d=self.dkm*1000
        def set_d(self,value):
            self.d=value
            self.dkm=self.d/1000
        def set_LocationPecentage(self,p):
            self.pl=p
        def set_TimePecentage(self,p):
            self.pt=p
        def set_ERPkW(self,kW):
            self.ERPkW=kW
            self.voltERPkW=kW
        def OnWorldPoint_Change(self):
            if (hasattr(self.Transmitter,"WGS")) and (hasattr(self.Receiver,"WGS")):
                self.d=self.Transmitter.Distance(self.Receiver)
                self.dkm=self.d/1000
                adopont=QgsPointXY(self.Transmitter.EOV.x(),self.Transmitter.EOV.y())
                vevopont=QgsPointXY(self.Receiver.EOV.x(),self.Receiver.EOV.y())
                self.ir=adopont.azimuth(vevopont)
                self.Transmitter.EOV.setZ(self.Terep._EOVmagassag(self.Transmitter.EOV))
                self.Receiver.EOV.setZ(self.Terep._EOVmagassag(self.Receiver.EOV))
                if not(self.Antenna is None):
                    ir=self.Antenna[:,0]
                    dB=self.Antenna[:,1]
                    idB=np.interp(self.ir-self.AntennaMaxIr,ir,dB,period=360)
                    self.ERPkW=self.voltERPkW*10**(idB/10)
        def Curb(self):
            hado = float(self.Transmitter.WGS.Elev + self.Transmitter.m)
            losal = float(self.Receiver.WGS.Elev + self.Receiver.m - hado) / self.d
            d = self.Terep.dl
            ovr = 0
            if len(self.Terep.Profile)>2:
                ovr = len(self.Terep.Profile)-2
                for i in range(1,len(self.Terep.Profile)-2):
                    hd = losal * d + hado
                    hov = hd - self.Receiver.m - self.Terep.Profile[i]
                    if hov>0: ovr -= 1
                    d += self.Terep.TerepResolution_m
                ovr =float(ovr) / float(len(self.Terep.Profile)-2)
            return ovr
        def kantenna(self,G):
            return -29.78+20*math.log10(self.RadioLink.f)-G
        def E(self,Loss,ERPkW=-1):
            """
            Loss = átviteli út csillapítása
            ERP kW-hoz
            return E = térerősség [dBuV/m]
            """
            if ERPkW==-1: ERPkW=self.ERPkW
            return 137.2217-Loss+20*math.log10(self.f)+10*math.log10(ERPkW)
        def CP(self,E,ERPkW,Gr):
            """
            ERPkW = Padó[kW]
            Gr = Vevőantenna nyereség izotróphoz képest [dB]
            """
            return 10*math.log10(ERPkW)+E-kantenna(Gr)-107
        def Loss(self,E,ERPkW=-1):
            """
            E = térerősség [dBuV/m]
            ERP kW-hoz
            return Loss = átviteli út csillapítása
            """
            if ERPkW==-1: ERPkW=self.ERPkW
            return 137.2217-E + 20*math.log10(self.f)+10*math.log10(ERPkW)
        def FarFieldDistance(self):
            return 4*math.pi*self.Transmitter.m*self.Receiver.m*self.f/300
    class Freespace(object):
        def __init__(self, *args, **kwargs):
            """
            RadioLink vagy
            MHz, dkm
            """
            if "RadioLink" in kwargs: self.RadioLink=kwargs["RadioLink"]
            else:
                self.RadioLink = Propagation.RadioLink()
                if "MHz" in kwargs: self.RadioLink.f = kwargs["MHz"]
                if "dkm" in kwargs: self.RadioLink.set_dkm = kwargs["dkm"]
        def Loss(self):
            return 20*math.log10(self.RadioLink.dkm)+20*math.log10(self.RadioLink.f)+32.45
        def E(self):
            """
            Szabadtéri csillapítással számított térerősség izotróp antennán, dipólon nagyobb kToDipol-lal
            """
            return self.RadioLink.E(self.Loss(),self.RadioLink.ERPkW)
        def CheckModel(self):
            #Altair WinProp 2021.0.3
            return self.RadioLink.d>1,"d > 1m"
    class EmpiricalTwoRay(object):
        def __init__(self, *args, **kwargs):
            """
            RadioLink vagy
            MHz, dkm
            """
            if "RadioLink" in kwargs: self.RadioLink=kwargs["RadioLink"]
            else:
                self.RadioLink = Propagation.RadioLink()
                if "MHz" in kwargs: self.RadioLink.f = kwargs["MHz"]
                if "dkm" in kwargs: self.RadioLink.set_dkm = kwargs["dkm"]
        def Loss(self):
            if self.RadioLink.d<1:
                return 20
            L=40*math.log10(self.RadioLink.d)-20*math.log10(self.RadioLink.Transmitter.m*self.RadioLink.Receiver.m)
            Lfsp=Propagation.Freespace(RadioLink=self.RadioLink).Loss()
            if L<Lfsp: L=Lfsp
            if L<20: L=20
            return L
        def E(self):
            return self.RadioLink.E(self.Loss(),self.RadioLink.ERPkW)
        def CheckModel(self):
            #Altair WinProp 2021.0.3
            los=self.RadioLink.Transmitter.LineOfSight()
            return self.RadioLink.d<los,"d < LOS (={0:.1f}m)".format(los)
    class Hata(object):
        def __init__(self, *args, **kwargs):
            """
            RadioLink vagy
            MHz, dkm
            """
            if "RadioLink" in kwargs:
                self.RadioLink=kwargs["RadioLink"]
            else:
                self.RadioLink=Propagation.RadioLink()
                if "MHz" in kwargs: self.RadioLink.f = kwargs["MHz"]
                if "dkm" in kwargs: self.RadioLink.set_dkm(kwargs["dkm"])
        def Loss(self):
            if self.RadioLink.d<1: return 20
            logf=math.log10(self.RadioLink.f)
            Lu=69.55+26.16*logf-13.82*math.log10(self.RadioLink.Transmitter.m)+math.log10(self.RadioLink.dkm)*(44.9-6.55*math.log10(self.RadioLink.Transmitter.m))
            if self.RadioLink.GeneralEnvironment==self.RadioLink.EEnvironment.index("Dense Urban"):
                if self.RadioLink.f<=200:
                    Ch=8.29*(math.log10(1.54*self.RadioLink.Receiver.m))**2-1.1
                else:
                    Ch=3.2*(math.log10(11.75*self.RadioLink.Receiver.m))**2-4.97
            else: Ch=0.8+(1.1*logf-0.7)*self.RadioLink.Receiver.m-1.56*logf
            if self.RadioLink.GeneralEnvironment==self.RadioLink.EEnvironment.index("Suburban"): Lu-=2*math.log10(self.RadioLink.f/28)**2+5.4
            if self.RadioLink.GeneralEnvironment<self.RadioLink.EEnvironment.index("Suburban"): Lu-=4.78*math.log10(self.RadioLink.f)**2-18.33*logf+40.94
            return Lu-Ch
        def E(self):
            return self.RadioLink.E(self.Loss(),self.RadioLink.ERPkW)
        def CheckModel(self):
            #Altair WinProp 2021.0.3
            return (self.RadioLink.f>=150) and (self.RadioLink.f<=1500) and (self.RadioLink.dkm>=0.1) and (self.RadioLink.dkm<=20) and (self.RadioLink.Transmitter.m>=30) and (self.RadioLink.Transmitter.m<=200) and (self.RadioLink.Receiver.m>=1) and (self.RadioLink.Receiver.m<=10),            "150MHz <= f <=1500MHz and 100m <= d <= 20km and 30m <= h1 <= 200m and 1m <= h2 <= 10m"
    class COSTHata(object):
        def __init__(self, *args, **kwargs):
            """
            RadioLink vagy
            MHz, dkm
            """
            if "RadioLink" in kwargs:
                self.RadioLink=kwargs["RadioLink"]
            else:
                self.RadioLink = Propagation.RadioLink()
                if "MHz" in kwargs: self.RadioLink.f = kwargs["MHz"]
                if "dkm" in kwargs: self.RadioLink.set_dkm(kwargs["dkm"])
        def Loss(self):
            if self.RadioLink.d<1: return 20
            logf=math.log10(self.RadioLink.f)
            Lb=46.3+33.9*logf-13.82*math.log10(self.RadioLink.Transmitter.m)+math.log10(self.RadioLink.dkm)*(44.9-6.55*math.log10(self.RadioLink.Transmitter.m))
            ahr=(1.1*logf-0.7)*self.RadioLink.Receiver.m-(1.56*logf-0.8)
            if self.RadioLink.GeneralEnvironment>self.RadioLink.EEnvironment.index("Urban"):
                if self.RadioLink.f<=200:
                    ahr=8.29*(math.log10(1.54*self.RadioLink.Receiver.m))**2-1.1
                else:
                    ahr=3.2*(math.log10(11.75*self.RadioLink.Receiver.m))**2-4.97
            if self.RadioLink.GeneralEnvironment==self.RadioLink.EEnvironment.index("Dense Urban"): ahr-=3
            Lb-=ahr
            Lfsp=Propagation.Freespace(RadioLink=self.RadioLink).Loss()
            if Lb<Lfsp: Lb=Lfsp
            if Lb<20: Lb=20
            return Lb
        def E(self):
            return self.RadioLink.E(self.Loss(),self.RadioLink.ERPkW)
        def CheckModel(self):
            #Altair WinProp 2021.0.3
            return (self.RadioLink.f>=150) and (self.RadioLink.f<=1500) and (self.RadioLink.dkm>=0.1) and (self.RadioLink.dkm<=20) and (self.RadioLink.Transmitter.m>=30) and (self.RadioLink.Transmitter.m<=200) and (self.RadioLink.Receiver.m>=1) and (self.RadioLink.Receiver.m<=10),"150MHz <= f <=1500MHz and 100m <= d <= 20km and 30m <= h1 <= 200m and 1m <= h2 <= 10m"
    class ExtendedHata(object):
        def __init__(self, *args, **kwargs):
            """
            RadioLink vagy
            MHz, dkm
            """
            if "RadioLink" in kwargs:
                self.RadioLink=kwargs["RadioLink"]
            else:
                self.RadioLink=Propagation.RadioLink()
                if "MHz" in kwargs: self.RadioLink.f = kwargs["MHz"]
                if "dkm" in kwargs: self.RadioLink.set_dkm(kwargs["dkm"])
        def Loss(self):
            if self.RadioLink.d<1:
                return 20
            logf=math.log10(self.RadioLink.f)
            ahm=((1.1*logf)-0.7)*min(10,self.RadioLink.Receiver.m)-(1.56*logf-0.8)+max(0,20*math.log10(self.RadioLink.Receiver.m/10))
            bhb=min(0,20*math.log10(self.RadioLink.Transmitter.m/30))
            alfa=1
            if self.RadioLink.dkm>20: alfa=1+(0.14+0.000187*self.RadioLink.f+0.00107*self.RadioLink.Transmitter.m)*(math.log10(self.RadioLink.dkm/20))**0.8
            L=0
            if (self.RadioLink.f>30) and (self.RadioLink.f<=150):
                L=69.6+26.2*math.log10(150)-20*math.log10(150/self.RadioLink.f)-13.82*math.log10(max(30,self.RadioLink.Transmitter.m))+(44.9-6.55*math.log10(max(30,self.RadioLink.Transmitter.m)))*math.log10(self.RadioLink.dkm)**alfa-ahm-bhb
            if (self.RadioLink.f>150) and (self.RadioLink.f<=1500):
                L=69.6+26.2*logf-13.82*math.log10(max(30,self.RadioLink.Transmitter.m))+(44.9-6.55*math.log10(max(30,self.RadioLink.Transmitter.m)))*math.log10(self.RadioLink.dkm)**alfa-ahm-bhb
            if (self.RadioLink.f>1500) and (self.RadioLink.f<=2000):
                L=46.3+33.9*logf-13.82*math.log10(max(30,self.RadioLink.Transmitter.m))+(44.9-6.55*math.Log10(max(30,self.RadioLink.Transmitter.m))) * math.log10(self.RadioLink.dkm)**alfa-ahm-bhb
            if (self.RadioLink.f>2000) and (self.RadioLink.f<=3000):
                L=46.3+33.9*math.log10(2000)+10*math.log10(self.RadioLink.f/2000)-13.82*math.log10(max(30,self.RadioLink.Transmitter.m))+(44.9-6.55*math.log10(max(30,self.RadioLink.Transmitter.m)))*math.log10(self.RadioLink.dkm)**alfa-ahm-bhb
            if (self.RadioLink.GeneralEnvironment==self.RadioLink.EEnvironment.index("Suburban")):
                L=L-2*(math.log10((min(max(150,self.RadioLink.f),2000)/28)))**2-5.4
            if (self.RadioLink.GeneralEnvironment<self.RadioLink.EEnvironment.index("Suburban")):
                L=L-4.78*(math.log10(min(max(150,self.RadioLink.f),2000)))**2+18.33*math.log10((min(max(150,self.RadioLink.f),2000)))-40.94
            Lfsp=Propagation.Freespace(RadioLink=self.RadioLink).Loss()
            if L<Lfsp: L=Lfsp
            if L<20: L=20
            return L
        def E(self):
            return self.RadioLink.E(self.Loss(),self.RadioLink.ERPkW)
        def CheckModel(self):
            #Altair WinProp 2021.0.3
            return (self.RadioLink.f>=30) and (self.RadioLink.f<=3000) and (self.RadioLink.dkm>=0.1) and (self.RadioLink.dkm<=40) and (self.RadioLink.Transmitter.m>=30) and (self.RadioLink.Transmitter.m<=200) and (self.RadioLink.Receiver.m>=1) and (self.RadioLink.Receiver.m<=10),            "30MHz <= f <=3000MHz and 100m <= d <= 40km and 30m <= h1 <= 200m and 1m <= h2 <= 10m"
    class ITU1546(object):
        def __init__(self, *args, **kwargs):
            """
            RadioLink vagy
            MHz, dkm, heff
            """
            if "RadioLink" in kwargs:
                self.RadioLink=kwargs["RadioLink"]
            else:
                self.RadioLink=Propagation.RadioLink()
                if "MHz" in kwargs: self.RadioLink.f=kwargs["MHz"]
                if "dkm" in kwargs: self.RadioLink.set_dkm(kwargs["dkm"])
                if "heff" in kwargs: self.heff=kwargs["heff"]
            if "AnalogDigital" in kwargs: self.RadioLink.AnalogDigital= kwargs["AnalogDigital"]
            if "BWMHz" in kwargs: self.RadioLink.BWMHz=kwargs["BWMHz"]
            if "LocationPecentage" in kwargs: self.RadioLink.pl=kwargs["LocationPecentage"]
            if "TimePecentage" in kwargs: self.RadioLink.pt=kwargs["TimePecentage"]
            if "Environment" in kwargs: self.RadioLink.GeneralEnvironment=self.RadioLink.EEnvironment.index(kwargs["Environment"])
            if "Service" in kwargs: self.RadioLink.Service=kwargs["Service"]
            if "TimePecentage" in kwargs: self.RadioLink.pt= kwargs["TimePecentage"]
            self.sg3db=P1546.SG3DB()
        def CreateSG3DB(self):
            self.sg3db.first_point_transmitter=1
            self.sg3db.TxRxDistance=self.RadioLink.dkm
            self.sg3db.x=np.arange(0,self.RadioLink.dkm,self.RadioLink.Terep.dl/1000)
            self.sg3db.h_gamsl=np.array(self.RadioLink.Terep.Profile)
            if len(self.sg3db.x)>len(self.sg3db.h_gamsl): self.sg3db.x=self.sg3db.x[:len(self.sg3db.h_gamsl)]
            if len(self.sg3db.h_gamsl)>len(self.sg3db.x): self.sg3db.h_gamsl=self.sg3db.h_gamsl[:len(self.sg3db.x)]
            if self.RadioLink.Terep.FEDlayer==None:
                self.sg3db.coveragecode=np.full(len(self.RadioLink.Terep.Profile),self.RadioLink.GeneralEnvironment)
                self.sg3db.h_ground_cover=np.full(len(self.RadioLink.Terep.Profile),10*max(0,self.RadioLink.GeneralEnvironment-1))
            else:
                self.sg3db.coveragecode=np.array(self.RadioLink.Terep.Fedettseg,dtype="object")
                self.sg3db.h_ground_cover=np.array(self.RadioLink.Terep.ClutterHeight)
            self.sg3db.radio_met_code=np.full(len(self.RadioLink.Terep.Profile),4)#Land=4, Coast=3, Sea=1
            self.sg3db.frequency=np.array([self.RadioLink.f])
            self.sg3db.hTx=np.array([self.RadioLink.Transmitter.m])
            self.sg3db.hTxeff=np.array([np.nan])
            self.sg3db.hRx=np.array([self.RadioLink.Receiver.m])
            self.sg3db.polHVC=np.array([self.RadioLink.Pol]) #H=0,V=1,C=2
            self.sg3db.TxdBm=np.array([np.nan])
            self.sg3db.MaxLb=np.array([np.nan])
            self.sg3db.Txgn=np.array([np.nan])#Transmitter Gain
            self.sg3db.Rxgn=np.array([np.nan])#Receiver Gain
            self.sg3db.RxAntDO=np.array([np.nan])#Antenna előre/hátra viszony
            self.sg3db.ERPMaxHoriz=np.array([10**(self.RadioLink.ERPkW/10)+30])#ERP dBW vízszintes síkban
            self.sg3db.ERPMaxVertical=np.array([np.nan])
            self.sg3db.ERPMaxTotal=self.sg3db.ERPMaxHoriz
            self.sg3db.HRPred=np.array([np.nan])
            self.sg3db.TimePercent=np.array([self.RadioLink.pt])
            self.sg3db.q=np.array([self.RadioLink.pl])
            self.sg3db.LwrFS=np.array([np.nan])#Losses relative to free space
            self.sg3db.MeasuredFieldStrength=np.array([np.nan])
            self.sg3db.BasicTransmissionLoss=np.array([np.nan])
            self.sg3db.RxHeightGainGroup=np.array([-1])
            self.sg3db.IsTopHeightInGroup=np.array([1])
            self.sg3db.Ndata=1 #Number of different measured data sets
        def Szamol(self):
            self.CreateSG3DB()
            flag_debug=0 #set to 1 if the csv log files need to be produced (together with stdout)
            flag_plot=0 #set to 1 if the plots of the height profile are to be shown
            flag_path=1 #pathprofile is available (=1), not available (=0)
            wa=500 #Dimension of a square area for variability calculation
            ClutterCode='P1546'
            self.sg3db.debug=flag_debug #collect intermediate results in log files (=1), or not (=0)
            self.sg3db.pathinfo=1 #pathprofile is available (=1), not available (=0)
            #update the data structure with the Tx Power (kW)
            for kindex in range(0,self.sg3db.Ndata):
                PERP=self.sg3db.ERPMaxTotal[kindex]
                HRED=self.sg3db.HRPred[kindex]
                PkW=10**(PERP/10)/1000  #kW
                if np.isnan(PkW):
                    # use complementary information from Basic Transmission Loss and
                    # received measured strength to compute the transmitter power + gain
                    E=self.sg3db.MeasuredFieldStrength[kindex]
                    PL=self.sg3db.BasicTransmissionLoss[kindex]
                    f=self.sg3db.frequency[kindex]
                    PdBkW=-137.2217+E-20*math.log10(f)+PL
                    PkW=10**(PdBkW/10.0)
                self.sg3db.TransmittedPower=np.append(self.sg3db.TransmittedPower,PkW)
            # discriminate land and sea portions
            dland=0
            dsea=0
            if (len(self.sg3db.radio_met_code)>0) and (len(self.sg3db.coveragecode)>0):
                for i in range(0,len(self.sg3db.x)):
                    if i==len(self.sg3db.x)-1:
                        dinc=(self.sg3db.x[-1]-self.sg3db.x[-2])/2
                    elif i==0:
                        dinc=(self.sg3db.x[1]-self.sg3db.x[0])/2
                    else:
                        dinc=(self.sg3db.x[i+1]- self.sg3db.x[i-1])/2
                    if (self.sg3db.radio_met_code[i]==1) or (self.sg3db.radio_met_code[i]==3):  #sea and coastal land
                        dsea=dsea+dinc
                    else:
                        dland=dland+dinc
            elif len(self.sg3db.radio_met_code)==0 and len(self.sg3db.coveragecode)>0:
                for i in range(0,len( self.sg3db.x)):
                    if (i==len( self.sg3db.x)-1):
                        dinc=(self.sg3db.x[-1]-self.sg3db.x[-2])/2.0
                    elif (i==0):
                        dinc=(self.sg3db.x[1]-self.sg3db.x[0])/2.0
                    else:
                        dinc=(self.sg3db.x[i+1]-self.sg3db.x[i-1])/2.0
                    if self.sg3db.coveragecode[i]==2:  #sea - when radio-met code is missing, it is supposed that the file is organized as in DNR p.1812...
                        dsea=dsea+dinc
                    else:
                        dland=dland+dinc
            else:
                dland=np.nan
                dsea=np.nan
            hTx=self.sg3db.hTx
            hRx=self.sg3db.hRx
            for measID in range(0,len(hRx)):
                #print ('Computing the fields for Dataset # %d\n' % (measID))
                # Determine clutter heights
                if len(self.sg3db.coveragecode)>0:
                    i=self.sg3db.coveragecode[-1]
                    RxClutterCode,RxP1546Clutter,R2external=P1546.clutter(i,ClutterCode)
                    i=self.sg3db.coveragecode[0]
                    TxClutterCode,TxP1546Clutter,R1external=P1546.clutter(i,ClutterCode)
                    if TxP1546Clutter.find('Rural') != -1: # do not apply clutter correction at the transmitter side
                        R1external = 0
                    # if clutter heights are specified in the input file, use those instead of representative clutter heights
                    if (np.size(self.sg3db.h_ground_cover)!=0) and (ClutterCode.find('default')==-1):
                        if not np.isnan(self.sg3db.h_ground_cover[-1]):
                            self.sg3db.RxClutterHeight=self.sg3db.h_ground_cover[-1]
                        else:
                            self.sg3db.RxClutterHeight=R2external
                        if not np.isnan(self.sg3db.h_ground_cover[0]):
                            self.sg3db.TxClutterHeight=self.sg3db.h_ground_cover[0]
                        else:
                            self.sg3db.TxClutterHeight=R1external
                    else:
                        self.sg3db.RxClutterHeight = R2external
                        self.sg3db.TxClutterHeight = R1external
                else:                
                    # cov-code is empty, use default
                    [RxClutterCode,RxP1546Clutter,R2external]=P1546.clutter(1,ClutterCode)
                    [TxClutterCode,TxP1546Clutter,R1external]=P1546.clutter(1,ClutterCode)
                    self.sg3db.RxClutterCodeP1546=RxP1546Clutter
                    self.sg3db.RxClutterHeight=R2external
                    self.sg3db.TxClutterHeight=R1external
                xx=self.sg3db.x[-1]-self.sg3db.x[0]
                self.sg3db.LandPath=dland
                self.sg3db.SeaPath=dsea         
                # implementation of P1546-6 Annex 5 Paragraph 1.1
                # if both terminals are at or below the levels of clutter in their respective vicinities,
                # then the terminal  with the greater height above ground should be treated as the transmitting/base station
                # Once the clutter has been chosen, the second terminal becomes a
                # transmitter in the following cases according to S5 1.11
                # a) both 1 and 2 are below clutter (h1<R1, h2<R2) and h2>h1
                # b) 2 is above clutter and 1 is below clutter (h1<R1, h2>R2)
                # c) both 1 and 2 are above clutter (h1>R1 h2>R2) and h2eff > h1eff
                hhRx=hRx[measID]
                hhTx=hTx[measID]
                x=self.sg3db.x
                h_gamsl=self.sg3db.h_gamsl
                x_swapped = x[-1]-x[::-1]
                h_gamsl_swapped = h_gamsl[::-1]
                swap_flag = False
                heff=P1546.heffCalc(x,h_gamsl,hTx[measID])
                heff_swapped=P1546.heffCalc(x_swapped,h_gamsl_swapped, hRx[measID])
                if (self.sg3db.first_point_transmitter == 0):
                    swap_flag = True
                TxSiteName = self.sg3db.TxSiteName
                RxSiteName = self.sg3db.RxSiteName
                if swap_flag:
                    # exchange the positions of Tx and Rx
                    #print('Annex 5 Paragraph 1.1 applied, terminals are swapped.\n')
                    dummy = hhRx
                    hhRx = hhTx
                    hhTx = dummy
                    x = x_swapped
                    h_gamsl = h_gamsl_swapped
                    dummy = self.sg3db.TxClutterHeight
                    self.sg3db.TxClutterHeight = self.sg3db.RxClutterHeight
                    self.sg3db.RxClutterHeight = dummy
                    TxSiteName = self.sg3db.RxSiteName
                    RxSiteName = self.sg3db.TxSiteName
                    dummy = RxP1546Clutter
                    RxP1546Clutter = TxP1546Clutter
                    TxP1546Clutter = dummy
                    dummy = RxClutterCode
                    RxClutterCode = TxClutterCode
                    TxClutterCode = dummy
                self.sg3db.h2=hhRx
                self.sg3db.ha=hhTx
                # path info is available (in the sg3db files)
                self.sg3db.htter=h_gamsl[0]
                self.sg3db.hrter=h_gamsl[-1]
                self.sg3db.RxClutterCodeP1546 = RxP1546Clutter
                # # plot the profile
                if flag_plot:
                    fig_cnt=fig_cnt + 1
                    newfig=pl.figure(fig_cnt)
                    h_plot=pl.plot(x,h_gamsl,linewidth = 2,color = 'k')
                    pl.xlim(np.min(x), np.max(x))
                    hTx = self.sg3db.hTx
                    hRx = self.sg3db.hRx
                    pl.title('Tx: ' + self.sg3db.TxSiteName + ', Rx: '  + self.sg3db.RxSiteName + ', ' +  self.sg3db.TxCountry +  self.sg3db.MeasurementFileName)
                    pl.grid(True)
                    pl.xlabel('distance [km]')
                    pl.ylabel('height [m]')
                # # plot the position of transmitter/receiver
                hTx=self.sg3db.hTx
                hRx=self.sg3db.hRx
                if flag_plot:
                    ax=pl.gca()
                if measID!=[]:
                    if (measID>len(hRx)) or (measID < 0):
                        raise ValueError('The chosen dataset does not exist.')
                    self.sg3db.userChoiceInt=measID
                    # this will be a separate function
                        # Transmitter
                    if flag_plot:
                        if (self.sg3db.first_point_transmitter == 1):
                            pl.plot(np.array([ x[0], x[0]]), np.array([h_gamsl[0], h_gamsl[0]+ hhTx]),linewidth = 2, color = 'b')
                            pl.plot(x[0], h_gamsl[0]+hTx[0], marker='v',color='b')
                            pl.plot(np.array([ x[-1], x[-1]]), np.array([h_gamsl[-1],h_gamsl[-1]+hhRx]),linewidth = 2,color = 'r')
                            pl.plot(x[-1], h_gamsl[-1]+hhRx, marker = 'v',color = 'r')
                        else:
                            pl.plot(np.array([ x[-1], x[-1]]), np.array([h_gamsl[-1],h_gamsl[-1]+hhTx]),linewidth = 2,color ='b')
                            pl.plot(x[-1], h_gamsl[0]+hTx[0], marker='v',color  ='b')
                            pl.plot(np.array([ x[0], x[0] ]), np.array([h_gamsl[0],h_gamsl[0]+hhRx]),linewidth = 2,color = 'r')
                            pl.plot(x[0], h_gamsl[0]+hhRx, marker = 'v',color = 'r')
                        ax = pl.gca()
                if measID!=[]:    
                    #if(get(handles.heffCheck,'Value'))
                    heff=P1546.heffCalc(x,h_gamsl,hhTx)
                    self.sg3db.heff = heff
                    # compute the terrain clearance angle
                    tca = P1546.tcaCalc(x,h_gamsl,hhRx,hhTx)
                    self.sg3db.tca = tca
                    if flag_plot:
                        P1546.plotTca(ax,x,h_gamsl,hhRx,tca)
                    # compute the terrain clearance angle at transmitter side
                    teff1 = P1546.teff1Calc(x,h_gamsl,hhTx,hhRx)
                    self.sg3db.eff1 = teff1
                    if flag_plot:
                        P1546.plotTeff1(ax,x,h_gamsl,hhTx,teff1)
                    # plot the average height above the ground
                    if flag_plot:
                        x1=x[0]
                        x2=x[-1]
                        if x2 > 15:
                            x2=15
                        yy=ax.get_ylim()
                        dy=yy[1]-yy[0]
                        y1=hhTx+h_gamsl[0]-heff
                        y2=y1
                        pl.plot(np.array([x1, x2]), np.array([y1, y2]),color = 'r')
                        if x[-1] < 15:
                            pl.text((x1+x2)/2,y1+0.05*dy,'hav(0.2d,d) = '+ str(y1))
                        else:
                            pl.text(x2,y1+0.05*dy,'hav(3,15) = ' + str(y1))
                        #pl.show()   
                        pl.draw()
                        pl.pause(0.01)
                        #input("Press [enter] to continue.")
                # Execute P.1546
                fid_log=-1
                if flag_debug==1:
                    filename2 = out_dir + filename1[0:-4] + '_' + str(measID) + '_log.csv'
                    fid_log = open(filename2, 'w')
                    if (fid_log == -1):
                        error_str = filename2 + ' cannot be opened.'
                        raise IOError(error_str)
                self.sg3db.fid_log=fid_log
                self.sg3db.wa=wa
                self.sg3db=P1546.Compute(self.sg3db)
                if flag_debug==1:
                    fid_log.close()
                    # print the deviation of the predicted from the measured value,
                    # double check this line
                    # Measurement folder | Measurement File | Dataset | Measured Field Strength | Predicted Field Strength | Deviation from Measurement
                    fid_all.write(' %s, %s, %d, %.8f, %.8f, %.8f\n' % (self.sg3db.MeasurementFolder,self.sg3db.MeasurementFileName,measID, self.sg3db.MeasuredFieldStrength[measID], self.sg3db.PredictedFieldStrength, self.sg3db.PredictedFieldStrength - self.sg3db.MeasuredFieldStrength[measID]))
        def Loss(self):
            return self.sg3db.PredictedTransmissionLoss
        def E(self):
            """
            ERP kW-hoz
            """
            self.Szamol()
            return self.sg3db.PredictedFieldStrength #self.RadioLink.E(self.Loss(),ERPkW)
        def CheckModel(self):
            return (self.RadioLink.f>=30) and (self.RadioLink.f<=4000) and (self.RadioLink.dkm>=1) and (self.RadioLink.dkm<=1000),"30MHz <= f <=4000MHz and 1km <= d <= 1000km"
    class ITM(object):
        ERadioClimate=["Unknown","Equatorial","Continental_Subtropical","Maritime_Tropical","Desert","Continental_Temperate","Maritime_Temperate_on_Over_Land","Maritime_Temperate_on_Over_Sea"]
        EMode=["Unknown","Line_Of_Sight","Single_Horizon","Double_Horizon","Double_Horizon_Diffraction_Dominant","Double_Horizon_Troposcatter_Dominant"]#Terjedési mód visszaadott érték
        def __init__(self, **kwargs):
            """
            RadioLink vagy
            MHz, dkm
            """
            if "RadioLink" in kwargs: self.RadioLink = kwargs["RadioLink"]
            else: self.RadioLink = Propagation.RadioLink()
            if "MHz" in kwargs: self.RadioLink.f = kwargs["MHz"]
            if "dkm" in kwargs: self.RadioLink.set_dkm(kwargs["dkm"])
            self.Mode = 0
        def LossPP(self):
            #DEFINE MAIN USER PARAMETERS
            #Define an empty dict for user defined parameters
            mup = {} 
            mup['fmhz']  =  self.RadioLink.f   #Define radio operating frequency (MHz)
            mup['d'] = self.RadioLink.dkm      #Define distance between terminals in km (from Longley Rice docs)
            mup['hg'] = [self.RadioLink.Transmitter.m, self.RadioLink.Receiver.m]  #Define antenna heights - Antenna 1 height (m) # Antenna 2 height (m)
            mup['ipol'] = self.RadioLink.Pol    #Polarization selection (0=horizontal, 1=vertical)
            if len(self.RadioLink.Terep.Profile)==0: self.RadioLink.Terep.readProfile()
            output = self.itmlogic_p2p(mup)
            #Select Case prop.kwx
            # Case 0 #No Error.
            # Case 1
            # Throw New Class_PropagationError("Warning: Some parameters are nearly out of range.  Results should be used with caution.")
            # Case 2
            # Throw New Class_PropagationError("Note: Default parameters have been substituted for impossible ones.")
            # Case 3
            # Throw New Class_PropagationError("Warning: A combination of parameters is out of range.  Results are probably invalid.")
            # Case Else
            # Throw New Class_PropagationError("Warning: Some parameters are out of range.  Results are probably invalid.")
            #End Select
            return output
        def itmlogic_p2p(self, mup):
            """
            Run itmlogic in point to point (p2p) prediction mode.
            mup : dict
            surface_profile_m : list Contains surface profile measurements in meters.
            Returns
            output : list of dicts Contains model output results.
            """
            prop = mup
            #DEFINE ENVIRONMENTAL PARAMETERS
            prop['eps'] = 15.   #Terrain relative permittivity
            prop['sgm'] = 0.005 #Terrain conductivity (S/m)
            prop['klim'] = 5    #Climate selection (1=equatorial, 2=continental subtropical, 3=maritime subtropical, 4=desert, 5=continental temperate, 6=maritime temperate overland, 7=maritime temperate, oversea (5 is the default)
            prop['ens0'] = 314  #Surface refractivity (N-units): also controls effective Earth radius
            #DEFINE STATISTICAL PARAMETERS
            qc = [50.]          #Confidence  levels for predictions
            qr = [50.]          #Reliability levels for predictions
            pfl = []            #Number of points describing profile -1
            pfl.append(len(self.RadioLink.Terep.Profile) - 1)
            pfl.append(self.RadioLink.Terep.dl)
            pfl.extend(self.RadioLink.Terep.Profile)
            # Refractivity scaling ens=ens0*exp(-zsys/9460.)
            zsys = 0            #(Average system elev above sea level)
            # Note also defaults to a continental temperate climate
            # Setup some intermediate quantities
            prop['lvar'] = 5    # Initial values for AVAR control parameter: LVAR=0 for quantile change, 1 for dist change, 2 for HE change, 3 for WN change, 4 for MDVAR change, 5 for KLIM change
            prop['gma'] = 157E-9# Inverse Earth radius
            db = 8.685890       # Conversion factor to db
            nc = len(qc)        #Number of confidence intervals requested
            nr = len(qr)        #Number of reliability intervals requested
            dkm = prop['d']     #Length of profile in km
            prop['pfl'] = pfl   #Store profile in prop variable
            prop['kwx'] = 0     #Zero out error flag
            
            prop['wn'] = prop['fmhz'] / 47.7    #Initialize omega_n quantity
            prop['ens'] = prop['ens0']  #Initialize refractive index properties
            if zsys != 0: prop['ens'] = prop['ens'] * math.exp(-zsys / 9460) #Scale this appropriately if zsys set by user
            prop['gme'] = prop['gma'] * (1 - 0.04665 * math.exp(prop['ens'] / 179.3)) #Include refraction in the effective Earth curvature parameter
            zq = complex(prop['eps'], 376.62 * prop['sgm'] / prop['wn'])    #Set surface impedance Zq parameter
            if prop['ipol'] == 0: prop['zgnd'] = np.sqrt(zq - 1) #Set Z parameter (h pol)
            else: prop['zgnd'] = prop['zgnd'] / zq  #Set Z parameter (v pol)
            
            prop['klimx'] = 0   #Flag to tell qlrpfl to set prop.klim=prop.klimx and set lvar to initialize avar routine
            prop['mdvarx'] = 11 #Flag to tell qlrpfl to use prop.mdvar=prop.mdvarx and set lvar to initialize avar routine
            zr = qerfi([x / 100 for x in qr])   #Convert requested reliability levels into arguments of standard normal distribution
            zc = qerfi([x / 100 for x in qc])   #Convert requested confidence levels into arguments of standard normal distribution
            #Initialization routine for point-to-point mode that sets additional parameters of prop structure
            prop = qlrpfl(prop)
            # Here he = effective antenna heights, dl = horizon distances, the = horizon elevation angles
            # mdvar = mode of variability calculation: 0=single message mode, 1=accidental mode, 2=mobile mode, 3 =broadcast mode, +10 =point-to-point, +20=interference
            fs = db * np.log(2 * prop['wn'] * prop['dist']) #Free space loss in db
            q = prop['dist'] - prop['dlsa'] #Used to classify path based on comparison of current distance to computed line-of-site distance
            q = max(q - 0.5 * pfl[1], 0) - max(-q - 0.5 * pfl[1], 0)    #Scaling used for this classification
            #Report dominant propagation type predicted by model according to parameters obtained from qlrpfl
            if q < 0: self.Mode = 1
            elif q == 0: self.Mode = 2
            else: self.Mode = 3
            if prop['dist'] <= prop['dlsa']: self.Mode = 4
            elif prop['dist'] > prop['dx']: self.Mode = 5
            avar1, prop = avar(zr[0], 0, zc[0], prop)
            return fs+avar1

            #print('Confidence levels {}, {}, {}'.format(str(qc[0]), str(qc[1]), str(qc[2])))

            ## Confidence  levels for predictions
            #qc = [50, 90, 10]

            ## Reliability levels for predictions
            #qr = [1, 10, 50, 90, 99]

            #output = []
            #for jr in range(0, (nr)):
            #    for jc in range(0, nc):
            #        #Compute corrections to free space loss based on requested confidence
            #        #and reliability quantities
            #        avar1, prop = avar(zr[jr], 0, zc[jc], prop)
            #        output.append({
            #            'dkm': prop['d'],
            #            'rel': qr[jr],
            #            'con': qc[jc],
            #            'loss': fs + avar1 #Add free space loss and correction
            #            })
            #return output
        def E(self):
            """
            Szabadtéri csillapítással számított térerősség izotróp antennán, dipólon nagyobb kToDipol-lal
            """
            return self.RadioLink.E(self.LossPP(),self.RadioLink.ERPkW)
        def CheckModel(self):
            return (self.RadioLink.f>=20) and (self.RadioLink.f<=40000) and (self.RadioLink.dkm>=1) and (self.RadioLink.dkm<=2000),"20MHz <= f <=4000MHz and 1km <= d <= 2000km"