import paramiko


# Open a transport

host = "10.11.120.81"
port = 22
transport = paramiko.Transport((host, port))

# Auth

password = "varmour"
username = "root"
transport.connect(username = username, password = password)

# Go!

sftp = paramiko.SFTPClient.from_transport(transport)

# Download

filepath = '/etc/passwd'
localpath = '/home/remotepasswd'
sftp.get(filepath, localpath)

# Upload

filepath = '/home/foo.jpg'
localpath = '/home/pony.jpg'
sftp.put(localpath, filepath)

# Close

sftp.close()
transport.close()