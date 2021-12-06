#!/usr/bin/env python3

import shutil
import time
from datetime import datetime

import wx
import os
import errno, sys
from configLibrary import Field, SettingsSection, SettingsController


ERROR_INVALID_NAME = 123
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
def getDirs(path):
    def innerIsDir(name):
        return os.path.isdir(os.path.join(path, name))
    return innerIsDir, os.listdir(path)

class ValidPath(str):
    def __new__(cls, content):
        return str.__new__(cls,  os.path.abspath(content))

    def __init__(self, path):
        self.valid = self.is_pathname_valid(path)
        self.exists_or_creatable = False
        self.exists = False
        self.type = False
        self.path = False
        self.absolute_path = False
        self.after_init(path)
        path = self.absolute_path or path
        super().__init__()

    def after_init(self,path):
        if self.valid:
            self.exists_or_creatable = self.is_path_exists_or_creatable(path)
            if self.exists_or_creatable:
                self.exists = os.path.exists(path)
                if self.exists:
                    is_directory = os.path.isdir(path)
                    if is_directory:
                        self.type = "dir"
                    else:
                        self.type = "file"
            else:
                self.exists = False
                self.type = False
            self.path = path
            self.absolute_path = os.path.abspath(path)

    def __abs__(self):
        return self.absolute_path

    def __str__(self):
        return self.absolute_path

    def __repr__(self):
        return self.absolute_path

    def get_folder_list(self,path):
        filter_method, iterable = getDirs(path)
        return list(map(ValidPath,map(lambda x: os.path.join(path,x),iterable)))

    def getContent(self):
        if not self.exists:
            return False
        if self.type == "dir":
            return self.get_folder_list(self.absolute_path)
        else:
            file = open(self.absolute_path)
            data = file.read()
            file.close()
            return data

    def create(self, path_type, default=False):
        if self.exists_or_creatable and not self.exists:
            if path_type == "dir":
                try:
                    os.mkdir(self.absolute_path)
                    self.after_init(self.path)
                except Exception as excp:
                    raise excp
            elif path_type == "file":
                try:
                    newfile = open(self.absolute_path, 'a+')  # open file in append mode
                    if default:
                        newfile.write(default)
                    else:
                        newfile.write("")
                    newfile.close()
                    self.after_init(self.path)
                except Exception as excp:
                    raise excp

    def is_pathname_valid(self,pathname):
        '''
        `True` if the passed pathname is a valid pathname for the current OS;
        `False` otherwise.
        '''
        try:
            if not isinstance(pathname, str) or not pathname:
                return False
            _, pathname = os.path.splitdrive(pathname)
            root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
                if sys.platform == 'win32' else os.path.sep
            assert os.path.isdir(root_dirname)
            root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep
            for pathname_part in pathname.split(os.path.sep):
                try:
                    os.lstat(root_dirname + pathname_part)
                except OSError as exc:
                    if hasattr(exc, 'winerror'):
                        if exc.winerror == ERROR_INVALID_NAME:
                            return False
                    elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                        return False
        except TypeError as exc:
            return False
        else:
            return True

    def is_path_creatable(self,pathname):
        '''
        `True` if the current user has sufficient permissions to create the passed
        pathname; `False` otherwise.
        '''
        dirname = os.path.dirname(pathname) or os.getcwd()
        return os.access(dirname, os.W_OK)

    def is_path_exists_or_creatable(self,pathname):
        '''
        `True` if the passed pathname is a valid pathname for the current OS _and_
        either currently exists or is hypothetically creatable; `False` otherwise.

        This function is guaranteed to _never_ raise exceptions.
        '''
        try:
            return self.is_pathname_valid(pathname) and (
                os.path.exists(pathname) or self.is_path_creatable(pathname))
        except OSError:
            return False


CONFIG_FILE_NAME = "folder_backup_creator.ini"
CONFIG_FILE_PATH = ValidPath(CONFIG_FILE_NAME)

class PathSettings(SettingsSection):
    save_directory_path = Field(default="None")
    backups_directory_path = Field(default="./saveBackups")

