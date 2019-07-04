from numpy import sqrt, abs, sign
# Transforms between TTLC and yaw rate offset on circular
# trajectories, assuming centered initial position. Based on
# small angle approximation of cosine, but should be in practice
# very accurate on reasonable yaw rates.
#
# b is the yaw rate offset in radians (negative is understeering)
# t is the TTLC (negative is understeering)
# w is half the road width
# r is the path radius
# v is the velocity (m/s)

def ttlc_from_offset(b, w, r, v):
    return sign(b)*sqrt(w*(2*r + sign(b)*w)/(abs(b)*r*v))

def offset_from_ttlc(t, w, r, v):
    return sign(t)*w*(2*r + sign(t)*w)/(r*t**2*v)

if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt

    rng = np.radians(np.linspace(-10, 10, 1000))

    param = dict(w=1.5, r=80, v=8)
    undoed = offset_from_ttlc(ttlc_from_offset(rng, **param), **param)
    plt.plot(rng, undoed - rng)
    plt.figure()
    plt.plot(-np.degrees(rng[rng < -0.01]), -ttlc_from_offset(rng[rng < -0.01], **param), label='Understeer')
    plt.plot(np.degrees(rng[rng > 0.01]), ttlc_from_offset(rng[rng > 0.01], **param), label='Oversteer')
    plt.xlabel("Yaw rate bias (degrees)")
    plt.ylabel("TTLC (seconds)")
    plt.legend()
    plt.show()
