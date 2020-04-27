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

class Window(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.title = 'SW 2876 Boldre Factory Tools Device Configuration GUI'
        self.initUI()

    def initUI(self):

        self.setWindowTitle(self.title)
        windowLayout = QGridLayout()

        #COMPort Groupbox-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        '''Select serial port to open'''

        connect_box = QGroupBox()
        layout_connect_box = QVBoxLayout()

        self.ports_label = QLabel('Select Device Serial Port:')
        self.ports_cb = QComboBox()

        ports = (serial.tools.list_ports.comports())
        ports_list = []
        for port, desc, hwid in sorted(ports):
            ports_list.append("{}: {}".format(port, desc))
        for port in ports_list:
            self.ports_cb.addItem(port)

        layout_connect_box.addWidget(self.ports_label)
        layout_connect_box.addWidget(self.ports_cb)
        layout_connect_box.addStretch(1)

        connect_box.setLayout(layout_connect_box)

        #directory groupbox------------------------------------------------------------------------------------------------------------------------------------------------------
        
        '''States current directory and gives option to change directory'''

        dir_settings = QGroupBox()
        layout_dir_settings = QVBoxLayout() 

        folder = os.path.normpath(os.path.expanduser("~/"))

        self.dir_label = QLabel('Config File Directory')
        self.dir_selected = QLineEdit()
        self.files_label = QLabel('files selected (to write to unit)')
        self.files_selected  = QLineEdit()
        self.change_dir_button = QPushButton('change directory')

        self.dir_selected.setText(folder)
        self.files_selected.setText(folder)
        self.change_dir_button.clicked.connect(self.change_dir)

        layout_dir_settings.addWidget(self.dir_label)
        layout_dir_settings.addWidget(self.dir_selected)
        layout_dir_settings.addWidget(self.change_dir_button)
        layout_dir_settings.addStretch(-1)

        dir_settings.setLayout(layout_dir_settings)

        #available dih files groupbox----------------------------------------------------------------------------------------------------------------------------------------------------

        '''searches current directory from groupbox above and lists all files beginning with fl and ending with .json'''

        dih_files_box = QGroupBox()
        layout_dih_files_box = QVBoxLayout()

        self.dih_files_label = QLabel('Available dih Files')
        self.dih_files_text = QPlainTextEdit()

        for file in self.find_available_files('nvm'):
            self.dih_files_text.appendPlainText(file)

        self.dih_files_text.setReadOnly(True)

        layout_dih_files_box.addWidget(self.dih_files_label)
        layout_dih_files_box.addWidget(self.dih_files_text)
        layout_dih_files_box.addStretch(-1)

        dih_files_box.setLayout(layout_dih_files_box)

        #available fl files groupbox----------------------------------------------------------------------------------------------------------------------------------------------------

        '''searches current directory from groupbox above and lists all files beginning with fl and ending with .json'''

        fl_files_box = QGroupBox()
        layout_fl_files_box = QVBoxLayout()

        self.fl_files_label = QLabel('Available Factory Locked Files')
        self.fl_files_text = QPlainTextEdit()

        for file in self.find_available_files('fl'):
            self.fl_files_text.appendPlainText(file)

        self.fl_files_text.setReadOnly(True)

        layout_fl_files_box.addWidget(self.fl_files_label)
        layout_fl_files_box.addWidget(self.fl_files_text)
        layout_fl_files_box.addStretch(-1)

        fl_files_box.setLayout(layout_fl_files_box)

        #available um files groupbox----------------------------------------------------------------------------------------------------------------------------------------------------

        '''searches current directory from groupbox above and lists all files beginning with um and ending with .json'''

        um_files_box = QGroupBox()
        layout_um_files_box = QVBoxLayout()

        self.um_files_label = QLabel('Available User Modifiable Files')
        self.um_files_text = QPlainTextEdit()

        for file in self.find_available_files('um'):
            self.um_files_text.appendPlainText(file)

        self.um_files_text.setReadOnly(True)

        layout_um_files_box.addWidget(self.um_files_label)
        layout_um_files_box.addWidget(self.um_files_text)
        layout_um_files_box.addStretch(1)

        um_files_box.setLayout(layout_um_files_box)

        #Write files groupbox-----------------------------------------------------------------------------------------------------------------------------------------------------------

        '''key selection
        choose file number to write for each file
        cannot write before key is selected
        QLineEdit autofills box with available numbers'''
       
        write_files_gb = QGroupBox()
        layout_write_files_gb = QVBoxLayout()

        self.select_key_button = QPushButton('select key')
        self.key_label = QLabel('key selected:')
        self.key_selection = QLineEdit()
        self.number_label_dih = QLabel('NVM Device Info Header file number:')
        self.number_lineedit_dih = QLineEdit()
        self.number_label_fl = QLabel('Factory locked file number:')
        self.number_lineedit_fl = QLineEdit()
        self.number_label_um = QLabel('User modifiable file number')
        self.number_lineedit_um = QLineEdit()
        self.completer_dih = QCompleter()
        self.completer_fl = QCompleter()
        self.completer_um = QCompleter()
        self.write_button = QPushButton('write to device')

        model_dih = QtCore.QStringListModel()
        self.completer_dih.setModel(model_dih)
        self.get_completion_data(model_dih, datatype ='nvm')

        model_fl = QtCore.QStringListModel()
        self.completer_fl.setModel(model_fl)
        self.get_completion_data(model_fl, datatype='fl')

        model_um = QtCore.QStringListModel()
        self.completer_um.setModel(model_um)
        self.get_completion_data(model_um, datatype='um')
        
        self.select_key_button.clicked.connect(self.select_key_action)
        self.key_selection.setReadOnly(True)
        self.number_lineedit_fl.setCompleter(self.completer_fl)
        self.number_lineedit_um.setCompleter(self.completer_um)
        self.number_lineedit_dih.setCompleter(self.completer_dih)
        self.write_button.clicked.connect(self.write_to_device)
        self.write_button.setEnabled(False)

        layout_key = QHBoxLayout()
        layout_write_fl_files = QHBoxLayout()
        layout_write_um_files = QHBoxLayout()
        layout_write_dih_files = QHBoxLayout()
       
        layout_key.addWidget(self.select_key_button)
        layout_key.addWidget(self.key_selection)

        write_files_fl_widgets = [self.number_label_fl, self.number_lineedit_fl]
        write_files_um_widgets = [self.number_label_um, self.number_lineedit_um]
        write_files_dih_widgtes = [self.number_label_dih, self.number_lineedit_dih]

        for widget in write_files_fl_widgets:
            layout_write_fl_files.addWidget(widget)

        for widget in write_files_um_widgets:
            layout_write_um_files.addWidget(widget)

        for widget in write_files_dih_widgtes:
            layout_write_dih_files.addWidget(widget)

        layout_write_files_gb.addLayout(layout_key)
        layout_write_files_gb.addLayout(layout_write_fl_files)
        layout_write_files_gb.addLayout(layout_write_um_files) 
        layout_write_files_gb.addLayout(layout_write_dih_files)
        layout_write_files_gb.addWidget(self.write_button)
     
        layout_write_files_gb.addStretch(1)

        write_files_gb.setLayout(layout_write_files_gb)

        #activity log groupbox---------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        activity_log_gb = QGroupBox()
        layout_activity_log_gb = QVBoxLayout()

        self.textbox = QPlainTextEdit()

        self.textbox.setReadOnly(True)

        layout_activity_log_gb.addWidget(self.textbox)

        activity_log_gb.setLayout(layout_activity_log_gb)

        #window grid layout---------------------------------------------------------------------------------------------------------------------------------------------------------------------

        windowLayout.addWidget(connect_box, 0, 0)
        windowLayout.addWidget(write_files_gb, 0, 2)
        windowLayout.addWidget(dir_settings, 0, 1)
        windowLayout.addWidget(dih_files_box, 2, 0, 1, 1)
        windowLayout.addWidget(fl_files_box, 2, 1, 1, 1)
        windowLayout.addWidget(um_files_box, 2, 2, 1, 1)
        windowLayout.addWidget(activity_log_gb, 0, 3, 3, 1)

        self.setLayout(windowLayout)
        self.show()

    def change_dir(self):

        '''opens up QFileDialog and prompts to select directory
        updates available files in groupbox below'''

        default = self.dir_selected.text()
        chosen_dir = str(QFileDialog.getExistingDirectory(self, "Select Directory", default))
        self.dir_selected.setText(chosen_dir)
        self.um_files_text.clear()
        self.fl_files_text.clear()
        self.dih_files_text.clear()
        files_fl = self.find_available_files('fl')
        for file in files_fl:
            self.fl_files_text.appendPlainText(file)
        files_um = self.find_available_files('um')
        for file in files_um:
            self.um_files_text.appendPlainText(file)
        files_dih = self.find_available_files('nvm')
        for file in files_dih:
            self.dih_files_text.appendPlainText(file)

    def select_key_action(self):

        '''opens up QFileDialog and prompts to select key file - only shows txt files
        Once key has been selected, write file button becomes enabled'''

        default = self.dir_selected.text()
        chosen_key = (QFileDialog.getOpenFileName(self, "Select key file", '*.txt', default))[0]
        self.key_selection.setText(str(chosen_key))     
        self.write_button.setEnabled(True)

    def find_available_files(self, datatype):

        '''returns list of files in directory selected ending with .json and starting with given datatype)'''

        search_folder = self.dir_selected.text()
        os.chdir(search_folder)
        files = glob.glob('{}*.json'.format(datatype))
        print(files)
        return files

    def get_completion_data(self, model, datatype):

        '''searches for possible file numbers and adds them to auto complete list in write files groupbox'''

        files_list = self.find_available_files(datatype)

        numbers_list = []

        for file in files_list:
            numbers_list.append(str((re.findall(r'\d+', file)))[2:6])
    
        model.setStringList(numbers_list)

    def write_to_device(self):

        '''uses writeconfigurationdata to run FPLI commands'''

        direc = self.dir_selected.text()

        dih_filename = 'nvm-dih-{}'.format(str(self.number_lineedit_dih.text()))
        fl_filename = 'fl-section-{}'.format(str(self.number_lineedit_fl.text()))
        um_filename = 'um-section-{}'.format(str(self.number_lineedit_um.text()))

        files = glob.glob('{}/*.json'.format(direc))

        dih_file = ''
        fl_file = ''
        um_file = ''

        for file in files:
            if file == '{}\\{}.json'.format(direc, fl_filename):
                fl_file = file.replace("\\", "/")
            if file == '{}\\{}.json'.format(direc, um_filename):
                um_file = file.replace("\\", "/")
            if file == '{}\\{}.json'.format(direc, dih_filename):
                dih_file = file.replace("\\", "/")

        files_not_found = []

        if dih_file == '':
            files_not_found.append('{}\\{}.json'.format(direc, dih_filename))
        if um_file == '':
            files_not_found.append('{}\\{}.json'.format(direc, um_filename))
        if fl_file == '':
            files_not_found.append('{}\\{}.json'.format(direc, fl_filename))

        if files_not_found != []: 
            self.textbox.appendPlainText('Error: Could not find the following files:\n{}'.format('\n'.join(files_not_found)))
            msg = QMessageBox()     
            msg.setIcon(3)
            msg.setText("File does not exist in current directory")
            msg.setInformativeText('Could not find the following files:\n{}'.format('\n'.join(files_not_found)))
            msg.setWindowTitle("Error")
            msg.exec_()

        else:
            self.textbox.appendPlainText('Attemping to write following files to device:\n{}\n{}\n{}\n\n'.format(dih_file, um_file, fl_file))

            com_text = str(self.ports_cb.currentText())
            com = com_text[3]

            ecckey = self.key_selection.text()

            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            os.system('write-configuration-data.py "COM{}" "device" "{}" "{}" "{}" "{}"'.format(com, ecckey, dih_file, fl_file, um_file))

            #check?
            self.textbox.appendPlainText('Process succeeded, configuration data has been programmed.')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    screen = Window()
    screen.show()
    sys.exit(app.exec_())