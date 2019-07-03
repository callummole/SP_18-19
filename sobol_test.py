import numpy as np
import sobol_seq
import matplotlib.pyplot as plt
    

#### SOBOL RANDOMISATION #######

#3 dimensional sobol sequence: SAB, Onset Time, Trajs
Trials = 30
sobol_3D = sobol_seq.i4_sobol_generate(3, 30) # 0,1 scale

print(sobol_3D)


#onset time pool to range between 5-9.

#autofile as integers 0-3.

#sab from -5 - +5

#OnsetTimePool_sobel = np.arange(5, 9.25, step = .25) 
#OnsetTimePool = OnsetTimePool[OnsetTimePool[] != 6]


onset_sobol = sobol_3D[:,0] * 4 + 5
autofile_sobol = np.round(sobol_3D[:,1] * 3,0) 
sab_sobol = sobol_3D[:,2] * 10 - 5

plt.figure(2)
plt.plot(sab_sobol, autofile_sobol, 'k.', markersize=5, alpha = .2)
plt.xlabel("Steering Angle Biases (deg/s)")
plt.ylabel("Onset Times (s)")
plt.title("Sobol samples")
plt.show()
