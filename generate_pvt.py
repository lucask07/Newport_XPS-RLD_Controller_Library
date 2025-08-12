import math
import numpy as np
import matplotlib.pyplot as plt
import os

GROUP_ROTATION = 1
GROUP_TRANSLATION = 2
MULTI_AXIS_GROUP = 3

def generate_sine_wave_pvt(filename, amplitude=50, period=4, duration=10, dt=0.1, group=GROUP_TRANSLATION, forwarded_data=None):
    """
    Generate a PVT file with relative position deltas and absolute velocities.

    Group 1: Rotation table
    Group 2: Translation Stage
    Group 3: Multi-axis group, using both previous groups.

    Format per line: delta_t pos1 vel1 pos2 vel2
    """

    n_samples = int(duration / dt)
    t = np.linspace(0, duration, n_samples + 1)

    # Absolute sine positions for Axis 2
    pos2 = amplitude * np.sin(2 * np.pi * t / period)
    
    return position_to_pvt(filename, pos2, duration=duration, dt=dt, group=group, forwarded_data=forwarded_data)

def position_to_pvt(filename, positions, duration=10, dt=0.1, group=GROUP_TRANSLATION, forwarded_data=None):
    """
    Generate a PVT file with relative position deltas and absolute velocities.

    Group 1: Rotation table
    Group 2: Translation Stage
    Group 3: Multi-axis group, using both previous groups.

    Format per line: delta_t pos1 vel1 pos2 vel2
    """

    # Absolute positions for Axis 2
    pos = positions
    vel = np.gradient(pos, dt)

    # Convert to relative position deltas
    pos_deltas = np.diff(pos, prepend=pos[0])


    # Compute max stats for quick info, this is not accurate for how the system calculates acceleration and velocity
    #max_acc = np.max(np.abs(np.gradient(vel, dt)))
    #max_vel = np.max(np.abs(vel))
    #print(f"Max acceleration magnitude on axis 2: {max_acc:.3f} units/s²")
    #print(f"Max velocity magnitude on axis 2: {max_vel:.3f} units/s")

    if group == GROUP_ROTATION:
        write_pvt_file(filename, dt, pos_deltas, vel, 0, 0)
    elif group == GROUP_TRANSLATION:
        write_pvt_file(filename, dt, 0, 0, pos_deltas, vel)
    elif group == MULTI_AXIS_GROUP:
        # If we are using a multi-axis group, we need to combine the data before writing
        
        return (pos_deltas, vel)


def write_pvt_file(filename, delta_t, pos1, vel1, pos2, vel2):
    """
    Write PVT data to a file.
    
    """

    if type(pos1) is not np.ndarray:
        pos1 = [0]
    elif type(pos2) is not np.ndarray:
        pos2 = [0]
    

    with open(filename, 'w') as f:
        for i in range(max(len(pos1), len(pos2))):
            if len(pos1) == 1:
                pos1 = np.zeros_like(pos2)
                vel1 = np.zeros_like(vel2)
            elif len(pos2) == 1:
                pos2 = np.zeros_like(pos1)
                vel2 = np.zeros_like(vel1)
            
            f.write(f"{delta_t:.5f} {pos1[i]:.5f} {vel1[i]:.5f} {pos2[i]:.5f} {vel2[i]:.5f}\n")
        
        # Final stop line
        f.write(f"{delta_t:.5f} 0.0 0.0 0.0 0.0\n")
        f.write(f"{delta_t:.5f} 0.0 0.0 0.0 0.0\n")
    
    print(f"PVT file '{filename}' generated with {len(pos1)} samples.")
    
def generate_multi_axis_pvt(data1, data2, filename="multi_axis.pvt", dt=0.1):
    """
    Generate a multi-axis PVT file from two sets of data.
    
    This function assumes data1 and data2 are tuples of (positions, velocities).
    """

    print(data1)
    
    pos1, vel1 = data1
    pos2, vel2 = data2

    write_pvt_file(filename, dt, pos1, vel1, pos2, vel2)

