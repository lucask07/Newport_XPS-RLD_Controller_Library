import math
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_sine_wave_pvt(filename, amplitude=50, period=4, duration=20, dt=0.1):
    """
    Generate a PVT file with relative position deltas and absolute velocities.

    Axis 1: remains fixed at 0.
    Axis 2: follows a sine wave.
    Format per line: delta_t pos1 vel1 pos2 vel2
    """

    n_samples = int(duration / dt)
    t = np.linspace(0, duration, n_samples + 1)

    # Absolute sine positions for Axis 2
    pos2 = amplitude * np.sin(2 * np.pi * t / period)
    vel2 = np.gradient(pos2, dt)

    # Convert to relative position deltas
    pos2_deltas = np.diff(pos2, prepend=pos2[0])

    # Axis 1: no movement
    pos1_deltas = np.zeros_like(pos2_deltas)
    vel1 = np.zeros_like(vel2)

    # Compute max stats for info
    max_acc = np.max(np.abs(np.gradient(vel2, dt)))
    max_vel = np.max(np.abs(vel2))
    print(f"Max acceleration magnitude on axis 2: {max_acc:.3f} units/s²")
    print(f"Max velocity magnitude on axis 2: {max_vel:.3f} units/s")

    # Write to file
    with open(filename, 'w') as f:
        for i in range(n_samples):
            f.write(f"{dt:.5f} {pos1_deltas[i]:.5f} {vel1[i]:.5f} {pos2_deltas[i]:.5f} {vel2[i]:.5f}\n")

        # Final stop line
        f.write(f"{dt:.5f} 0.0 0.0 0.0 0.0\n")

def position_to_pvt(filename, positions, duration=10, dt=0.1):
    """
    Generate a PVT file with relative position deltas and absolute velocities.

    Axis 1: remains fixed at 0.
    Axis 2: follows {positions}
    Format per line: delta_t pos1 vel1 pos2 vel2
    """

    n_samples = len(positions)
    t = np.linspace(0, duration, n_samples + 1)

    # Absolute positions for Axis 2
    pos2 = positions
    vel2 = np.gradient(pos2, dt)

    # Convert to relative position deltas
    pos2_deltas = np.diff(pos2, prepend=pos2[0])

    # Axis 1: no movement
    pos1_deltas = np.zeros_like(pos2_deltas)
    vel1 = np.zeros_like(vel2)

    # Compute max stats for info
    max_acc = np.max(np.abs(np.gradient(vel2, dt)))
    max_vel = np.max(np.abs(vel2))
    print(f"Max acceleration magnitude on axis 2: {max_acc:.3f} units/s²")
    print(f"Max velocity magnitude on axis 2: {max_vel:.3f} units/s")

    # Write to file
    with open(filename, 'w') as f:
        for i in range(n_samples):
            f.write(f"{dt:.5f} {pos2_deltas[i]/2:.5f} {vel2[i]/2:.5f} {pos2_deltas[i]:.5f} {vel2[i]:.5f}\n")

        # Final stop line
        f.write(f"{dt:.5f} 0.0 0.0 0.0 0.0\n")
        f.write(f"{dt:.5f} 0.0 0.0 0.0 0.0\n")
    

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

if __name__ == "__main__":
    filename = os.path.join("TCL_Scripts", "sine_wave.pvt")
    #generate_sine_wave_pvt(filename, amplitude=10, period=1, duration=10, dt=0.15)

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
