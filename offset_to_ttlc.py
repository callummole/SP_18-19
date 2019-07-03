from sympy import *
import numpy as np
import matplotlib.pyplot as plt

var("v w", real=True, positive=True, nonzero=True)
var("t", real=True, positive=True)
var("b", real=True, nonzero=True, positive=True)
var("x a", real=True, cls=Function)

da = b
a = dsolve(
        Eq(Derivative(a(t)), da),
        a(t), ics={a(0): 0})
a = a.rhs
a = simplify(a)

dx = sin(a)*v
x = dsolve(
        Eq(Derivative(x(t)), dx),
        x(t), ics={x(0): 0}
        ).rhs.simplify()
critical = Eq(x, w/2)
b_to_t = solve(critical, t)[1]
cosa = solve(Eq(b, 1 - t**2/2), t)[1].simplify()
b_to_t_approx = cosa.subs({b: -b*w/(2*v) + 1})/b
#b_to_t_approx = cosa.subs({b: (-b*w + v)/(2*v)})/b

t_to_b_approx = solve(Eq(t, b_to_t_approx), b)[0]
#pprint(t_to_b_approx)

vals = {v: 8, w: 1.5}
numa = lambdify(b, b_to_t_approx.subs(vals))
numinv = lambdify(t, t_to_b_approx.subs(vals))
num = b_to_t.subs(vals)
#print(solve(Eq(t, num), b))
num = lambdify(b, num)
rng = np.radians(np.linspace(-10, 10, 1000))
plt.plot(np.degrees(rng), num(np.abs(rng)), label="True")
plt.plot(np.degrees(rng), numa(np.abs(rng)), '--', label='Approximation')
plt.xlabel("Yaw rate bias (degrees)")
plt.ylabel("TTLC")
plt.legend()

plt.figure()
trng = np.linspace(-10, 10, 1000)
plt.plot(trng, numinv(trng), label='Approximation')
plt.ylabel("Yaw rate bias (degrees)")
plt.xlabel("Time to line crossing (seconds)")

plt.legend()
plt.figure()
plt.plot(np.degrees(rng), np.degrees(np.abs(numinv(num(rng)) - rng)))
plt.xlabel("Bias (degrees)")
plt.ylabel("Inversion approximation error (degrees)")

print("b =", t_to_b_approx)
plt.show()
#pprint(sol.simplify())
