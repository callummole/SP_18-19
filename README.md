Experiment Repository for preprint: Mole et al., 2020, Predicting Takeover Response to silent automated failures. 

The experiment was ran in the following order.

- Practice (steer manually to familiarise with simulator; experience take-overs) (SP_Orca18_Practice.py)
- Pre Baseline Count (without Driving) (SP_Orca18_DistractorOnly.py, BLOCK = 1)
- Driving without Task (SP_Orca18_Main.py, DISTRACTOR_TYPE = "None") (counterbalanced with below)
- Driving with Task (SP_Orca18_Main.py, DISTRACTOR_TYPE = "Middle")
- Post Baseline Count (without Driving) (SP_Orca18_DistractorOnly.py, BLOCK = 1)

The module that coordinates the distractor task is Count_Adjustable.py.

The experiment used eyetracking, which relies on a custom fork of pupil-labs, branch in venlab_udp_thread:  https://github.com/OscartGiles/pupil/tree/venlab_udp_thread

For wheel automation the experiment relies on scripts in repo https://github.com/callummole/LogiWheel_Automation


