"""This script uses the FPLI to communicate with the application firmware on a device connected to the PC via an RS-485 port."""

import sys
import os
import shutil
import argparse
import subprocess

fpli_script = """# Write the application firmware NVM device info header (DIH) to the device
write_dih <SUB_DIH>

# Write the factory-locked (FL) section of the application firmware configuration data to the device
write_fl <SUB_FL> <SUB_PEM>

# Write the user-modifiable (UM) section of the application firmware configuration data to the device
write_um <SUB_UM>

# Swap the active bank of configuration data in the device. This is neccessary to apply configuration changes as writes to the FL and UM sections are always applied to the inactive bank.
swap

# Write the factory-locked (FL) section of the application firmware configuration data to the device
write_fl <SUB_FL> <SUB_PEM>

# Write the user-modifiable (UM) section of the application firmware configuration data to the device
write_um <SUB_UM>

# Swap the active bank of configuration data in the device. This is neccessary to apply configuration changes as writes to the FL and UM sections are always applied to the inactive bank.
swap"""

fpli_script_filename = "temp_fpli_cli_script.txt"


def cache_file_if_exists(file_path):
    """
    The FPLI doesn't handle paths with spaces in, make a local duplicate of the existing file
    """
    if os.path.exists(file_path):
        src = os.path.realpath(file_path)
        shutil.copy2(src, '.')
        return os.path.basename(file_path)
    else:
        sys.exit('Could not write configuration data to device, "' + file_path + '" does not exist.')


def delete_file_if_exists(file_path):
    """
    This function can be used to deleted temporary files without erroring
    """
    # noinspection PyBroadException,PyPep8
    try:
        os.remove(file_path)
    except:
        pass


if __name__ == "__main__":
    """
    The script starts the FPLI in command line mode which repeatedly sends the Maintenance protocol connect command (see 'Maintenance Protocol ICD') to the application firmware. The application
    firmware on a newly manufactured device should not have any configuration data programmed, it will therefore be waiting in maintenance mode looking for this connect command. Once the FPLI has
    established communication with the device the FL and UM sections of the application firmware's configuration data is written.

    Note that no output is displayed whilst the FPLI is attempting to connect to the device, the FPLI output is buffering and will be displayed when the external executable terminates.
    """
    parser = argparse.ArgumentParser(description='A script which communicates with the application firmware on an attached device to program the configuration data')
    parser.add_argument('port', help="The serial port to which the device is connected")
    parser.add_argument('device', help="The name of the connected device")
    parser.add_argument('ecckey', help="The relative path to the factory-locked configuration data signing key PEM file which is associated with the connected device")
    parser.add_argument('dih', help="The relative path to the NVM device info header JSON file which is to be written to the connected device")
    parser.add_argument('flconf', help="The relative path to the factory-locked configuration data JSON file which is to be written to the connected device")
    parser.add_argument('umconf', help="The relative path to the user-modifiable configuration data JSON file which is to be written to the connected device")
    args = parser.parse_args()

    fpli_stdout = ''

    try:
        print('Checking configuration file paths and generating temporary FPLI script')
        fpli_script = fpli_script.replace('<SUB_PEM>', cache_file_if_exists(args.ecckey))
        fpli_script = fpli_script.replace('<SUB_DIH>', cache_file_if_exists(args.dih))
        fpli_script = fpli_script.replace('<SUB_FL>', cache_file_if_exists(args.flconf))
        fpli_script = fpli_script.replace('<SUB_UM>', cache_file_if_exists(args.umconf))
        fpli_script_file = open(fpli_script_filename, "w")
        fpli_script_file.write(fpli_script)
        fpli_script_file.close()
        print('Using the FPLI to communicate with the application firmware on device \'' + args.device + '\' connected to \'' + args.port + '\' to program configuration data:')
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # noinspection PyProtectedMember
            fpli_exe = sys._MEIPASS + r"/Boldre Factory Programming and Licensing Interface.exe"  # pylint: disable=no-member
        else:
            # noinspection PyPep8
            fpli_exe = r"../sw-2864-boldre-factory-programming-and-licensing-interface/boldre-factory-programming-and-licensing-interface/bin/x86/Release/Boldre Factory Programming and Licensing Interface.exe"
        fpli_script_filename = os.path.abspath(fpli_script_filename)
        fpli_stdout = subprocess.check_output([fpli_exe, "-c" + args.port[3:], "script", fpli_script_filename], stderr=subprocess.STDOUT, cwd=".")
    except subprocess.CalledProcessError:
        print(fpli_stdout.decode('latin_1').encode('utf_8'))
        sys.exit('Could not write configuration data to device.')
    else:
        print(fpli_stdout.decode('latin_1').encode('utf_8'))
        if 'Error' in fpli_stdout.decode('latin_1'):
            sys.exit('Could not write configuration data to device.')
        print('Process succeeded, configuration data has been programmed.')
    finally:
        delete_file_if_exists(os.path.basename(args.ecckey))
        delete_file_if_exists(os.path.basename(args.dih))
        delete_file_if_exists(os.path.basename(args.flconf))
        delete_file_if_exists(os.path.basename(args.umconf))
        delete_file_if_exists(fpli_script_filename)