def plot_pvt(filename):
    # Read and plot PVT file
    data = np.loadtxt(filename)
    delta_ts = data[:, 0]
    pos1 = data[:, 1]
    vel1 = data[:, 2]
    pos2 = data[:, 3]
    vel2 = data[:, 4]

    time = np.cumsum(delta_ts)

    # Reconstruct cumulative positions
    cum_pos1 = np.cumsum(pos1)
    cum_pos2 = np.cumsum(pos2)

    fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    axs[0].plot(time, cum_pos1, label="Pos Axis 1")
    axs[0].plot(time, vel1, label="Vel Axis 1")
    axs[0].set_ylabel("Axis 1")
    axs[0].legend()
    axs[0].grid(True)

    axs[1].plot(time, cum_pos2, label="Pos Axis 2")
    axs[1].plot(time, vel2, label="Vel Axis 2")
    axs[1].set_ylabel("Axis 2")
    axs[1].set_xlabel("Time (s)")
    axs[1].legend()
    axs[1].grid(True)

    plt.suptitle("PVT Trajectory")
    plt.tight_layout()
    plt.show()


def generate_deceleration_pvt(last_pos, last_vel, dt=0.2, acc=-100.0):
    """
    Generate deceleration PVT rows (delta-pos, velocity) for instrument 2.
    Assumes instrument 1 is stationary.
    """
    rows = []
    vel = last_vel

    negative_sign = -1 if last_vel < 0 else 1

    first = True
    
    while (negative_sign * vel) > 0:
        next_vel = vel + (acc * dt * negative_sign)
        if next_vel * negative_sign < 0:
            next_vel = 0.0
        
        avg_vel = (vel + next_vel) / 2

        if first:
            delta_pos = abs(avg_vel * dt) * negative_sign
            first = False
        else:
            delta_pos = abs(avg_vel * dt) * negative_sign

        rows.append((dt, 0.0, 0.0, delta_pos, next_vel))
        vel = next_vel
    
    return rows

def fix_csv(filename, acceleration=-1200):
    """
    Fix the CSV file by removing the first line if it contains a timestamp of 0.0 
    and adjusting values to be relative instead of absolute.
    """
    lines = []
    with open(filename, 'r+') as f:
        lines_og = f.readlines()

        lines = lines_og.copy()
        
        # Take out the first line Time,Axis 1 Position,Axis 1 Velocity,Axis 2 Position,Axis 2 Velocity
        lines[0] = ""

        # The next line should not have a timestamp of 0.0
        if lines[1].startswith("0.0"):
            lines[1] = lines[1].replace("0.0", "0.2", 1)
        
        lines[1] = ""
        
        # Now, we have to convert the timestamps from absolute time to delta time
        for i in range(3, len(lines)):
            parts = lines_og[i].strip().split(',')
            if len(parts) < 5:
                continue
            
            # Convert the first part to delta time
            if i == 1:
                delta_time = float(parts[0])
                delta_pos1 = float(parts[1])
                delta_pos2 = float(parts[3])
            else:
                delta_time = float(parts[0]) - float(lines_og[i-1].strip().split(',')[0])
                delta_pos1 = float(parts[1]) - float(lines_og[i-1].strip().split(',')[1])
                delta_pos2 = float(parts[3]) - float(lines_og[i-1].strip().split(',')[3])

            
            
            #print(f"Line {i}: Original timestamp: {float(parts[0])}, previous timestamp: {float(lines[i-1].strip().split(',')[0])}, Delta time: {delta_time:.5f}")
   
            
            parts[0] = f"{delta_time:.5f}"
            parts[1] = f"{delta_pos1:.5f}"
            parts[3] = f"{delta_pos2:.5f}"
            lines[i] = ','.join(parts) + '\n'
        
        # Adjust for the deacceleration at the end of the trajectory
        starting_pos = 100
        current_pos = starting_pos
        for i in range(3, len(lines)):
            parts = lines[i].strip().split(',')
            current_pos += float(parts[3])  # Update current position with the delta
        
        # Now we know where we are position-wise and we can start decellerating from there
        dt = lines[3].strip().split(',')[0]

        vel_value1 = float(lines[-3].strip().split(',')[4]) 
        vel_value2 = float(lines[-2].strip().split(',')[4]) 

        pos_value1 = float(lines[-2].strip().split(',')[3])

        vel_diff = max(vel_value1, vel_value2) - min(vel_value1, vel_value2)
        deceleration = vel_diff / 2  # Half the difference to decelerate to zero

        rows = generate_deceleration_pvt(pos_value1, vel_value2, dt=float(dt), acc=acceleration)

        rows_strings = [f"{row[0]:.5f},{row[1]:.5f},{row[2]:.5f},{row[3]:.5f},{row[4]:.5f}\n" for row in rows]

        # Gives the first line more time to reach the first position, gives us more headroom for acceleration
        parts = lines[2].strip().split(',')
        parts[0] = f"{float(parts[0]) * 4}"
        lines[2] = ','.join(parts) + '\n'


    
        


        
    with open(filename, 'w') as f:
        f.writelines(lines[:-1])
        f.writelines(rows_strings)


