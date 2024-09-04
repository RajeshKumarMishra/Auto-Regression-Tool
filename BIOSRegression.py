import subprocess
import time
import os
import shutil
import paramiko
import requests
import re
import json

file = "BinaryTool.json"
with open(file, 'r') as file:
    json_data = file.read()
ParsedData = json.loads(json_data)

for TestData in ParsedData:
    good_commit = TestData["PassShaId"]
    bad_commit = TestData["FailShaId"]
    opensourcerepo = TestData["OpenSourceRepo"]
    BuildCommand = TestData["BuildCommand"]
    BuildDirectoryPath = TestData["BuildDirectoryPath"]
    BuildPathPrefixGlobal = TestData["BuldFilePrefix"]
    ssh_host = TestData["HostIP"]
    ssh_username = TestData["HostUsername"]
    ssh_password = TestData["HostPassword"]
    
ssh_port = 22
network_path = r'\\{}\Samples'.format(ssh_host)
network_path1 = r'\\{}\Samples\CurrentExecution'.format(ssh_host)
batch_file_path = r"C:\Samples\Execution.bat"


   
def checkout_to_path(path):
    os.chdir('/')
    SourceDir = "\\Rajesh\\DemoSource"
    os.chdir(SourceDir)
    os.chdir(path)
    print("Current Directory is:",os.getcwd())
  


def run_command(command):
    """Run a command using subprocess and capture the output."""
    try:
        result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout)
        return result.stdout  # Return the output for further processing
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")
        return None

def git_bisect_start(good_commit, bad_commit):
    """Start the git bisect process with known good and bad commits."""
    if opensourcerepo == "None":
        checkout_to_path('Intel')
    else:
        checkout_to_path(opensourcerepo)
    run_command(['git', 'bisect', 'start'])
    run_command(['git', 'bisect', 'good', good_commit])
    run_command(['git', 'bisect', 'bad', bad_commit])

        
def IsBuildFilePresent():
    for file in os.listdir(os.getcwd()):
        if file.startswith(BuildPathPrefixGlobal):
            print("*****Build file Found",file)    
            return file
            
def CopyBinarytoFlashPath():
    for file in os.listdir(os.getcwd()):
        if file.startswith(BuildPathPrefixGlobal):
            new_name = "CORP_BG5_PS_INT_REL.rom"   
            shutil.copy(file, new_name)
            return new_name
            
def copy_log_file(source_path, destination_path):
    """Copy the contents of the source log file to the destination log file."""
    try:
        shutil.copy(source_path, destination_path)
        print(f"Copied log file to {destination_path}")
    except Exception as e:
        print(f"Failed to copy log file: {e}")

def get_commit_title(commit_id):
    """Get the title of the commit."""
    try:
        result = subprocess.run(['git', 'show', '--no-patch', '--format=%s', commit_id], text=True, stdout=subprocess.PIPE)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Failed to get commit title: {e}")
        return None

def ExecuteTest(ssh_host, ssh_port, ssh_username, ssh_password, batch_file_path):
    """
    Executes a batch file on a remote Windows machine via SSH and returns the output.

    :param ssh_host: IP address or hostname of the remote PC
    :param ssh_port: SSH port (default is 22)
    :param ssh_username: SSH username for the remote PC
    :param ssh_password: SSH password for the remote PC
    :param batch_file_path: Path to the batch file on the remote PC
    :return: A tuple containing the standard output and standard error
    """
    # Initialize the SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the SSH server
        client.connect(hostname=ssh_host, port=ssh_port, username=ssh_username, password=ssh_password)
        
        # Execute the batch file using cmd.exe
        stdin, stdout, stderr = client.exec_command(f"cmd.exe /c \"{batch_file_path}\"")
        
        # Wait for the command to complete and fetch the output
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        errors = stderr.read().decode('utf-8')
        
        return output, errors, exit_status
        
    except paramiko.AuthenticationException:
        print("Authentication failed, please verify your credentials.")
    except paramiko.SSHException as sshException:
        print(f"Could not establish SSH connection: {sshException}")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        client.close()
   

def build_bios(current_commit, count):

    commit_title = get_commit_title(current_commit)
    sanitizedtitle = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', commit_title)
    destination_log_file = f"{sanitizedtitle}.log"
    if os.path.exists(destination_log_file):
        print(f"The file '{sanitizedtitle}' exists.")
    else:
        print(f"The file '{sanitizedtitle}' doesn't exists.")

    checkout_to_path('Intel/AlderlakeboardPkg')
    print(f"Currently at commit {current_commit}")
    return_code = subprocess.call(BuildCommand, shell=True)
    
    
    checkout_to_path('RomImages')
    temp = IsBuildFilePresent()
    print(count, current_commit, temp)
    BuildFileNameOutput = str(count)+ "_" + current_commit + "_" + temp 
    OutPutFileBiosName = network_path + "\\" + BuildFileNameOutput
    shutil.copy(temp,OutPutFileBiosName)
    temp1 = CopyBinarytoFlashPath()
    OutPutFileBiosName = network_path1 + "\\" + temp1
    shutil.copy(temp1,OutPutFileBiosName)
    print("Copying Binary to HOST Machine....")
    stdout, stderr, exit_status = ExecuteTest(ssh_host, ssh_port, ssh_username, ssh_password, batch_file_path)
    
    checkout_to_path('Intel')

    with open(destination_log_file, 'w') as log_file:
        log_file.write(stdout)
        
    if "---- TEST PASSED ----" in stdout:
        return "good"
    else:
        return "bad"


def git_bisect_manual(network_file_path):
    """Manually process git bisect with test results from a file."""
    bisect_count = 0
    
    while True:
        # Get the current commit ID
        current_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], text=True, stdout=subprocess.PIPE).stdout.strip()
        bisect_count += 1
        print(f"Currently at commit {current_commit}")
          
        test_result = build_bios(current_commit, bisect_count)
        print("....Flashing the BIOS....")
        if opensourcerepo == "None":
            checkout_to_path('Intel')
        else:
            checkout_to_path(opensourcerepo)
        time.sleep(1)
               
        if test_result is None:
            print("Could not read the test result. Please check the file path and permissions.")
            break
        
        if test_result == 'good':
            output = run_command(['git', 'bisect', 'good'])
        elif test_result == 'bad':
            output = run_command(['git', 'bisect', 'bad'])
        else:
            print("Invalid test result in file. Expected 'good' or 'bad'.")
            continue
        
        if output is None:
            continue
        
        # Check if bisect is finished by looking for the "bisect finished" message
        if "bisect finished" in output or "is the first bad commit" in output:
            print("Bisect finished. The first bad commit has been found.")
            break
         
                 
def CopyJsontoHost():
    source_file = 'BinaryTool.json'
    destination_file = os.path.join(network_path, os.path.basename(source_file))
    shutil.copy(source_file, destination_file)


#Copy Json file to Host Machine
network_file_path = r'\\BASBSLAB019\Samples\Endofexecution.txt'
CopyJsontoHost()

# Start the git bisect process
git_bisect_start(good_commit, bad_commit)

# Now manually process git bisect with user input
git_bisect_manual(network_file_path)

# Reset the bisect process after completion
run_command(['git', 'bisect', 'reset'])