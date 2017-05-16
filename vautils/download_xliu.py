# !/usr/bin/env python
import paramiko, datetime, os

# hostname = '10.11.120.86'
# username = 'varmour_no_cli'
# password = 'vArmour123'
hostname = '10.11.120.86'
username = 'varmour_no_cli'
password = 'vArmour123'
port = 22
local_dir = 'e:\\test\\'
remote_dir = '/tmp/'

t = paramiko.Transport(hostname, port)
a = t.connect(username=username, password=password)
sftp = paramiko.SFTPClient.from_transport(t)

# files=sftp.listdir(dir_path)
files = sftp.listdir(remote_dir)
print(files)
# files = ['interfaces']
# for f in files:
#     print ('#########################################')
#     print('Beginning to download file from %s %s ' % (hostname, datetime.datetime.now()))
#     print('Downloading file:', os.path.join(remote_dir, f))
#     sftp.get(os.path.join(remote_dir, f), os.path.join(local_dir, f))  # 下载
#     # sftp.put(os.path.join(local_dir,f),os.path.join(remote_dir,f))#上传
#     print('Download file success %s ' % datetime.datetime.now())
#     print('')
#     print('##########################################')
#
# t.close()