if __name__ == "__main__":
    from TCL_upload import Newport_Controller_Connection
    import time

    filename = os.path.join("TCL_Scripts", "sine_wave.pvt")
    dt = .2

    controller = Newport_Controller_Connection(ip="10.219.2.44", username="Administrator", password="Administrator")

    #print(test())
    #print(generate_sine_wave_pvt(filename, amplitude=10, period=1, duration=10, dt=dt, group=MULTI_AXIS_GROUP))

    #generate_multi_axis_pvt(
    #    generate_sine_wave_pvt(filename, amplitude=5, period=8, duration=10, dt=0.15, group=MULTI_AXIS_GROUP),
    #    (0,0),#generate_sine_wave_pvt(filename, amplitude=45, period=4, duration=10, dt=0.15, group=MULTI_AXIS_GROUP),
    ##    filename=filename,
    #    dt=dt
    #)

    controller.safe_start(group=MULTI_AXIS_GROUP)



    import pvt
    duration =5
    amplitude = 90
    period = 3
    # Define the sequence of time values, in seconds.

    n_samples = int(duration / dt)
    t = np.linspace(0, duration, n_samples + 1)

    # Absolute sine positions for Axis 2
    pos2 = amplitude * np.cos(2 * np.pi * t / period)

    # Define the sequence of position values, in centimetres. Note
    # we use a 2-D array for the position sequence.
    position_sequence = [
        np.zeros_like(pos2),  # axis 1 positions
        pos2,   # axis 2 positions #### np.diff(pos2, prepend=pos2[0])
    ]

    print(np.full(len(t) - 1, dt))
    print(len(np.full(len(t), dt)), len(position_sequence[0]), len(position_sequence[1]))
    print(np.isnan(np.full(len(t), dt)).any(),np.isnan(position_sequence[0]).any(), np.isnan(position_sequence[1]).any())

    # Create a sequence, generating the missing velocity values
    pvt_sequence = pvt.Sequence.generate_velocities(t, position_sequence, velocity_sequences=None)
    # Save the sequence to a file for import to the PVT Viewer App
    #pvt_sequence.save_to_file(filename)


    print(f"Generated PVT sequence.")

    # Fix the CSV file to remove the first line and adjust timestamps
    #fix_csv(filename)

    controller.time_ms = 10_000
    controller.start_gathering(trigger="Group3.PVT.TrajectoryStart", time_ms=controller.time_ms)
    result = controller.upload_and_execute(
        local_path=filename,
        remote_filename="sine_wave.pvt",
        destpath=controller.TRAJECTORIES_PATH,
        enable_overwrite=True,
        script_name="traj.tcl",
        task_name="traj-run-1",
        verify_pvt="sine_wave.pvt"
    )

    if result is not None:
        raise Exception("PVT file verification failed.")

    if controller.poll_until_gathering_done(timeout=5):
        controller.stop_and_save_gathering()
        controller.get_gathered_data()
        controller.open_graph_webpage()
    else:
        print("Gathering never completed.")

    controller.convert_dat_to_csv("Gathering.dat", "Gathering.csv")

    '''
    pos = [0]
    neg = False
    for i in range(20):
        change = 20
        if neg:
            change *= -1

        newVal = pos[-1] + change
        if i % 5 == 4:
            neg = not neg

        pos.append(newVal)

    position_to_pvt(filename, pos, duration=10, dt=0.5)

    plot_pvt(filename)
    print(f"PVT file '{filename}' generated.")
    '''
