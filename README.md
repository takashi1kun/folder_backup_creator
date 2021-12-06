# Folder Backup Creator

This is a very simple application that does a single thing, copy a whole directory with all it's contents included to
another directory under a numbered new directory.

For example given folder "G:/folder1" that you want to backup and you have set "G:/backupsOfFolder1" as the backup
destination this program basically would create a new folder named 0 under "G:/backupsOfFolder1" and then it would copy
"G:/folder1" inside 0, so it would end as "G:/backupsOfFolder1/0/folder1", if you click again the same but with the next
number 1, so you would end with "G:/backupsOfFolder1/1/folder1" after that "G:/backupsOfFolder1/2/folder1", "G:/backupsOfFolder1/3/folder1",
"G:/backupsOfFolder1/4/folder1" and so on, so this creates backups without deleting the previous backup.

These backups are created on demand, you click a button named backup and it does it without prompting anything, it just
does it.

This program needs to be configured, it can either be configured trough the file it would create automatically when you
boot it or trought it's own settings menu that is in edit->Edit Settings. 
There are only 2 settings, the folder you want to create backups of, and the destination where those backups are going
to get stored.

This was originally created to create backups of a certain game save files because of fear of them being deleted for some
error, as this program let's you create backups rather fast, with a single button click, trought a GUI and without doing
anything else or doing things automatically. This program also do not restore backups, you do that manually

## Disclaimer
This program was done to be ran under windows and only windows, it may run on some linux enviorments but i do not assure
it. You can run it trought running python main.py directly or trought the executable i provide.

btw i used wxGlade and wxFormBuilder to generate the boilerplate of the GUI, the GUI is rendered using wxPything library
and settings are handled by a wrapper i wrote myself ripping some code from classyconf, this wrapper is a wrapper for
config_file because i wanted something more like classyconf but that worked like config_file so i wrote the wrapper.

