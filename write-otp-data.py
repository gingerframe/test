"""This script uses the FPLI to communicate with the application firmware on a device connected to the PC via an RS-485 port."""

import sys
import argparse
import subprocess
import os

if __name__ == "__main__":
    """
    The script starts the FPLI in command line mode which repeatedly sends the Maintenance protocol connect command (see 'Maintenance Protocol ICD') to the application firmware. The application
    firmware on a newly manufactured device should not have any configuration data programmed, it will therefore be waiting in maintenance mode looking for this connect command. Once the FPLI has
    established communication with the device the OTP data is written.

    Note that no output is displayed whilst the FPLI is attempting to connect to the device, the FPLI output is buffering and will be displayed when the external executable terminates.
    """
    parser = argparse.ArgumentParser(description='A script which communicates with the bootloader firmware on an attached device to program an application firmware image')
    parser.add_argument('port', help="The serial port to which the device is connected")
    parser.add_argument('device', help="The name of the connected device")
    parser.add_argument('serial', help="The serial number which is to be written to the connected device")
    parser.add_argument('ecckey', help="The relative path to the factory-locked configuration data signing key PEM file which is to be written to the connected device")
    args = parser.parse_args()

    fpli_stdout = ''

    try:
        print('Using the FPLI to communicate with the application firmware on device \'' + args.device + '\' connected to \'' + args.port + '\' to program OTP data:')
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # noinspection PyProtectedMember
            fpli_exe = sys._MEIPASS + r"/Boldre Factory Programming and Licensing Interface.exe"  # pylint: disable=no-member
            
        else:
            # noinspection PyPep8
            r"../sw-2864-boldre-factory-programming-and-licensing-interface/boldre-factory-programming-and-licensing-interface/bin/x86/Release/Boldre Factory Programming and Licensing Interface.exe"

        fpli_stdout = subprocess.check_output([fpli_exe, "-c" + args.port[3:], "write_otp", args.serial, args.ecckey], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print(fpli_stdout)
        sys.exit('Could not write OTP data to device.')
    else:
        print(fpli_stdout)
        if 'Error' in fpli_stdout:
            sys.exit('Could not write OTP data to device.')
        print('Process succeeded, OTP data has been programmed.')
