import os
import tarfile
import time
import shutil

BACKUP_DIR = '/app/restore/backups'
RESTORE_DIR = '/app/restore'
TMP_DIR = '/app/tmp'

def recreate_temp_folder(temp_folder):
    if os.path.exists(temp_folder):
        for root, dirs, files in os.walk(temp_folder, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    else:
        os.makedirs(temp_folder)
    
recreate_temp_folder(TMP_DIR)

def list_backups():
    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.tar')]
    backups.sort(key=lambda f: os.path.getmtime(os.path.join(BACKUP_DIR, f)))
    backups_with_dates = [(f, os.path.getmtime(os.path.join(BACKUP_DIR, f))) for f in backups]
    backups_with_dates = [{'name':f, 'date':time.strftime('%d/%m/%y', time.localtime(mtime))} for f, mtime in backups_with_dates]
    return backups_with_dates

def restore_backup(backup_name):
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    if not os.path.exists(backup_path):
        print(f'Backup not found: {backup_path}')
        return 'not-found'
    
    with tarfile.open(backup_path, 'r') as outer_tar:
        outer_tar.extractall(path=TMP_DIR)
    
    inner_tar_path = os.path.join(TMP_DIR, 'homeassistant.tar.gz')
    if not os.path.exists(inner_tar_path):
        print(f'Inner tar.gz not found in: {TMP_DIR}')
        return 'inner-gz-not-found'
    
    with tarfile.open(inner_tar_path, 'r:gz') as inner_tar:
        data_folder = os.path.join(TMP_DIR, 'data')
        inner_tar.extractall(path=TMP_DIR)
    
    if not os.path.exists(data_folder):
        print(f'Data folder not found in: {TMP_DIR}')
        return 'data-folder-not-found'
    for root, dirs, files in os.walk(RESTORE_DIR, topdown=False):
        for name in files:
            if os.path.dirname(os.path.join(root, name)) == os.path.join(RESTORE_DIR, 'backups'):
                continue
            os.remove(os.path.join(root, name))
        for name in dirs:
            if name != 'backups':
                os.rmdir(os.path.join(root, name))
    for item in os.listdir(data_folder):
        if item == 'backups':
            continue
        s = os.path.join(data_folder, item)
        d = os.path.join(RESTORE_DIR, item)
        if os.path.isdir(s):
            os.makedirs(d, exist_ok=True)
            for root, dirs, files in os.walk(s):
                for dir_ in dirs:
                    os.makedirs(os.path.join(d, os.path.relpath(os.path.join(root, dir_), s)), exist_ok=True)
                for file_ in files:
                    shutil.move(os.path.join(root, file_), os.path.join(d, os.path.relpath(os.path.join(root, file_), s)))
        else:
            shutil.move(s, d)
    recreate_temp_folder(TMP_DIR)
    print(f'Backup restored to: {RESTORE_DIR}')
    
def rename_backup(old_name, new_name):
    old_path = os.path.join(BACKUP_DIR, old_name)
    new_path = os.path.join(BACKUP_DIR, new_name)
        
    if not os.path.exists(old_path):
        return 'not-found'
        
    if os.path.exists(new_path):
        return 'already-exists'
        
    os.rename(old_path, new_path)
    
def delete_backup(backup_name):
    backup_path = os.path.join(BACKUP_DIR, backup_name)
        
    if not os.path.exists(backup_path):
        return 'not-found'
        
    os.remove(backup_path)