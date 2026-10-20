# -*- coding: utf-8 -*-

import math 
from CoolProp.CoolProp import PropsSI
from pint import UnitRegistry
ureg = UnitRegistry()
Q_ = ureg.Quantity



pb=30e6
pbb=pb/100000 #bars

pr=10e6
prb=pr/100000 #bars




wo=0.18
wf=0.056
wt=wo+wf

v=30 #m/s
n2=6950
gf=0.967 #specific gravity
t=298

#for q calculations
tq= 15.5 #degrees celsius
tqk= ureg.convert(tq, "celsius", "kelvin")
pq=101.3e3
rhoq= PropsSI('D', 'T', tqk, 'P', pq, 'Nitrogen') #density at standard conditions


rhob= PropsSI('D', 'T', t, 'P', pb, 'Nitrogen') #density at 300Bar
rhor= PropsSI('D', 'T', t, 'P', pr, 'Nitrogen')#density at 100Bar

"""OUTPUTS"""
"""Pipe Diameters"""
at=wt/(rhob*v)#flow area out of bottle

ao=wo/(rhor*v)#flow area into oxidiser

af=wf/(rhor*v)#flow area into fuel

dt=2*(math.sqrt((at/3.14)))
do=2*(math.sqrt((ao/3.14)))
df=2*(math.sqrt((af/3.14)))

dtmm=dt*1000
domm=do*1000
dfmm=df*1000

print("Pipe Diameter Before Regulator(mm)=", dtmm)
print("Pipe Diameter Before N2O Tank(mm)=", domm)
print("Pipe Diameter Before Fuel Tank(mm)=", dfmm)

"""CVs"""
qt=(wt*60)/(rhoq/1000)
qo=(wo*60)/(rhoq/1000)
qf=(wf*60)/(rhoq/1000)

cvt=qt/(n2*0.471*pbb*(math.sqrt(1/(gf*t))))
cvo=qo/(n2*0.471*prb*(math.sqrt(1/(gf*t))))
cvf=qf/(n2*0.471*prb*(math.sqrt(1/(gf*t))))

print("CV Before Regulator=", cvt)
print("CV Before N20 Tank=", cvo)
print("CV Before Fuel Tank=", cvf)