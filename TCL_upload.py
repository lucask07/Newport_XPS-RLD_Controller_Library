import requests
import base64
import os
import time

from urllib.parse import quote
from requests.auth import HTTPDigestAuth

class Newport_Controller_Connection():
    '''
    A class to handle the connection and communication with a Newport XPS controller.
    It provides methods to upload files, execute TCL scripts, and manage groups on the controller.
    The controller must be configured to allow remote access and the user must have the necessary permissions.
    '''

    def __init__(self, ip, username=None, password=None):
        '''Initialize the connection with the Newport XPS controller.
        Args:
            ip (str): The IP address of the Newport XPS controller.
            username (str): The username for the controller. If None, will prompt for input.
            password (str): The password for the controller. If None, will prompt for input.
            
        '''
        if username is None:
            username = input("Enter a username: ")
        
        if password is None:
            password = input("Enter a password: ")

        self.IP = ip
        self.AUTH = HTTPDigestAuth(username, password)
        self.username = username
        self.password = password
        
        self.time_ms = 5000

        self.GROUP_ROTATION = 1
        self.GROUP_TRANSLATION = 2
        self.MULTI_AXIS_GROUP = 3

        # Options for file upload destpath
        self.TCL_SCRIPTS_PATH = "scripts"
        self.TRAJECTORIES_PATH = "trajectories"
        self.GATHERINGS_PATH = "gatherings"




    def upload_file(self, local_path, remote_filename, destpath="scripts", enable_overwrite=False):
        ''' Upload a file to the Newport XPS controller.

        Args:
            local_path      (str): The local path to the file to be uploaded.
            remote_filename (str): The name of the file on the controller after upload.
            destpath        (str): The destination path on the controller where the file will be uploaded.
                                   Default is "scripts". Other options include "trajectories" and "gatherings".
            enable_overwrite (bool): If True, will overwrite the file if it already exists on the controller.
        
        '''

        # Usage example
        '''
        upload_tcl(
            local_path=os.path.join("TCL_Scripts", "Demo_file2.tcl"),
            remote_filename="Demo_file4.tcl"
        )'''

        ip = self.IP

        # Base64-encode required fields
        usr_b64 = base64.b64encode(self.username.encode()).decode()
        noexist_b64 = base64.b64encode(b"true" if not enable_overwrite else b"false").decode()
        destpath_b64 = base64.b64encode(destpath.encode("utf-8")).decode()
        action_b64 = base64.b64encode(b"upload").decode()
        cmd_type = "file"

        # This auth key must be from a live session.
        # You may need to scrape it from the login response unless it's static
        auth_key = "d169aa4109166f0b751fe3d51a62fdae"

        url = f"http://{ip}/cmd.php"

        with open(local_path, "rb") as f:
            files = {
                "upload": (remote_filename, f, "application/octet-stream")
            }

            data = {
                "usr": usr_b64,
                "auth": auth_key,
                "cmd": cmd_type,
                "action": action_b64,
                "destpath": destpath_b64,
                "noexist": noexist_b64
            }

            response = requests.post(url, data=data, files=files)
            print(f"Status: {response.status_code}")
            print(response.text)





    def execute_tcl_script(self, script_name, task_name=None):

        ''' Execute a tcl script on the Newport XPS controller.
        
        Args:
            script_name  (str): The name of the tcl script to execute. Must be already uploaded to the controller.
            task_name    (str): The name of the "task" for the script execution. If None, will use script_name with "-run-1" appended.
                               This is used to identify the execution instance.
            
        '''

        # Usage
        '''
        execute_tcl_script(
            script_name="Demo_file.tcl",
            task_name="Demo_file-run-1",
        )
        '''

        ip = self.IP

        if task_name is None:
            task_name=script_name[:-4] + "-run-1"

        raw_query = f"TCLScriptExecuteWithPriority({script_name},{task_name},MEDIUM,)"
        encoded_query = quote(raw_query)

        url = f"http://{ip}/MainController.fcgi/s=1/i=1235249915/t=30/q={encoded_query}/ENDREQUEST/"
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Referer": f"http://{ip}/"
        }

        try:
            response = requests.get(url, headers=headers, auth=self.AUTH, timeout=10)
            print(f"Status Code: {response.status_code}")
            print("Response Text:\n", response.text)
        except Exception as e:
            print("Error occurred:", e)

    def upload_and_execute(self, local_path, remote_filename, script_name= None, task_name=None, destpath="scripts", enable_overwrite=False):
        ''' Upload a tcl script to the Newport XPS controller and execute it.

        Args:
            local_path      (str): The local path to the tcl script to be uploaded.
            remote_filename (str): The name of the file on the controller after upload.
            script_name     (str): The name of the script to execute after upload. If None, will use remote_filename under the assumption that you want to run the same script you just uploaded.
            task_name       (str): The name of the "task" for the script execution. If None, will use remote_filename with "-run-1" appended.
            destpath        (str): The destination path on the controller where the file will be uploaded
            enable_overwrite (bool): If True, will overwrite the file if it already exists on the controller.
                                   Default is False, which will not overwrite existing files.

        '''
        # Usage
        '''
        upload_and_execute(
            local_path=os.path.join("TCL_Scripts", "Demo_file2.tcl"),
            remote_filename="Demo_file2.tcl"
            task_name="Demo_file2-run-1",
        )
        '''


        
        self.upload_file(local_path, remote_filename, destpath=destpath, enable_overwrite=enable_overwrite)
        self.execute_tcl_script(remote_filename if script_name==None else script_name, task_name=task_name)

    


    def get_gathered_data(self):
        ''' Download the Gathering.dat file from the Newport XPS controller.
        This file contains the data gathered during a gathering session.'''
        import requests
        from requests.auth import HTTPDigestAuth

        # Controller credentials
        ip = self.IP


        # Step 1: Download the binary gathering file
        url = f"http://{ip}/gatherings/Gathering.dat"
        response = requests.get(url, auth=self.AUTH)

        if response.status_code == 200:
            with open("Gathering.dat", "wb") as f:
                f.write(response.content)
            print("Downloaded Gathering.dat")
        else:
            print("Failed to download:", response.status_code, response.text)




    def convert_dat_to_csv(self, dat_path, csv_path):

        ''' Convert a Gathering.dat file to a CSV file.
        Args:
            dat_path (str): The path to the Gathering.dat file.
            csv_path (str): The path where the CSV file will be saved.
        '''

        import csv
        with open(dat_path, 'r') as dat_file:
            lines = dat_file.readlines()

        # Clean up any empty or whitespace-only lines
        lines = [line.strip() for line in lines if line.strip()]

        # Assume first non-empty line is header, and data is tab-separated
        header = lines[0].split('\t')
        rows = [line.split('\t') for line in lines[1:]]

        # Write to CSV
        with open(csv_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(header)
            writer.writerows(rows)

        print(f"Converted {dat_path} to {csv_path}")

    if False:
        upload_and_execute(
            ip="10.219.2.44",
            local_path=os.path.join("TCL_Scripts", "multi-axis.tcl"),
            remote_filename="multi-axis.tcl",
        )

        execute_tcl_script(
        ip="10.219.2.44",
        script_name="traj.tcl",
    )
        

    def send_fcgi_command(self, commands):
        ''' Send a FastCGI command to the Newport XPS controller.
        Args:
            commands (list): A list of commands to send to the controller.
                             Each command should be a string.
        Returns:
            str: The response from the controller.
        '''

        query = "%0A".join(commands) + "%0A/ENDREQUEST/"
        url = f"http://{self.IP}/MainController.fcgi/s=1/i=2018130879/t=30/q={query}"
        response = requests.get(url, auth=self.AUTH)
        print("→", commands[-1])
        print(response.text)
        return response.text

    def start_gathering(self, trigger="Immediate", time_ms=5000):
        ''' Start a gathering session on the Newport XPS controller.
        Args:
            trigger (str): The trigger condition for starting the gathering. Default is "Immediate".
            time_ms (int): The duration of the gathering in milliseconds. Default is 5000 ms.
        '''
        cmds = [
            "GatheringStop()",
            "GatheringReset()",
            "GatheringConfigurationSet(Group3.Pos1.CurrentPosition,Group3.Pos1.CurrentVelocity,Group3.Pos2.CurrentPosition,Group3.Pos2.CurrentVelocity)",
            f"EventExtendedConfigurationTriggerSet({trigger},,,,)",
            f"EventExtendedConfigurationActionSet(GatheringRun,{time_ms},10,0,0)",
            "EventExtendedStart(int*)"
        ]
        self.send_fcgi_command(cmds)


    def poll_until_gathering_done(self, timeout=20):
        ''' Poll the controller until the gathering is complete.
        Args:
            timeout (int): The maximum time to wait for the gathering to complete, in seconds. Default is 20 seconds.
        Returns:
            bool: True if the gathering completed successfully, False if it timed out.'''
        

        timeout = max(timeout, (self.time_ms//1000) + 1)    # If we are intentionally trying to record for longer, extend the timeout
        start_time = time.time()
        while True:
            response = self.send_fcgi_command(["GatheringCurrentNumberGet(int*,int*)"])
            try:
                # Parse the returned values
                parts = response.split(",")
                current = int(parts[1])
                total = self.time_ms    # Total time that we will be recording for
                print(f"Gathering: {current}/{total}")
                if current >= total:
                    return True
            except Exception as e:
                print("Polling parse error:", e)

            if time.time() - start_time > timeout:
                print("Timeout reached.")
                return False
            time.sleep(0.5)

    def open_graph_webpage(self, filename="Gathering.dat"):
        ''' Open the graph webpage for the gathered data.
        Args:
            filename (str): The name of the file to be displayed in the graph. Default is "Gathering.dat," which is where the gathering data is normally stored. If you use a different name, you must upload that file to the controller first.
        '''

        import webbrowser
        regular_string=f'''
hostname=XPS-f762
login={self.username}
auth_hash={self.AUTH}
source=/gatherings/{filename}
timestamp=
has_maincontroller=true
firmware_version=STANDARD_XPS-RL-D-USB
transfer_function=false
script_name=
script_args=

'''
        encoded_str = base64.b64encode(regular_string.encode("utf-8")).decode()
        webbrowser.open_new(f"http://{self.IP}/graph.html?_34576698=69649270&data={encoded_str}")

    def stop_and_save_gathering(self):
        ''' Stop the gathering session and save the data to the Gathering.dat file.'''
        self.send_fcgi_command(["GatheringStopAndSave()"])

    def init_group(self, group):
        ''' Initialize a group on the Newport XPS controller.
        Args:
            group (int): The group number to initialize. This should be a valid group number on the controller.
        '''
        self.send_fcgi_command([f"GroupInitialize(Group{group})"])
    
    def home_group(self, group):
        ''' Home a group on the Newport XPS controller.
        Args:
            group (int): The group number to initialize. This should be a valid group number on the controller.
        '''
        self.send_fcgi_command([f"GroupHomeSearch(Group{group})"])

    def kill_group(self, group):
        ''' Kill a group on the Newport XPS controller.
        Args:
            group (int): The group number to initialize. This should be a valid group number on the controller.
        '''
        self.send_fcgi_command([f"GroupHomeSearch(Group{group})"])

    def kill_all_groups(self):
        ''' Kill all groups on the Newport XPS controller.
        
        This will stop all movements and clear any active tasks.

        NOTE: this does not work right now
        '''
        self.send_fcgi_command([f"KillAll"])

    def PVT_verification(self, group, filename):
        ''' Verify the PVT trajectory for a group on the Newport XPS controller.
        Args:
            group (int): The group number to verify.
            filename (str): The name of the PVT file to verify.
        '''
        self.send_fcgi_command([f"MultipleAxesPTVerification(Group{group},{filename})"])

    def PVT_verification_result_get(self, group, pos):
        ''' Get the results of the PVT verification for a group on the Newport XPS controller.\n

        format of results:\n 
        double  MinimumPosition,\n
        double  MaximumPosition,\n
        double  MaximumVelocity,\n
        double  MaximumAcceleration

        Args:
            group (int): The group number to verify.
            pos (int): The position in the group to get the results for.
        Returns:
            str: The response from the controller containing the verification results.
        '''
        response = self.send_fcgi_command([f"MultipleAxesPVTVerificationResultGet(Group{group}.Pos{pos}, char * , double * , double * , double * , double *)"])
        return response

# -=============================================-


if __name__ == "__main__":

    controller = Newport_Controller_Connection( ip="10.219.2.44")

    controller.PVT_verification(
        group=controller.MULTI_AXIS_GROUP,
        filename="sine_wave.pvt"
    )

    controller.PVT_verification_result_get(
        group=controller.MULTI_AXIS_GROUP,
        pos=2
    )



    controller.time_ms = 10_000
    controller.start_gathering(trigger="Group3.PVT.TrajectoryStart", time_ms=controller.time_ms)
    controller.upload_and_execute(
        local_path=os.path.join("TCL_Scripts", "sine_wave.pvt"),
        remote_filename="sine_wave.pvt",
        destpath=controller.TRAJECTORIES_PATH,
        enable_overwrite=True,
        script_name="traj.tcl",
        task_name="traj-run-1",
    )
    if controller.poll_until_gathering_done(timeout=20):
        controller.stop_and_save_gathering()
        controller.get_gathered_data()
        controller.open_graph_webpage()
    else:
        print("Gathering never completed.")

    controller.convert_dat_to_csv("Gathering.dat", "Gathering.csv")

