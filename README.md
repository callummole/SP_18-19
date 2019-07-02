# SP_18-19
Repo for Undergraduate Projects academic year 2018-19: Cognitive Load during Automation.

The experiment was ran in the following order.

- Practice (steer manually to familiarise with simulator; experience take-overs) (SP_Orca18_Practice.py)
- Pre Baseline Count (without Driving; levels interleaved) (SP_Orca18_DistractorOnly.py, BLOCK = 1)
- Pre Baseline Driving (without Count; radii interleaved) (SP_Orca18_Main.py, DISTRACTOR_TYPE = None, BLOCK = 1)-
- Hard Count with Driving (counterbalanced with below) (SP_Orca18_Main.py, DISTRACTOR_TYPE = "Hard")
- Easy Count with Driving (counterbalanced with above) (SP_Orca18_Main.py, DISTRACTOR_TYPE = "Easy")
- Post Baseline Count (without Driving; levels interleaved) (SP_Orca18_DistractorOnly.py, BLOCK = 1)
- Post Baseline Driving (without Count; radii interleaved) (SP_Orca18_Main.py, DISTRACTOR_TYPE = None, BLOCK = 2)

The module that coordinates the distractor task is Count_Adjustable.py.

The experiment used eyetracking, which relies on a custom fork of pupil-labs, branch in venlab_udp_thread:  https://github.com/OscartGiles/pupil/tree/venlab_udp_thread

A Data Dictionary can be found in the Data Folder README. 


