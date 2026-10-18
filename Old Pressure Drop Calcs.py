# -*- coding: utf-8 -*-

import math 

"""
INPUTS
"""
"""Fluid Properties"""
fluid=1 #1 for nitrous, 2 for ipa

if fluid==1:
    mu=1.47e-5 #dynamic viscosity(Pa s)
    rho=833
    gf = 1.266 #specific gravity
else:
    mu=1.47e-5 #dynamic viscosity(Pa s)
    rho=1230.458
    gf = 1.266 #specific gravity
    
v=10#fluid velocity

tp=10e6 #tank pressure in pascals a guess
tpb=tp/100000 #tank pressure bars

"""Constants"""
n1=14.42
k=10
g=9.81 #gravity

"""Piping Factors"""
bends=10 #number of bends
l=4 #length of piping(m)
d=0.0127 #pipe diameter(m)
vn=2 #number of valves

"""Engine Properties"""
pc=4e6 #chamber pressure in pascals
pcb=pc/100000 #chamber pressure bars
w=2.13#mass flow rate

"""
OUTPUTS
"""
"""DYNAMIC PRESSURE LOSS"""
dpl=0.5*rho*(v**2)

"""FRICTION PRESSURE LOSS"""

"""Reynolds Number"""
nu=mu/rho #kinematic viscosity

re=(d*v)/nu #reynolds number

"""Friction Factor"""
if re<=2000:
    f=64/re
    if re >=4000 and re <= 10000:
        f=0.3154/(re**0.237)
elif re>10000:
    f=0.0032+(0.221/(re**0.237))
    
"""Darcy Wesibach"""  
dw=(f*l*(rho/2)*(v**2))/(d)      


"""Pressure Loss in Bends"""
bpl=f*(k*(v**2))/(2*g)
tbpl=bpl*bends


"""REGEN PRESSURE LOSS"""
rpl=0.2*pc

"""INJECTOR PRESSURE DROP"""
ipl=0.2*pc


"""TOTAL PRESSURE LOSS WITHOUT VALVES"""
tpl=ipl+rpl+tbpl+dpl+dw
tplb=tpl/100000 #pressure loss in bars
print("Total Pressure Loss Less valves=", tplb)

"""COMPONENT PRESSURE LOSS"""
injp=ipl+pc #minimum pressure at the injector face
satp=5.5e6 #nitrous saturation pressure in pascals

if fluid ==1:
    minp=satp
else: minp=injp
        

tva=tp-tpl-minp #valve allowance
tvab= tva/100000 #valves pressure allowance bars

va=tva/vn #per valve
print("Pressure Loss in Valves=", tvab)

"""VALVE CV CALCULATIONS"""
vab= va/100000 #valve pressure allowance bars

q=(w*60)/(rho/1000) #flowrate in litres/min

cv=q/(n1*math.sqrt((vab/gf)))
print("Valve CV=", cv)
