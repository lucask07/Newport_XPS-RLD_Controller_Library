import TCL_upload, pvt
from Generate_TCL import TCL_script
from generate_pvt import fix_csv
import numpy as np
import os
import sys
import threading 
import time 

sys.path.append("C:\\Users\\koer2434\Documents\\s24_seth_lindgren\\s24_seth_lindgren\\picodemocode\\PH300-v3.x-Demos\\64\\python\\")
sys.path.append("C:\\Users\\koer2434\Documents\\s24_seth_lindgren\\s24_seth_lindgren\\picodemocode\\PH300-v3.x-Demos\\64\\python\TTTRmode\\")

from tttrmode import capture_file, PTU_PATH

SPAD_DATA = False

def get_controller():
    # Initialize the controller connection
    # Ensure the IP address, username, and password are correct for your setup
    controller = TCL_upload.Newport_Controller_Connection(ip="10.219.2.44", username="Administrator", password="Administrator")

    # Safe start ensures that our group is ready to receive commands
    controller.safe_start(controller.MULTI_AXIS_GROUP)

    return controller


def main():
    # Initialize the controller connection
    # Ensure the IP address, username, and password are correct for your setup
    controller = TCL_upload.Newport_Controller_Connection(ip="10.219.2.44", username="Administrator", password="Administrator")

    # Safe start ensures that our group is ready to receive commands
    controller.safe_start(controller.MULTI_AXIS_GROUP)

    # Define the filenames you want to save the PVT file and TCL file to
    filename_pvt = "sample.pvt"
    filepath_pvt = os.path.join("TCL_Scripts", filename_pvt)

    filename_tcl = "sample.tcl"
    filepath_tcl = os.path.join("TCL_Scripts", filename_tcl)

    ###--- Create a TCL script to execute the trajectory ---###
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

    ###--- Generate a PVT trajectory ---###

    # Define the trajectory parameters
    # These parameters can be adjusted based on your specific trajectory requirements
    # Importantly, tweaking the dt value can have a significant impact on the trajectory's smoothness and accuracy
    dt = .2
    # dt = 0.05 - increases over velocity/acceleration errors as compared to 0.2 

    # Define the trajectory you want to generate, for example, a sine wave trajectory

    # Here, we define a sine wave trajectory with specific parameters
    # Adjust the duration, amplitude, and period as needed for your application
    duration = 12    # Duration of the trajectory in seconds
    amplitude = 20  # Amplitude of the sine wave in milimeters
    #period = 3     # Period of the sine wave in seconds
    period = 1     # Period of the sine wave in seconds
    pos_offset = 130 # closer to SPAD 
    theta_offset = 2 

    # Define the sequence of time values, in seconds.
    n_samples = int(duration / dt)
    t = np.linspace(0, duration, n_samples + 1)

    # Absolute sine positions for Axis 2
    pos2 = amplitude * np.cos(2 * np.pi * t / period) + pos_offset

    # Absolute positions for Axis 1 (rotation stage) 
    pos1 = 9 * np.cos(2 * np.pi * t / period) + theta_offset
    
    # Define the sequence of position values, in milimeters. 
    # Note: we use a 2-D array for the position sequence.
    position_sequence = [
        np.zeros_like(pos2) + theta_offset,  # axis 1 positions - normally rotation stage does not move 
        # pos1,
        pos2,   # axis 2 positions
    ]

    # Create a sequence, generating the missing velocity values
    pvt_sequence = pvt.Sequence.generate_velocities(t, position_sequence, velocity_sequences=None)
    
    # Save the sequence to a file for import to the PVT Viewer App
    pvt_sequence.save_to_file(filepath_pvt)

    # Fix the CSV file to remove the first line and adjust timestamps.
    # This step makes the PVT file compatible with our controller
    fix_csv(filepath_pvt, acceleration=-1200) # Adjust the acceleration as needed, always use negative values, because this is for deceleration, max of 2000

    # Start the gathering process with the specified trajectory
    # The time_ms parameter specifies how long the gathering should run
    controller.time_ms = (duration + 1) * 1000
    controller.start_gathering(trigger="Group3.PVT.TrajectoryStart", time_ms=controller.time_ms)

    keywords_args = {'local_path': filepath_pvt,
        'remote_filename': filename_pvt,
        'destpath': controller.TRAJECTORIES_PATH,
        'enable_overwrite': True,
        'script_name': filename_tcl,
        'task_name': "traj-run-1",
        'verify_pvt': filename_pvt}

    spad_filename = 'moving_close7_0411'

    if SPAD_DATA:
        # get SPAD data 
        # need to use either asyncio or multiprocessing 
        capture_file(filename=os.path.join(PTU_PATH, f"{spad_filename}_still_start.out"), tacq=2000)
        
        # result = controller.upload_and_execute(
            # local_path=filepath_pvt,
            # remote_filename=filename_pvt,
            # destpath=controller.TRAJECTORIES_PATH,
            # enable_overwrite=True,
            # script_name=filename_tcl,
            # task_name="traj-run-1",
            # verify_pvt=filename_pvt
        # )
        
        def capture_multiple(num_expr=5, tacq=2000):
            for i in range(num_expr):
                filename = os.path.join(PTU_PATH, f"{spad_filename}_{i}.out")
                capture_file(filename=filename, tacq=tacq)
            
        thread1 = threading.Thread(target=controller.upload_and_execute, kwargs=keywords_args) # there is a 1 second delay before executing 
        thread1.start()
        keywords_args = {'num_expr': 2, 'tacq':15000}
        
        thread2 = threading.Thread(target=capture_multiple, kwargs=keywords_args)
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        print('completed motion and TTTR capture')

    else:
        result = controller.upload_and_execute(**keywords_args)

    # Check if the PVT file verification was successful
    # If the verification fails, an exception will be raised
    
    # if result is not None:
        # raise Exception("PVT file verification failed.")


    # Start the polling process
    if controller.poll_until_gathering_done(timeout=5, verbose=False):
        controller.stop_and_save_gathering()
        controller.get_gathered_data()
        controller.open_graph_webpage()
    else:
        print("Gathering never completed.")

    if SPAD_DATA:
        capture_file(filename=os.path.join(PTU_PATH, f"{spad_filename}_still_end.out"), tacq=2000)

    # Optional step to convert the gathered data from .dat to .csv format
    controller.convert_dat_to_csv("Gathering.dat", "Gathering.csv")

    # replace will silently overwrite if the file already exists
    os.replace("Gathering.csv", os.path.join(PTU_PATH, f"{spad_filename}_stage_data.csv"))

    return controller

if __name__ == "__main__":
    controller = main()

    #  controller.move_relative(3,1, -8) -- move the rotation stage relative (in degrees) 
    #  controller.move_relative(3,2, 20) -- move the translation stage relative (in mm) 
    
    