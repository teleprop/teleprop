# -*- coding: utf-8 -*-
import io
from . import GeoCoord
import os
import math
class Terrain(object):
    """
    """
    _DTMdir = "c:/Term/Adat/dtm/"
    TerepResolution_m = 0
    kiterj = [".20m", ".04m", ".01m"]
    felbmeter = [1000., 200., 50.]
    felbdarab = [[33, 49],[161, 241], [641, 961]]
    def __init__(self,newResolution,newRadioLink):
        """
        newResolution 0=1000m, 1=200m, 2=50m
        """
        self.DTMdir = self._DTMdir
        self.resolution = newResolution
        self.Profile=[]
        self.RadioLink=newRadioLink
    #Public Property DTMdir As String
    #    Get
    #        Return pDTMdir
    #    End Get
    #    Set(value As String)
    #        If My.Computer.FileSystem.DirectoryExists(value) Then pDTMdir =
    #        value
    #    End Set
    #End Property
    def WGSMagassag(self,WGS):
        qEOV = WGS.toEOV()
        self.EOVMagassag(qEOV)
        WGS.Elev = qEOV.z
    def EOVMagassag(self,EOV):
        """
        A pont magasságának feltöltése adatbázisból.
        EOV A pont EOV koordinátája.
        A pont EOV.z elemének ad értéket.
        """
        mag = 150 #311094;823814;512
        ba = GeoCoord.EOV() #a betöltött magassági térkép sarokpontja
        ba.x = 32000 * int(EOV.x / 32000)
        ba.y = 48000 * int(EOV.y / 48000)
        s ="{0:.0f}{1:.0f}{2}".format(ba.y / 1000,ba.x/1000,self.kiterj[self.resolution])
        if os.path.exists(self.DTMdir + s):
            with io.open(self.DTMdir + s,'rb') as br:
                q=int(2*(self.felbdarab[self.resolution][1]*((ba.x+32000-EOV.x)//self.get_Resolution_m())+(EOV.y-ba.y)//self.get_Resolution_m()))
                br.seek(q,0)
                mag = ord(br.read(1)) + ord(br.read(1)) * 256
        else:
            mag = 150
        EOV.z = mag
    def MagKorr(self,d,d1):
        """
        A pont magasságának korrigálása fizikai Földgörbülettel.
        d Az összeköttetés távolsága.
        d1 A kérdéses pont távolsága az adótól mérve.
        return A magasságkorrekció méterben.
        Ennyivel "púposodik föl" a terep Föld görbülete miatt a vízszinteshez képest.
        """
        mk = 0
        if d > d1:
            s = 2 * GeoCoord.R * math.sin(d / (2 * GeoCoord.R))
            q = d1 ** 2 - ((s ** 2 + d1 ** 2 - (d - d1) ** 2) / (2 * s)) ** 2
            if q <= 0: mk = 0
            else: mk = math.sqrt(q)
        return mk    
    def get_Resolution_m(self):
        """
        A terepmodell felbontása.
        return A felbontás méterben, általában 50 m.
        """
        return self.felbmeter[self.resolution]
    def get_Resolution_km(self):
        """
        A terepmodell felbontása.
        return A felbontás méterben, általában 0.050 km.
        """
        return self.felbmeter[self.resolution] / 1000
    def readProfile(self,Foldgorbulet):
        """
        Az adó és a vevőpont között terepmetszet.
        Metszet A terepmetszetet tároló tömb.
        Foldgorbulet A földgörbület figyelembe vételét kapcsolja be.
        """
        p = GeoCoord.EOV()
        self.WGSMagassag(self.RadioLink.Transmitter.WGS)
        self.WGSMagassag(self.RadioLink.Receiver.WGS)
        self.RadioLink.Receiver.EOV.z=self.RadioLink.Receiver.WGS.Elev
        voltResolution = self.resolution
        if self.RadioLink.dkm < 50:
            self.resolution = 2
        elif (self.RadioLink.dkm >= 50) and (self.RadioLink.dkm < 200):
            self.resolution = 1
        else:
            self.resolution = 0
        ir = self.RadioLink.Receiver.WGS.Azimuth(self.RadioLink.Transmitter.WGS)
        dx = self.get_Resolution_m() * math.cos(math.radians(ir))
        dy = self.get_Resolution_m() * math.sin(math.radians(ir))
        self.Profile = []
        p = self.RadioLink.Transmitter.WGS.toEOV()
        self.EOVMagassag(p)
        for i in range(0,int(0.5 + self.RadioLink.d / self.get_Resolution_m()) + 1):
            p.x = p.x + dx 
            p.y = p.y + dy 
            self.EOVMagassag(p)
            self.Profile.append(p.z)
            if Foldgorbulet: self.Profile[-1] += self.MagKorr((self.RadioLink.d / self.get_Resolution_m()) * self.get_Resolution_m(), i * self.get_Resolution_m())
        self.TerepResolution_m = self.felbmeter[self.resolution]
        self.resolution = voltResolution
    #Public Function Lathato(EzaPont As Class_GeoCoord.Class_EOV) As Boolean
    #    Dim al As Double, d1 As Double, d2 As Double, h1 As Double, h2 As
    #    Double
    #    Dim HH As Double
    #    Dim pv As New Class_GeoCoord.Class_EOV
    #    Dim i As Long, qlathato As Boolean
    #    Dim dx As Double, dy As Double, del As Double
    #    Dim adoEOV As New
    #    Class_GeoCoord.Class_EOV(self.RadioLink.Transmitter.WGS.toEOV)
    #    al = adoEOV.Azimuth(EzaPont)
    #    d2 = adoEOV.Distance(EzaPont)
    #    dx = 50 * Math.Cos(al * pip180) : dy = 50 * Math.Sin(al * pip180)
    #    del = Math.Sqrt(dx ^ 2 + dy ^ 2)
    #    pv.x = EzaPont.x : pv.y = EzaPont.y : EOVMagassag(pv)
    #    EOVMagassag(adoEOV)
    #    h1 = adoEOV.z + self.RadioLink.Transmitter.AboveGround
    #    h2 = pv.z + self.RadioLink.Receiver.AboveGround
    #    i = 1 : d1 = 50 : qlathato = True
    #    HH = (h2 - h1) / d2
    #    While qlathato And (d1 <= d2)
    #        pv.x = adoEOV.x + i * dx
    #        pv.y = adoEOV.y + i * dy
    #        d1 = adoEOV.Distance(pv)
    #        EOVMagassag(pv)
    #        pv.z = pv.z + MagKorr(d2, i * del)
    #        qlathato = ((pv.z - h1) / d1) < HH
    #        i = i + 1
    #    End While
    #    Lathato = qlathato
    #End Function
    #'Public Shared Sub Probaheff()
    #' 'Adó 258351,546313,127
    #' 'Vevő 250015,501642
    #' 'heff = 127
    #' Dim tm As New Class_Terrain("c:\Term\Adat\dtm\",Enum_Resolution.Res_50m)
    #' tm.RadioLink = New Class_Propagation.Class_RadioLink
    #' tm.RadioLink.Transmitter = New Class_GeoCoord.Class_WorldPoint(New
    #Class_GeoCoord.Class_EOV(258351, 546313), 127)
    #' tm.RadioLink.Receiver = New Class_GeoCoord.Class_WorldPoint(New
    #Class_GeoCoord.Class_EOV(250015, 501642), 10)
    #' Debug.Print(tm.Heff)
    #'End Sub
