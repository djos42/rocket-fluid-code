# -*- coding: utf-8 -*-

import math 

from rocketprops.line_supt import calc_line_id_dp, calc_line_vel_dp
from rocketprops.rocket_prop import get_prop
from rocketprops.valve_supt import cv_valve_dp

from pint import UnitRegistry
ureg = UnitRegistry()
Q_ = ureg.Quantity

from CoolProp.CoolProp import PropsSI

"""Inputs"""
l=2 #line length in metres
lin= ureg.convert(l, "metres", "inch")   #metres to inches
w= 2.13
wpps= ureg.convert(w, "kg/s", "lb/s")   #kg/s to freedom units
v=10 
vfts= ureg.convert(v, "m/s", "ft/s")#m/s to football pitches per eagle cry

p= 100 #tank pressure in bar
ppa=ureg.convert(p, "bar", "pascal") #tank pressure in pascals
ppsi= ureg.convert(p, "bar", "psi")#bar to mountain dew per daytona
t= 15 #degrees celsius
tk= ureg.convert(t, "celsius", "kelvin") #celsius to kelvin
tr= ureg.convert(t, "celsius", "rankine") #celsius to John Cena per wendys
rough=1.4 #microns from https://www.swagelok.com/-/media/distributor-media/a-b/alfl/documents/swagelok-tubing-quality.ashx 
roughin=ureg.convert(rough, "micron", "inch") #microns to cadillac per a lifted truck


k=0.75 #for a 90 degree bend from https://neutrium.net/articles/fluid-flow/pressure-loss-from-fittings-excess-head-k-method/
bends=6 #guess at number of bends

kbend=k*bends

ind=0.5 - (2*0.049) #pipe inner diameter for a 1/2" tube as per https://www.swagelok.com/downloads/webcatalogs/en/ms-01-107.pdf

'''Line Pressure Drop'''
pObj = get_prop('N2O')

'''ID, deltaP = calc_line_id_dp( pObj, TdegR=tr, Ppsia=ppsi,
                              wdotPPS=wpps, velFPS=vfts,
                              roughness=roughin,  Kfactors=kbend, len_inches=lin)
#print( 'Inside Diam=%g inches, Pressure Drop =%g psid'%(ID, deltaP) )'''

vel, dp = calc_line_vel_dp( pObj, TdegR=tr, Ppsia=ppsi,
                 wdotPPS=wpps, IDinches=ind,
                 roughness=roughin,  Kfactors=kbend, len_inches=lin)
print( 'Velocity = %g ft/sec, Pressure Drop =%g psid'%(vel, dp) )

fv= ureg.convert(vel, "ft/s", "m/s") #flow velocity in m/s
dpbarl= ureg.convert(dp, "psi", "bar") #line pressure loss in Bar

print( 'Fluid Velocity = %g m/sec, Pressure Drop =%g bar\n'%(fv, dpbarl) )

'''Dynamic Pressure Loss'''
rho = PropsSI('D', 'T', tk, 'P', ppa, 'N2O')
dpl=0.5*rho*(fv**2) #pa

dplbar=ureg.convert(dpl, "pascal", "bar") 
dplpsi=ureg.convert(dpl, "pascal", "psi")

print( 'Dynamic Pressure Loss =%g bar\n'%(dplbar) )

"""Valve Pressue Drops"""
'''inputs'''
mvcv=2 #main valve cv
cvcv= 1.1 #check valve cv
fcv= 1 #filter cv

'''Filter'''
'''dpf = cv_valve_dp( pObj, Cv=fcv, wdotPPS=wpps, TdegR=tr, Ppsia=ppsi)
dpbarf= ureg.convert(dpf, "psi", "bar") #mainvalve pressure loss in Bar
print('deltaP for Filter = %g psid'%dpf)
print('deltaP for Filter = %g bar\n'%dpbarf)'''

'''Main Valve'''
dpmv = cv_valve_dp( pObj, Cv=mvcv, wdotPPS=wpps, TdegR=tr, Ppsia=(ppsi-dplpsi))
dpbarmv= ureg.convert(dpmv, "psi", "bar") #mainvalve pressure loss in Bar
print('deltaP for Main Valve = %g psid'%dpmv)
print('deltaP for Main Valve = %g bar\n'%dpbarmv)

'''Check Valve'''
dpcv = cv_valve_dp( pObj, Cv=cvcv, wdotPPS=wpps, TdegR=tr, Ppsia=(ppsi-dpmv-dplpsi))
dpbarcv= ureg.convert(dpcv, "psi", "bar") #mainvalve pressure loss in Bar
print('deltaP for Check Valve = %g psid'%dpcv)
print('deltaP for Check Valve = %g bar\n'%dpbarcv)



dpbarv=dpbarmv + dpbarcv 

dpfm=0 #flowmeter pressure loss in bar

tpl=dplbar+dpbarv+dpbarl+dpfm #total pressure loss
print( 'Total Pressure Loss = %g bar\n'%(tpl) )


