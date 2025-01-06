# -*- coding: utf-8 -*-
import datetime
from dateutil import tz
from qgis import *
from qgis.core import (
    QgsProject,QgsPoint,QgsPointXY,
    QgsCoordinateReferenceSystem,QgsCoordinateTransform)
import math
R = 6379743.001
wgscrs=QgsCoordinateReferenceSystem("EPSG:4326")
eovcrs=QgsCoordinateReferenceSystem("EPSG:23700")
wgstoeov=QgsCoordinateTransform(wgscrs,eovcrs,QgsProject.instance().transformContext())
class WorldPoint(object):
    """
    qwp=TeleDeLuxe.WorldPoint(TeleDeLuxe.EOV(250000,648000))
    print("EOVx="+str(qwp.EOV.x)+" EOVy="+str(qwp.EOV.y)+" EOVz="+str(qwp.EOV.z))
    print("Lon="+str(qwp.WGS.Lon.get_asFloat())+" Lat:"+str(qwp.WGS.Lat.get_asFloat()))

    qwp=TeleDeLuxe.WorldPoint(TeleDeLuxe.WGS(19.0208496721,47.5938759095))
    print("EOVx="+str(qwp.EOV.x)+" EOVy="+str(qwp.EOV.y)+" EOVz="+str(qwp.EOV.z))
    print("Lon="+str(qwp.WGS.Lon.get_asFloat())+" Lat:"+str(qwp.WGS.Lat.get_asFloat()))

    nap=qwp.Nap()
    print(nap)

    EOVx=250000 EOVy=648000 EOVz=0.0
    Lon=19.0208496721 Lat:47.5938759095
    EOVx=249999.986511 EOVy=647999.999994 EOVz=0.0
    Lon=19.0208496721 Lat:47.5938759095
    {'Nyugta': datetime.datetime(2021, 11, 17, 16, 7, 16, 519217, tzinfo=tzlocal()), 'Kelte': datetime.datetime(2021, 11, 17, 6, 53, 22, 348003, tzinfo=tzlocal())}
    """
    def __init__(self, *args, **kwargs):
        """
        Egymással szinkronizált WGS, EOV koordinátái és 
        földfelszín fölötti magassága van.
        args:
        WGS = az új pont WGS koordinátái
        EOV = az új pont EOV koordinátái
        
        példák:
        wp=WorldPoint(WGS=[18.889903,47.413658,30])
        wp=WorldPoint(EOV=[544107,190373,30])#Kab-hegy
        wp=WorldPoint(EOV=[638111.311184874,229976.00320334017,30])
        print("WGS:",wp.WGS)
        print("EOV:",wp.EOV)
        print(wp.WGS.x(),wp.WGS.y(),wp.WGS.z())
        print(wp.EOV.x(),wp.EOV.y(),wp.EOV.z())
        print(wp._value.asWkt())
        v=WorldPoint(EOV=[642167,202726,10])
        print("v pont távolsága = ",wp.Distance(v),"m")
        print("v pont iránya = ",wp.Azimuth(v),"°")
        print("v pont elevációja = ",wp.Elevation(v),"°")
        print(wp.Nap())
        print(wp.LineOfSight())
        """
        if "WGS" in kwargs:
            self._value=QgsPoint(kwargs["WGS"][0],kwargs["WGS"][1],kwargs["WGS"][2])
            self.set_WGS(self._value)
        elif "EOV" in kwargs:
            self._value=QgsPoint(kwargs["EOV"][0],kwargs["EOV"][1],kwargs["EOV"][2])
            self.set_EOV(self._value)
        else:
            self._value=QgsPoint()
        if "m" in kwargs:
            self.m=kwargs["m"]
        else: self.m=30
    def set_WGS(self,newWGS):
        self.WGS=newWGS
        self.EOV=self._toEOV(newWGS)
    def set_EOV(self,newEOV):
        self.EOV=newEOV
        self.WGS=self._toWGS(newEOV)
    def addToEOV(self,dx,dy):
        self.EOV.setX(self.EOV.x()+dx)
        self.EOV.setY(self.EOV.y()+dy)
        self.WGS=self._toWGS(self.EOV)
    def _toEOV(self,WGS):
        q=wgstoeov.transform(QgsPointXY(WGS.x(),WGS.y()))
        eov=QgsPoint(q.x(),q.y(),WGS.z())
        return eov
    def _toWGS(self,EOV):
        q=wgstoeov.transform(QgsPointXY(EOV.x(),EOV.y()),QgsCoordinateTransform.ReverseTransform)
        wgs=QgsPoint(q.x(),q.y(),EOV.z())
        return wgs
    def Distance(self,WorldPoint):
        return self.EOV.distance(WorldPoint.EOV)
    def Azimuth(self,WorldPoint):
        return (self.EOV.azimuth(WorldPoint.EOV)+360) % 360
    def Elevation(self,WorldPoint):
        return math.degrees(math.atan2(WorldPoint.EOV.z()-self.EOV.z(),self.Distance(WorldPoint)))
    def Nap(self,Datum=datetime.datetime.now()):
        n=(Datum-datetime.datetime(2000,1,1)).days-(-self.WGS.x()/360)-0.0009#+ 2451545
        J=2451545.0009+(-self.WGS.x()/360)+round(n)
        M=(357.5291+0.98560028*(J-2451545))%360
        Mrad=math.radians(M)
        C=(1.9148*math.sin(Mrad))+(0.02*math.sin(2*Mrad))+(0.0003*math.sin(3*Mrad))
        la=(M+102.9372+C+180)%360
        larad=math.radians(la)
        Jt=J+(0.0053*math.sin(Mrad))-(0.0069*math.sin(2*larad))
        derad=math.asin(math.sin(larad)*math.sin(math.radians(23.45)))
        Hrad=math.acos((math.sin(math.radians(-0.83))-math.sin(math.radians(self.WGS.y()))*math.sin(derad))/(math.cos(math.radians(self.WGS.y()))
        *math.cos(derad)))
        H=math.degrees(Hrad)
        Jha=2451545.0009+((H-self.WGS.x())/360)+round(n)
        Jset=Jha+(0.0053*math.sin(Mrad))-(0.0069*math.sin(2*larad))
        Jrise=2*Jt-Jset
        kel = (datetime.datetime(2000,1,1) + datetime.timedelta(seconds=(Jrise - 2451545) * 86400 + 12 * 3600)).replace(tzinfo=tz.tzutc())
        nyug=(datetime.datetime(2000,1,1)+datetime.timedelta(seconds=(Jset-2451545)*86400+12*3600)).replace(tzinfo=tz.tzutc())
        return {"Kelte":kel.astimezone(tz.tzlocal()),"Nyugta":nyug.astimezone(tz.tzlocal())}
    def RasterEOV(self,RasterSize): #RasterSize [m] méretű rácsra húzott EOV koordinátát ad vissza
        return EOV(round(self.EOV.x()/RasterSize)*RasterSize,round(self.EOV.y()/RasterSize)*RasterSize)
    def LineOfSight(self): #Optikai látótávolság
        return math.sqrt(2*R*self.EOV.z())
    #def __eq__(self,WorldPoint):
    #    if self!=None:
    #        return (self._value==WorldPoint._value)
    #    else:
    #        return False