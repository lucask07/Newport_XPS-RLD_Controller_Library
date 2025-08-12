
# Newport XPS-RLD Controller Library

This project works to develop an easy to use python library to interact with the Newport XPS-RLD Controller. It works mainly through sending HTTP requests to the local server and utilizes FCGI commands. Communicating this way through python enables easy automation for gathering data. Can be expanded to include any command compatible with the controller, but currently only inlcudes commands that I found to be particularly useful. 




## Usage/Examples

All of this sample code can be found in sample_script.py

Start with some imports
```python
import TCL_upload, pvt
from Generate_TCL import TCL_script
from generate_pvt import fix_csv
import numpy as np
import os
```


Then Initialize the controller connection.
Ensure the IP address, username, and password are correct for your setup.

```python
controller = TCL_upload.Newport_Controller_Connection(ip="10.219.2.44", username="Administrator", password="Administrator")
```

Using a safe_start command insures that the controller's groups are ready to be moved around.

Defining your file paths and names are important, if you're not using a subfolder, they can be the same.

```python
controller.safe_start(controller.MULTI_AXIS_GROUP)

# Define the filenames you want to save the PVT file and TCL file to
filename_pvt = "sample.pvt"
filepath_pvt = os.path.join("TCL_Scripts", filename_pvt)

filename_tcl = "sample.tcl"
filepath_tcl = os.path.join("TCL_Scripts", filename_tcl)
```


Now that we are connected to the controller, we will generate a TCL script that allows the controller to home (go to position 0) and to execute our PVT script. 

Then we upload our file to the controller.

This TCL script can be used over and over as you change your PVT file, assuming you leave the PVT filename the same. 

```python
# Create an instance of the TCL_script class
my_script = TCL_script()

# Move the multi-axis group to the home position
my_script.home(controller.MULTI_AXIS_GROUP)

# If you want to move the multi-axis group to a specific position, you can do so here
# This could be useful if you need an offset or a specific starting position
# Ex: my_script.move(controller.MULTI_AXIS_GROUP, [40, 100])

# Verify the PVT file before execution
my_script.pvt_verification(controller.MULTI_AXIS_GROUP, filename_pvt)

# Execute the PVT file
my_script.pvt_execution(controller.MULTI_AXIS_GROUP, filename_pvt)

# Write the TCL script to a file
my_script.write_file(filepath_tcl)

# Upload the TCL script to the controller
controller.upload_file(
    local_path=filepath_tcl,
    remote_filename=filename_tcl,
    destpath=controller.TCL_SCRIPTS_PATH,
    enable_overwrite=True
    )

```

Now we will generate our PVT file to run on the controller

```python
# Define the trajectory parameters
# These parameters can be adjusted based on your specific trajectory requirements
# Importantly, tweaking the dt value can have a significant impact on the trajectory's smoothness and accuracy
dt = .2

# Define the trajectory you want to generate, for example, a sine wave trajectory

# Here, we define a sine wave trajectory with specific parameters
# Adjust the duration, amplitude, and period as needed for your application
duration = 10    # Duration of the trajectory in seconds
amplitude = 100  # Amplitude of the sine wave in milimeters
period = 3       # Period of the sine wave in seconds


# Define the sequence of time values, in seconds.
n_samples = int(duration / dt)
t = np.linspace(0, duration, n_samples + 1)

# Absolute sine positions for Axis 2
pos2 = amplitude * np.cos(2 * np.pi * t / period)

# Define the sequence of position values, in milimeters. 
# Note: we use a 2-D array for the position sequence.
position_sequence = [
    np.zeros_like(pos2),  # axis 1 positions
    pos2,   # axis 2 positions
]

# Create a sequence, generating the missing velocity values
pvt_sequence = pvt.Sequence.generate_velocities(t, position_sequence, velocity_sequences=None)

# Save the sequence to a file for import to the PVT Viewer App
pvt_sequence.save_to_file(filepath_pvt)
```

The file generated through the pvt library used here is not quite compatible with our controller. Mainly, our controller uses relative time and position values, whereas the file generated uses absolute values. 

We have a function to fix this file and make it compatible with our controller. It also introduces an acceleration sequence in the beggining, and a deceleration sequence at the end. This helps us keep the maximum velocity and acceleration from spiking. 

```python
# Fix the CSV file to remove the first line and adjust timestamps.
# This step makes the PVT file compatible with our controller
fix_csv(filepath_pvt, acceleration=-1200) # Adjust the acceleration as needed, always use negative values, because this is for deceleration, max of 2000
```

After making the PVT file, we upload it to the controller and use a function to verify if it is valid or not. Having an invalid file will raise an exception and tell you which values are out of bounds. 

Calling the start_gathering function is used to set up the gathering trigger and window via the controller. If the PVT file is valid, the run should start with the gathering in place.

``` python
controller.time_ms = (duration + 1) * 1000  #The time_ms parameter specifies how long the gathering should run
controller.start_gathering(trigger="Group3.PVT.TrajectoryStart", time_ms=controller.time_ms)

result = controller.upload_and_execute(
        local_path=filepath_pvt,
        remote_filename=filename_pvt,
        destpath=controller.TRAJECTORIES_PATH,
        enable_overwrite=True,
        script_name=filename_tcl,
        task_name="traj-run-1",
        verify_pvt=filename_pvt
    )

# Check if the PVT file verification was successful
# If the verification fails, an exception will be raised
if result is not None:
    raise Exception("PVT file verification failed.")
```

Finally, we will start a polling process to monitor how far along we are in the data gathering process. Once done, we will download the data and open a webpage containing a graph showing the results in a default browser.

Verbose is used here to print how far in the process of the data gathering the controller is in real time.

```python

# Start the polling process
if controller.poll_until_gathering_done(timeout=5, verbose=True):
    controller.stop_and_save_gathering()
    controller.get_gathered_data()
    controller.open_graph_webpage()
else:
    print("Gathering never completed.")

# Optional step to convert the gathered data from .dat to .csv format
controller.convert_dat_to_csv("Gathering.dat", "Gathering.csv")
```