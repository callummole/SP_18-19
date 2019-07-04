# Computes (approximation) of yaw rate offset to TLC on a
# circular trajectory. The result is quite nasty, at least
# with Sympy. We get a solution only for TLC to yaw rate offset
# and invert it in a range using interpolation.

from sympy import *
import numpy as np
import matplotlib.pyplot as plt

var("v r", real=True, positive=True, nonzero=True)
var("t", real=True, positive=True)
var("g", nonzero=True, real=True)
var("b", real=True, positive=True)
var("w", real=True, negative=True)
var("x y a", real=True, cls=Function)

var("b", real=True, negative=True)
var("w", real=True, positive=True)

def small_angle_approx(e):
    x = symbols("x")
    mappings = {
        cos: 1 - x**2/2,
        acos: sqrt(-2*x + 2),
        sin: x,
        asin: x
    }
    return e.replace(
            lambda e: e.func in mappings,
            lambda e: mappings[e.func].subs({x: e.args[0]})
            )



g = v/r + b
da = g
a = dsolve(
        Eq(Derivative(a(t)), da),
        a(t), ics={a(0): 0})
a = a.rhs
a = simplify(a)

dx = sin(a)*v
x = dsolve(
        Eq(Derivative(x(t)), dx),
        x(t), ics={x(0): -r}
        ).rhs
#x = x.simplify().args[0][0].simplify() # A HACK!

dy = cos(a)*v
y = dsolve(
        Eq(Derivative(y(t)), dy),
        y(t), ics={y(0): 0}
        ).rhs
y = simplify(y)
#y = y.args[0][0].simplify() # A HACK!

def plotit(bias=0):

    ts = np.linspace(0, 60, 100)
    radius = 80
    speed = 8
    rate = speed/radius
    xs = lambdify((t, v, r, b), x)(ts, speed, radius, bias)
    ys = lambdify((t, v, r, b), y)(ts, speed, radius, bias)
    plt.plot(xs, ys)

sdist = (y**2 + x**2)

sdist = simplify(sdist)
critical = Eq(sdist, (r + w)**2).simplify()
critical = small_angle_approx(critical).simplify()
pprint(critical)
b_to_tlc = solve(critical, t)[-1].simplify()
#b_to_tlc = solve(critical, t)[1].simplify()
b_to_tlc = sqrt(w*(2*r - sign(b)*w)/(abs(b)*r*v))
pprint("WTF")
pprint(b_to_tlc)
pprint("Solution")
print(solve(Eq(b_to_tlc, t), b))

pos = b_to_tlc.subs({r: 80, v: 8, w: -1.5})
pos = pos.simplify()
neg = b_to_tlc.subs({r: 80, v: 8, w: -1.5})
neg = neg.simplify()


b_to_tlc = Piecewise(
        (np.inf, Eq(b, 0)),
        (pos, b > 0),
        (neg, b < 0)
        )

import mpmath
from mpmath import chebyfit
approx = chebyfit((lambdify(b, b_to_tlc, "mpmath")), np.radians([-10, 10]), 50)

b_to_tlc = lambdify(b, b_to_tlc)
rng = np.deg2rad(np.linspace(-10, 10, 1000))
a = (np.array(mpmath.polyval(approx, rng), dtype=float))
plt.plot(np.degrees(rng), b_to_tlc(rng))
plt.plot(np.degrees(rng), a)


plt.show()

#Understeer t = sqrt(w)*sqrt(2*r + w)/(sqrt(r)*sqrt(v)*sqrt(-b))
#Oversteer  t = sqrt(-w)*sqrt(2*r + w)/(sqrt(b)*sqrt(r)*sqrt(v))