class Settings(SettingsController):
    PATHS = PathSettings()
    @property
    def save_path(self):
        return ValidPath(self.PATHS.save_directory_path)

    @property
    def backup_path(self):
        return ValidPath(self.PATHS.backups_directory_path)

    def init_paths(self):
        if self.backup_path.exists_or_creatable and not self.backup_path.exists:
            self.backup_path.create("dir")
        if self.paths_configured_correctly:
            return True, ""
        elif not self.save_path.exists:
            return False, "Save directory path does not exists"
        else:
            return False, "Unknown error"

    @property
    def paths_configured_correctly(self):
        return self.save_path.exists and self.save_path.type == "dir" and self.backup_path.exists and self.backup_path.type == "dir"







class SettingsDialog(wx.Dialog):

    def __init__(self, parent, save_path, backup_path):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Settings", pos = wx.DefaultPosition, size = wx.Size( 366,162 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE )
        self.SetIcon(wx.Icon(resource_path("icon.ico")))

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        settingsContainer = wx.BoxSizer( wx.VERTICAL )
        settingsFormFieldsContainer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Paths" ), wx.VERTICAL )
        settingsSaveDataContainer = wx.BoxSizer( wx.HORIZONTAL )
        settingsSaveDataContainer.SetMinSize( wx.Size( 2,-1 ) )
        self.settingsSaveDataLabel = wx.StaticText( settingsFormFieldsContainer.GetStaticBox(), wx.ID_ANY, u"Directory to Backup", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.settingsSaveDataLabel.Wrap( -1 )
        settingsSaveDataContainer.Add( self.settingsSaveDataLabel, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL|wx.FIXED_MINSIZE, 5 )
        self.settingsSaveDataField = wx.DirPickerCtrl( settingsFormFieldsContainer.GetStaticBox(), wx.ID_ANY, str(save_path) if save_path.exists else "", u"Select Directory you want to backup", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
        settingsSaveDataContainer.Add( self.settingsSaveDataField, 1, wx.ALL|wx.EXPAND, 5 )
        settingsFormFieldsContainer.Add( settingsSaveDataContainer, 0, wx.EXPAND, 5 )
        settingsBackupDirContainer = wx.BoxSizer( wx.HORIZONTAL )
        settingsBackupDirContainer.SetMinSize( wx.Size( 2,-1 ) )
        self.settingsBackupDirLabel = wx.StaticText( settingsFormFieldsContainer.GetStaticBox(), wx.ID_ANY, u"Where to Store Backups", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.settingsBackupDirLabel.Wrap( -1 )
        settingsBackupDirContainer.Add( self.settingsBackupDirLabel, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL|wx.FIXED_MINSIZE, 5 )
        self.settingsBackupDirField = wx.DirPickerCtrl( settingsFormFieldsContainer.GetStaticBox(), wx.ID_ANY, str(backup_path) if backup_path.exists else "", u"Where do you want backups to be saved?", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
        settingsBackupDirContainer.Add( self.settingsBackupDirField, 1, wx.ALL|wx.EXPAND, 5 )
        settingsFormFieldsContainer.Add( settingsBackupDirContainer, 0, wx.EXPAND, 5 )
        settingsFormFieldsContainer.Add( ( 0,  0), 1, 0, 0 )
        settingsContainer.Add( settingsFormFieldsContainer, 1, wx.EXPAND, 0 )
        settingsFormButtons = wx.StdDialogButtonSizer()
        self.settingsFormButtonsSave = wx.Button( self, wx.ID_SAVE )
        settingsFormButtons.AddButton( self.settingsFormButtonsSave )
        self.settingsFormButtonsCancel = wx.Button( self, wx.ID_CANCEL )
        settingsFormButtons.AddButton( self.settingsFormButtonsCancel )
        settingsFormButtons.Realize()
        self.Bind(wx.EVT_BUTTON, self.save, self.settingsFormButtonsSave)
        settingsContainer.Add( settingsFormButtons, 0, wx.ALIGN_RIGHT|wx.ALL|wx.FIXED_MINSIZE, 4 )
        self.SetSizer( settingsContainer )
        self.Layout()
        self.Centre( wx.BOTH )

    def save(self, event):
        save = ValidPath(self.settingsSaveDataField.Path)
        backups = ValidPath(self.settingsBackupDirField.Path)
        if self.settingsSaveDataField.Path and save.exists:
            self.Parent.settings.PATHS.save_directory_path = str(save)
        if self.settingsBackupDirField.Path and backups.exists:
            self.Parent.settings.PATHS.backups_directory_path = str(backups)
        self.Close()

    def __del__( self ):
        pass

class MainWindow(wx.Frame):
    def __init__(self, *args, **kwds):
        self.settings = Settings(str(CONFIG_FILE_PATH))
        # begin wxGlade: MainWindow.__init__
        kwds["style"] = kwds.get("style", 0) | wx.CAPTION | wx.CLIP_CHILDREN | wx.CLOSE_BOX | wx.ICONIZE | wx.MINIMIZE_BOX | wx.SYSTEM_MENU
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((441, 443))
        self.SetTitle("Folder Backup Creator")
        self.SetIcon(wx.Icon(resource_path("icon.ico")))
        # Menu Bar
        self.FolderBackupData_menubar = wx.MenuBar()
        self.open = wx.Menu()
        item = self.open.Append(wx.ID_ANY, "Open Original Folder", "")
        self.Bind(wx.EVT_MENU, self.openSaveFolderMenuButton, item)
        item = self.open.Append(wx.ID_ANY, "Open Backups Folder", "")
        self.Bind(wx.EVT_MENU, self.openBackupsFolderMenuButton, item)
        item = self.open.Append(wx.ID_ANY, "Open Last Backup", "")
        self.Bind(wx.EVT_MENU, self.openLastBackupFolderMenuButton, item)
        item = self.open.Append(wx.ID_ANY, "Open Config File", "")
        self.Bind(wx.EVT_MENU, self.openConfigFileMenuButton, item)
        self.FolderBackupData_menubar.Append(self.open, "Open")
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Edit Settings", "")
        self.Bind(wx.EVT_MENU, self.openSettingsDialogMenuButton, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Create Backup", "")
        self.Bind(wx.EVT_MENU, self.createBackupMenuButton, item)
        self.FolderBackupData_menubar.Append(wxglade_tmp_menu, "Edit")
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Close Window", "")
        self.Bind(wx.EVT_MENU, self.closeMenuButton, item)
        self.FolderBackupData_menubar.Append(wxglade_tmp_menu, "Close")
        self.SetMenuBar(self.FolderBackupData_menubar)
        # Menu Bar end

        self.FolderBackupData_statusbar = self.CreateStatusBar(2)
        self.FolderBackupData_statusbar.SetStatusWidths([-1, 30])
        # statusbar fields
        FolderBackupData_statusbar_fields = [self.settings.save_path, "Loaded"]
        for i in range(len(FolderBackupData_statusbar_fields)):
            self.FolderBackupData_statusbar.SetStatusText(FolderBackupData_statusbar_fields[i], i)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl_1 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "Intializing\n", style=wx.TE_BESTWRAP | wx.TE_MULTILINE | wx.TE_READONLY)
        #self.text_ctrl_1.write("Initiaded\n")
        sizer_1.Add(self.text_ctrl_1, 1, wx.EXPAND, 0)

        grid_sizer_1 = wx.FlexGridSizer(1, 2, 0, 0)
        sizer_1.Add(grid_sizer_1, 0, wx.BOTTOM | wx.EXPAND, 0)

        self.button_1 = wx.Button(self.panel_1, wx.ID_ANY, "Backup")
        grid_sizer_1.Add(self.button_1, 0, wx.EXPAND, 0)

        self.button_2 = wx.Button(self.panel_1, wx.ID_ANY, "Open Folder")
        grid_sizer_1.Add(self.button_2, 0, wx.EXPAND, 0)

        grid_sizer_1.AddGrowableRow(0)
        #grid_sizer_1.AddGrowableRow(1)
        grid_sizer_1.AddGrowableCol(0)
        grid_sizer_1.AddGrowableCol(1)

        self.panel_1.SetSizer(sizer_1)

        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.backup_save_data, self.button_1)
        self.Bind(wx.EVT_BUTTON, self.open_backup_folder, self.button_2)
        path_correct, warn_message = self.settings.init_paths()
        if not path_correct:
            self.error(warn_message)
        #self.settingsDialog = SettingsDialog(self)
        # end wxGlade


    def get_folder_list(self,path):
        filter_method, iterable = getDirs(path)
        return list(map(str,sorted(map(int,filter(filter_method, iterable)), reverse=True)))

    @property
    def save_path(self):
        return self.settings.save_path

    @property
    def backup_path(self):
        return self.settings.backup_path

    @property
    def save_data_folder_name(self):
        return os.path.basename(self.save_path)

    @property
    def backupFolderList(self):
        return self.get_folder_list(self.backup_path)

    @property
    def last_backup_path(self):
        backupFolders = self.backupFolderList
        if len(backupFolders):
            return "%s/%s" % (self.backup_path, backupFolders[0])
        else:
            return False

    def openFolder(self, path):
        os.startfile(path)

    def print(self,val, log_type="INFO"):
        self.text_ctrl_1.write("\n[%s](%s):\n%s\n" % (log_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S") ,val))
        print(val)

    def warn(self, val):
        self.print(val, "WARN")

    def error(self, val):
        self.print(val, "ERROR")

    def createDirGen(self,path):
        def createDir(directory_name):
            total_path = "%s/%s" % (path, directory_name)
            try:
                os.mkdir(total_path)
            except OSError:
                self.error("Creation of the directory %s failed" % total_path)
                return False
            else:
                self.print("Successfully created the directory %s " % total_path)
                return total_path
        return createDir

    def getNewName(self):
        folderList = self.backupFolderList
        name = "0"
        if len(folderList):
            name = str(int(folderList[0])+1)
        return name

    def createBackup(self):
        if self.check_if_config_is_correct():
            self.print("Creating Backup")
            name = self.getNewName()
            createDir = self.createDirGen(self.backup_path)
            self.print("Creating Backup Directory")
            new_dir_path = createDir(name)
            if not new_dir_path:
                self.error("Can't create new backup directory")
                return
            self.print("Coping files from save folder to backup folder")
            newBackupPath = "%s/%s" % (new_dir_path,self.save_data_folder_name)
            shutil.copytree(self.save_path, newBackupPath)
            self.print("Files copied successfully in to %s" % newBackupPath)

    def check_if_config_is_correct(self):
        if not self.settings.paths_configured_correctly:
            self.error("Paths not configured correctly")
            return False
        else:
            return True

    def openConfigFileMenuButton(self, event):
        self.openFolder(CONFIG_FILE_PATH)
        event.Skip()

    def openBackupFolder(self):
        if self.check_if_config_is_correct():
            self.print("Opening Backups folder")
            self.openFolder(self.backup_path)
            self.print("Backups folder opened at %s" % self.backup_path)

    def openSaveFolderMenuButton(self, event):  # wxGlade: MainWindow.<event_handler>
        if self.check_if_config_is_correct():
            self.print("Opening Original folder")
            self.openFolder(self.save_path)
            self.print("Save data opened at %s" % self.save_path)
        event.Skip()

    def openBackupsFolderMenuButton(self, event):  # wxGlade: MainWindow.<event_handler>
        self.openBackupFolder()
        event.Skip()

    def openSettingsDialogMenuButton(self, event):
        with SettingsDialog(self, self.settings.save_path, self.settings.backup_path) as settingsDialog:
            if settingsDialog.ShowModal() == wx.ID_OK:
                # do something here
                print('Hello')
                event.Skip()
            else:
                event.Skip()

    def openLastBackupFolderMenuButton(self, event):  # wxGlade: MainWindow.<event_handler>
        if self.check_if_config_is_correct():
            self.print("Opening last backup folder")
            path = self.last_backup_path
            if not path:
                self.error("There are no backups yet")
            else:
                self.openFolder(path)
                self.print("Last Backup folder opened at %s" % path)
        event.Skip()

    def createBackupMenuButton(self, event):  # wxGlade: MainWindow.<event_handler>
        self.createBackup()
        event.Skip()

    def closeMenuButton(self, event):  # wxGlade: MainWindow.<event_handler>
        self.print("Closing Application")
        time.sleep(1)
        self.Close(force=True)
        event.Skip()

    def backup_save_data(self, event):  # wxGlade: MainWindow.<event_handler>
        self.createBackup()
        event.Skip()

    def open_backup_folder(self, event):  # wxGlade: MainWindow.<event_handler>
        self.openBackupFolder()
        event.Skip()



class MyApp(wx.App):
    def OnInit(self):
        self.FolderBackupData = MainWindow(None, wx.ID_ANY, "")
        self.SetTopWindow(self.FolderBackupData)
        self.FolderBackupData.Show()
        return True



if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
