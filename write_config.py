from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
import sys
import os
import serial
import serial.tools.list_ports
import glob
import re
import shutil
import subprocess
import datetime


class writeconfigurationdata(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.fpli_script_filename = "temp_fpli_cli_script.txt"
        self.fpli_stdout = ''
        self.dst = r"C:/Users/ginger frame"

    def cache_file_if_exists(self, file_path):
        """
        The FPLI doesn't handle paths with spaces in, make a local duplicate of the existing file
        """
        dst = r"C:/Users/ginger frame"

        if os.path.exists(file_path):
            src = os.path.realpath(file_path) 
            shutil.copy2(src, './temp')
            print(os.path.basename(file_path))
            return os.path.basename(file_path)
        else:
            print('error')
            sys.exit('Could not write configuration data to device, "' + file_path + '" does not exist.')
    
    def delete_file_if_exists(self, file_path):
        """
        This function can be used to deleted temporary files without erroring
        """
        # noinspection PyBroadException,PyPep8
        try:
            os.remove(file_path)
        except:
            pass

    def script_dih(self, dih):
        dih_file = self.cache_file_if_exists(self, dih)
        script = 'write_dih {}'.format(dih_file) 
        return script

    def script_flconf(self, ecckey, flconf):
        flconf_file = self.cache_file_if_exists(self, flconf)
        ecckey_file = self.cache_file_if_exists(self, ecckey)
        script = 'write_fl {} {}'.format(flconf_file, ecckey_file)
        return script

    def script_um(self, umconf):
        print(umconf)
        umconf_file = self.cache_file_if_exists(self, umconf)
        script = 'write_um {}'.format(umconf_file)
        return script

    def run(self, script, port, dst):

        os.chdir(dst)

        try:
            fpli_script = script
            fpli_script_file = open(self.fpli_script_filename, "w")
            fpli_script_file.write(fpli_script)
            fpli_script_file.close()
            print('Using the FPLI to communicate with the application firmware on device')
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # noinspection PyProtectedMember
                fpli_exe = sys._MEIPASS + r"/Boldre Factory Programming and Licensing Interface.exe"  # pylint: disable=no-member
            else:
                # noinspection PyPep8
                fpli_exe = self.dst + "/sw-2864-boldre-factory-programming-and-licensing-interface/boldre-factory-programming-and-licensing-interface/bin/x86/Release/Boldre Factory Programming and Licensing Interface.exe"
                print(os.path.abspath(fpli_exe))
            fpli_script_filename = os.path.abspath(self.fpli_script_filename)
            print(os.path.abspath(self.fpli_script_filename))
            fpli_stdout = subprocess.check_output([fpli_exe, "-c" + port, "script", fpli_script_filename], stderr=subprocess.STDOUT, cwd=".")
        except subprocess.CalledProcessError:
            print(fpli_stdout.decode('latin_1').encode('utf_8'))
            sys.exit('Could not write configuration data to device.')
        else:   
            print(fpli_stdout.decode('latin_1').encode('utf_8'))
            if 'Error' in fpli_stdout.decode('latin_1'):
                sys.exit('Could not write configuration data to device.')
            print('Process succeeded, configuration data has been programmed.')
        finally:
            lambda: self.delete_file_if_exists('./temp')
            lambda: self.delete_file_if_exists(fpli_script_filename)

class DataCaptureThread(QtCore.QThread):
    """reads data from anemometer in separate thread
    and emits a string of the data"""
    update_anemometer_log = QtCore.pyqtSignal(str)

    def __init__(self, vcp, *args, **kwargs):
        QtCore.QThread.__init__(self, *args, **kwargs)
        # setup required variables
        self.vcp = vcp
        self.data_pause = False
        self.stop_timer = False

    def collect_data(self):
        """reads data from anemometer, strips leading and trailing characters,
         time stamp and emits to main thread"""
        self.vcp.read(self.vcp.inWaiting())
        while True:
            data = self.vcp.readline()
            data = data.decode("ASCII")
            timestamp = "," + datetime.datetime.now().strftime("%H:%M:%S")
            data_timestamp = data + timestamp
            if not self.data_pause:
                self.update_anemometer_log.emit(data_timestamp)
            if self.stop_timer:
                break

    def display_data(self, condition):
        """pauses/resumes display of data"""
        if condition:
            self.data_pause = False
        else:
            self.data_pause = True

    def data_collect_stop(self):
        """stops data collection timer"""
        self.stop_timer = True

    def run(self):
        """initiates collect data function"""
        self.collect_data()
              

class Window(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.title = 'write configuration data'
        self.anemometer_vcp = None
        self.initUI()

    def initUI(self):

        self.setWindowTitle(self.title)
        windowLayout = QGridLayout()

        #COMPort Groupbox-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        '''Connect/Disconnect to anemometer by selecting serial port and baud rate. Contains button to read data output'''

        connect_box = QGroupBox()
        layout_connect_box = QVBoxLayout()

        ports_label = QLabel('Select serial port:')
        self.ports_cb = QComboBox()
        baud_label = QLabel('Select baud rate:')
        self.baud_cb = QComboBox()
        self.connect_button = QPushButton('Connect')
        self.disconnect_button = QPushButton('Disconnect')
        self.read_data_button = QPushButton('Read data from unit')
        self.stop_reading_button = QPushButton('Stop reading data')

        ports = (serial.tools.list_ports.comports())
        ports_list = []
        for port, desc, hwid in sorted(ports):
            #print("{}: {} [{}]".format(port, desc, hwid))
            ports_list.append("{}: {}".format(port, desc))
        for port in ports_list:
            self.ports_cb.addItem(port)

        baud_rates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        for rate in baud_rates:
            self.baud_cb.addItem(str(rate))
        self.baud_cb.setCurrentIndex(5)

        self.connect_button.clicked.connect(self.connect_action)
        self.disconnect_button.clicked.connect(self.disconnect_action)
        self.disconnect_button.hide()
        self.read_data_button.clicked.connect(self.read_data_action)
        self.read_data_button.setEnabled(False)
        self.stop_reading_button.hide()
        self.stop_reading_button.clicked.connect(self.stop_reading_action)
           
        layout_select_comport = QHBoxLayout()
        layout_select_baud_rate = QHBoxLayout()

        layout_select_comport.addWidget(ports_label)
        layout_select_comport.addWidget(self.ports_cb)
        layout_select_comport.addStretch(1)

        layout_select_baud_rate.addWidget(baud_label)
        layout_select_baud_rate.addWidget(self.baud_cb)
        layout_select_baud_rate.addStretch(1)

        layout_connect_box.addLayout(layout_select_comport)
        layout_connect_box.addLayout(layout_select_baud_rate)
        layout_connect_box.addWidget(self.connect_button)
        layout_connect_box.addWidget(self.disconnect_button)
        layout_connect_box.addWidget(self.read_data_button)
        layout_connect_box.addWidget(self.stop_reading_button)
        layout_connect_box.addStretch(-1)

        connect_box.setLayout(layout_connect_box)

        #directory groupbox------------------------------------------------------------------------------------------------------------------------------------------------------
        
        '''States current directory and gives option to change directory'''

        dir_settings = QGroupBox()
        layout_dir_settings = QVBoxLayout() 

        folder = "C:/Users/ginger frame/FPLI Files/example files"

        self.dir_label = QLabel('current directory')
        self.dir_selected = QLineEdit()
        files_label = QLabel('files selected (to write to unit)')
        files_selected  = QLineEdit()
        change_dir_button = QPushButton('change directory')

        self.dir_selected.setText("C:/Users/ginger frame/FPLI Files/example files")
        files_selected.setText(folder)
        change_dir_button.clicked.connect(self.change_dir)

        layout_dir_settings.addWidget(self.dir_label)
        layout_dir_settings.addWidget(self.dir_selected)
        layout_dir_settings.addWidget(change_dir_button)
        layout_dir_settings.addStretch(-1)

        dir_settings.setLayout(layout_dir_settings)

        #available fl files groupbox----------------------------------------------------------------------------------------------------------------------------------------------------

        '''searches current directory from groupbox above and lists all files beginning with fl and ending with .json'''

        fl_files_box = QGroupBox()
        fl_files_box.setFixedWidth(170)
        layout_fl_files_box = QVBoxLayout()

        fl_files_label = QLabel('available factory locked files')
        self.fl_files_text = QPlainTextEdit()

        for file in self.find_available_files('fl'):
            self.fl_files_text.appendPlainText(file)

        self.fl_files_text.setReadOnly(True)

        layout_fl_files_box.addWidget(fl_files_label)
        layout_fl_files_box.addWidget(self.fl_files_text)
        layout_fl_files_box.addStretch(-1)

        fl_files_box.setLayout(layout_fl_files_box)

        #available um files groupbox----------------------------------------------------------------------------------------------------------------------------------------------------

        '''searches current directory from groupbox above and lists all files beginning with um and ending with .json'''

        um_files_box = QGroupBox()
        layout_um_files_box = QVBoxLayout()

        um_files_box.setFixedWidth(170)

        um_files_label = QLabel('available user modifiable files')
        self.um_files_text = QPlainTextEdit()

        for file in self.find_available_files('um'):
            self.um_files_text.appendPlainText(file)

        self.um_files_text.setReadOnly(True)

        layout_um_files_box.addWidget(um_files_label)
        layout_um_files_box.addWidget(self.um_files_text)
        layout_um_files_box.addStretch(1)

        um_files_box.setLayout(layout_um_files_box)

        #Write files groupbox-----------------------------------------------------------------------------------------------------------------------------------------------------------

        '''key selection
        choose file number to write (fl or um)
        cannot write fl file before key is selected
        QLineEdit autofills box with available numbers'''
       
        write_files_gb = QGroupBox()
        layout_write_files_gb = QVBoxLayout()

        select_key_button = QPushButton('select key')
        key_label = QLabel('key selected:')
        self.key_selection = QLineEdit()
        number_label_fl = QLabel('Factory locked file number:')
        self.number_lineedit_fl = QLineEdit()
        self.number_button_fl = QPushButton('write to device')
        number_label_um = QLabel('User modifiable file number')
        self.number_lineedit_um = QLineEdit()
        self.number_button_um = QPushButton('write to device')
        completer_fl = QCompleter()
        completer_um = QCompleter()
        self.reset_button = QPushButton('Reset Anemometer')

        model_fl = QtCore.QStringListModel()
        completer_fl.setModel(model_fl)
        self.get_completion_data(model_fl, datatype='fl')

        model_um = QtCore.QStringListModel()
        completer_um.setModel(model_um)
        self.get_completion_data(model_um, datatype='um')
        
        select_key_button.clicked.connect(self.select_key_action)
        self.key_selection.setReadOnly(True)
        self.number_button_fl.setEnabled(False)
        self.number_button_fl.clicked.connect(lambda: self.write_to_device('fl'))
        self.number_lineedit_fl.setCompleter(completer_fl)
        self.number_button_um.clicked.connect(lambda: self.write_to_device('um'))
        self.number_lineedit_um.setCompleter(completer_um)
        self.reset_button.setEnabled(False)
        self.reset_button.clicked.connect(self.reset_action)

        layout_key = QHBoxLayout()
        layout_write_fl_files = QHBoxLayout()
        layout_write_um_files = QHBoxLayout()
       
        layout_key.addWidget(select_key_button)
        layout_key.addWidget(self.key_selection)

        write_files_fl_widgets = [number_label_fl, self.number_lineedit_fl, self.number_button_fl]
        write_files_um_widgets = [number_label_um, self.number_lineedit_um, self.number_button_um]

        for widget in write_files_fl_widgets:
            layout_write_fl_files.addWidget(widget)

        for widget in write_files_um_widgets:
            layout_write_um_files.addWidget(widget)

        layout_write_files_gb.addLayout(layout_key)
        layout_write_files_gb.addLayout(layout_write_fl_files)
        layout_write_files_gb.addLayout(layout_write_um_files)      
        layout_write_files_gb.addWidget(self.reset_button)

        layout_write_files_gb.addStretch(1)

        write_files_gb.setLayout(layout_write_files_gb)

        #activity log groupbox---------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        activity_log_gb = QGroupBox()
        layout_activity_log_gb = QVBoxLayout()

        self.textbox = QPlainTextEdit()

        self.textbox.setReadOnly(True)

        layout_activity_log_gb.addWidget(self.textbox)

        activity_log_gb.setLayout(layout_activity_log_gb)

        #data output groupbox------------------------------------------------------------------------------------------------------------------------------------------------
        
        data_output_gb = QGroupBox('Output from Anemometer')
        data_output_gb.setFixedHeight(300)
        layout_data_output_gb = QVBoxLayout()

        self.data_log = QPlainTextEdit()

        self.data_log.setReadOnly(True)

        layout_data_output_gb.addWidget(self.data_log)

        data_output_gb.setLayout(layout_data_output_gb)

        #window grid layout---------------------------------------------------------------------------------------------------------------------------------------------------------------------

        windowLayout.addWidget(connect_box, 0, 0, 1, 2)
        windowLayout.addWidget(dir_settings, 1, 0, 1, 2)
        windowLayout.addWidget(fl_files_box, 2, 0, 1, 1)
        windowLayout.addWidget(um_files_box, 2, 1, 1, 1)
        windowLayout.addWidget(write_files_gb, 0, 2)
        windowLayout.addWidget(activity_log_gb, 1, 2, 2, 1)
        windowLayout.addWidget(data_output_gb, 3, 0, 2, 3)

        self.setLayout(windowLayout)
        self.show()

    def find_available_files(self, datatype):

        '''returns list of files in directory selected ending with .json and starting with given datatype)'''

        search_folder = self.dir_selected.text()
        os.chdir(search_folder)
        files = glob.glob('{}*.json'.format(datatype))
        return files

    def get_completion_data(self, model, datatype):

        '''searches for possible file numbers and adds them to auto complete list in write files groupbox'''
        
        if datatype == 'fl':
            files_list = self.find_available_files('fl')

        if datatype =='um':
            files_list = self.find_available_files('um')

        numbers_list = []

        for file in files_list:
            numbers_list.append(str((re.findall(r'\d+', file)))[2:6])
    
        model.setStringList(numbers_list)

    def connect_action(self):

        '''checks if anemometer is connected properly 
        success message box appears only if output can be read from anemometer 
        otherwise error box appears'''

        success_msg = QMessageBox()
        success_msg.setIcon(QMessageBox.Information)
        success_msg.setText("Anemometer Connected")
        success_msg.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        success_msg.setStandardButtons(QMessageBox.Ok)

        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setText("Cannot Connect to Anemometer")
        error_msg.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        error_msg.setStandardButtons(QMessageBox.Ok)

        com_text = str(self.ports_cb.currentText())
        com = com_text[0:4]
        
        baud = str(self.baud_cb.currentText())

        self.textbox.appendPlainText("Attempting connection to Anemometer on: {}\nwith baud rate: {}".format(com, baud))

        try:
            self.anemometer_vcp = serial.Serial(com, baud, bytesize = 8, timeout=2, rtscts=True, dsrdtr=True)
            self.textbox.appendPlainText("{} open".format(com))
            test = self.anemometer_vcp.readline()
            #self.textbox.appendPlainText("Read line from anemometer: " + test.decode())
            if test:
                self.textbox.appendPlainText("Anemometer connected")
                success_msg.exec_()
                self.connect_button.hide()
                self.disconnect_button.show()   
                self.read_data_button.setEnabled(True)
            else:
                self.textbox.appendPlainText("No data output from anemometer.... closing port\n")
                error_msg.exec_()
                self.anemometer_vcp.close()
                self.read_data_button.setEnabled(False)
          
        except (serial.SerialException, ValueError, UnicodeDecodeError, IndexError) as e:
            self.textbox.appendPlainText(str(e))
            error_msg.exec_()
            if self.anemometer_vcp is not None:
                self.anemometer_vcp.close()

    def disconnect_action(self):

        '''attempts to disconnect anemometer'''

        try:
            self.anemometer_vcp.close()
            self.textbox.appendPlainText("Anemometer disconnected")
            self.disconnect_button.hide()
            self.connect_button.show()
            self.read_data_button.setEnabled(False)
        except (serial.SerialException, ValueError, AttributeError) as e:
            self.textbox.appendPlainText(str(e))
        self.anemometer_vcp = None

    def change_dir(self):

        '''opens up QFileDialog and prompts to select directory
        updates available files in groupbox below'''

        default = self.dir_selected.text()
        chosen_dir = str(QFileDialog.getExistingDirectory(self, "Select Directory", default))
        self.dir_selected.setText(chosen_dir)
        self.um_files_text.clear()
        self.fl_files_text.clear()
        files_fl = self.find_available_files('fl')
        for file in files_fl:
            self.fl_files_text.appendPlainText(file)
        files_um = self.find_available_files('um')
        for file in files_um:
            self.um_files_text.appendPlainText(file)

    def select_key_action(self):

        '''opens up QFileDialog and prompts to select key file - only shows txt files
        Once key has been selected, reset and wrte fl file buttons become enabled'''

        default = self.dir_selected.text()
        chosen_key = (QFileDialog.getOpenFileName(self, "Select key file", '*.txt', default))[0]
        print(chosen_key)
        self.key_selection.setText(str(chosen_key))     
        self.number_button_fl.setEnabled(True)
        self.reset_button.setEnabled(True)

    def write_to_device(self, datatype):

        '''uses writeconfigurationdata to run FPLI commands'''

        try:
            self.anemometer_vcp.close()

        except:
            pass

        selected_file = ''
        files_list = self.find_available_files(datatype)

        if datatype == 'fl':
            number = str(self.number_lineedit_fl.text())

        if datatype == 'um':
            number = str(self.number_lineedit_um.text())

        for file in files_list:
            if number == str(re.findall(r'\d+', file))[2:6]:
                selected_file = file
                
        if selected_file == '':
            self.textbox.appendPlainText('Error: Could not find file number {}'.format(number))
            msg = QMessageBox()     
            msg.setIcon(3)
            msg.setText("File does not exist in current directory")
            msg.setInformativeText("Could not find file number {}".format(number))
            msg.setWindowTitle("Error")
            msg.exec_()

        else:
            com_text = str(self.ports_cb.currentText())
            com = com_text[3]
            print(com)

            self.textbox.appendPlainText('Attemping to write following file to anemometer:\n{}'.format(selected_file))
            file = os.path.abspath(selected_file)
            self.key = (r"C:\Users\ginger frame\sw-2876-boldre-factory-tools\example files\CK20040097.txt")
            if datatype == 'fl':
                script = writeconfigurationdata.script_flconf(writeconfigurationdata, key, selected_file)   
            if datatype == 'um':
                script = writeconfigurationdata.script_um(writeconfigurationdata, selected_file)
            self.textbox.appendPlainText("Command: {}".format(script))
            t = writeconfigurationdata()
            writeconfigurationdata.run(t, script, com)

    def read_data_action(self):
        self.anemometer_data_thread = DataCaptureThread(self.anemometer_vcp)
        self.anemometer_data_thread.start()
        self.anemometer_data_thread.update_anemometer_log.connect(self.anemometer_update)
        self.number_button_fl.setEnabled(False)
        self.number_button_um.setEnabled(False)
        self.read_data_button.hide()
        self.stop_reading_button.show()

    def stop_reading_action(self):
        self.stop_reading_button.hide()
        self.read_data_button.show()
        self.number_button_fl.setEnabled(True)
        self.number_button_um.setEnabled(True)
        self.anemometer_data_thread.data_collect_stop()
        #self.anemometer_data_thread.finished.connect(self.close_vcp)
        self.anemometer_data_thread.quit()
        self.anemometer_data_thread = None

    def anemometer_update(self, anemometer_output):
        """update anemometer log with anemometer readings"""
        self.data_log.appendPlainText(anemometer_output)

    def reset_action(self):

        com_text = str(self.ports_cb.currentText())
        com = com_text[3]

        key = (r"C:\Users\ginger frame\sw-2876-boldre-factory-tools\example files\CK20040097.txt")

        default = self.dir_selected.text()
        vanilla_folder = str(QFileDialog.getExistingDirectory(self, "Select vanilla config folder", default))

        vanilla_dih = ('{}/nvm-dih.json'.format(vanilla_folder))
        vanilla_um = ('{}/um-section.json'.format(vanilla_folder))
        vanilla_fl = ('{}/fl-section.json'.format(vanilla_folder))

        dih_script = writeconfigurationdata.script_dih(writeconfigurationdata, vanilla_dih)
        um_script = writeconfigurationdata.script_um(writeconfigurationdata, vanilla_um)
        fl_script = writeconfigurationdata.script_flconf(writeconfigurationdata, key, vanilla_fl)
        swap_script = 'swap'

        script = '\n'.join([dih_script, um_script, fl_script, swap_script, dih_script, um_script, fl_script, swap_script])

        self.textbox.appendPlainText("Command: {}".format(script))
        t = writeconfigurationdata()
        writeconfigurationdata.run(t, script, com, vanilla_folder)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    screen = Window()
    screen.show()
    sys.exit(app.exec_())