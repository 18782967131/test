"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Nfs implements the abstraction needed to simulate or run nfs traffic across a
given client and server.

.. moduleauthor:: xliu@sigma-rt.com
"""
import time,os,re
from vautils.traffic.linux import Traffic

class Nfs(Traffic):
    """
    Nfs implements the nfs traffic class.
    """
    def __init__(self,*args,**kwargs) :
        """
        Initializes the Nfs Traffic object. It calls the initializer of the
        parent first to set the common instance attributes.

        kwargs:
            :client (LinuxVm): linux vm object type, for example pc1
            :server (LinuxVm): linux vm object type, for example pc2
            :dest_intf (str): destination interface name, for example : eth1

        Examples:
                nfs = Nfs( **{'client': pc1,'server':pc2,'dest_intf':'eth1'} )
                nfs.start()
                nfs.check_transfer()
                nfs.stop()
        """

        if 'client' not in kwargs or \
            'server' not in kwargs or \
            'dest_intf' not in kwargs:
            raise ValueError("'client', 'server' and 'dest_intf' are \
                          mandatory parameters!")

        self._client = kwargs.get('client')
        self._server = kwargs.get('server')
        self._dest_intf = kwargs.get('dest_intf')
        super(Nfs, self).__init__(self._client, self._server, self._dest_intf)

    def start(self,**kwargs):
        """
        method used to start the Nfs traffic process in the background on the
        client. It launches the mount client tool in the background, using the
        test interface.
        kwargs:
            :nfs_size (str): size of the file to be put or get in terms of MB
            :nfs_file (str): file name under nfs folder in nfs server for testing
            :nfs_client_path (str): absolute path of nfs client
        Returns: True/False
        Example : nfs.start() or nfs.start(**{'nfs_file'}:'test','file_size':'5})
        """
        self._nfs_path = self._conf_server.exec_command('grep "^/" /etc/exports | awk \'{print $1}\'')
        self._nfs_path=self._nfs_path.strip()
        self._file_size = kwargs.get('file_size',5)
        if 'nfs_file' in kwargs :
            self._nfs_file_name = kwargs.get('nfs_file')
            self._nfs_file = "{}/{}".format(kwargs.get('nfs_file'),self._nfs_path)
        else :
            self._nfs_file = '{}/nfstest'.format(self._nfs_path)
            self._nfs_file_name = 'nfstest'

        self._local_path = kwargs.get('local_path','/tmp/test')
        self._clientpid = None
        self._nfs_client_file = "{}/{}".format(self._local_path,self._nfs_file_name)

        self.setup_server_client_infra()
        self._build_nfs_cmd()

        #start to send nfs traffic
        self._clientpid, outfile = self._conf_client.exec_background(self._cmd, search_expr='mount',redirect=True)
        self._log.info('mount pid: {}'.format(self._clientpid))

        self.started = False
        if self._clientpid:
            mgt_ip = self._conf_client._access._resource.get_mgmt_ip()
            self._log.info("started send nfs traffic on {} pc".format(mgt_ip))
            self._log.info('Send nfs traffic again via creating file on nfs server to make sure nfs server\
             can sync up file from nfs client and the number of packets increasingly')

            pid, self.logfile = self._conf_client.create_file(
                                  path=self._local_path,
                                  name=self._nfs_file_name,
                                  size=self._file_size,
                                  exec_type='async')
            if pid :
                self._log.info('creating file pid: {}'.format(pid))
                self.started = True
            else :
                self._log.error('Failed to create file on client')

        return self.started

    def check_transfer(self):
        '''
        Check the file if it is transfer complete and the file if it is correct. compare the file
        via md5sum tool
        Returns: True/False
        '''
        return_value = False
        check_file_tag = False
        self._log.info("Check transfer if it was completed")

        #just to check the file if is created
        for i in range(1,3) :
            if self._get_status() :
                check_file_tag = True
                break

        if check_file_tag :
            check_file = self._conf_server.exec_command("ls -l {}".format(self._nfs_file))
            md5_server=self._conf_server.get_md5sum(self._nfs_file)
            md5_client = self._conf_client.get_md5sum("{}/{}".format(self._local_path,self._nfs_file_name))
            if re.search(r'No such file or directory',check_file) is None and (md5_server == md5_client) :
                return_value = True
                self._log.info('NFS server have sync up files from client!')
            else :
                self._log.error('nfs server did not sync up from nfs client\
                or md5 of nfs server is not the same as client')
                self._log.error('md5 of nfs client is {}'.format(md5_client ))
                self._log.error('md5 of nfs server is {}'.format(md5_server))

        return return_value

    def _get_status(self):
        '''
        Get the status of creating file

        Returns:True/False
        Examples: get_status()
        '''
        for i in range(1, int(self._file_size)) :
            output = \
                self._conf_client.exec_command('grep "{}.0 MiB) copied" {}'.format(self._file_size, self.logfile))
            if output :
                self._log.info("Completed to create file on nfs client")
                return True
            time.sleep(2)

        self._log.error("Creating file still not finish in {} seconds".format(int(self._file_size)*2))
        return False

    def stop(self):
        """
        method to stop the nfs traffic process spawned by the start method. It
        remove test file of nfs client and umount.It calls the del function to
        de-link references tothe instances created by the traffic object, this
        also forces any open paramiko channels to the remote devices to be closed.
        """
        if not self.started:
            self._log.error("NFS traffic not started - cannot stop!")
        else:
            self._conf_server.remove_file(self._nfs_file)
            output = self._conf_client.exec_command( \
                "df -h |grep %s |awk '{if ($6 == \"%s\") {print $1}}'" % (self._local_path, self._local_path))
            if output != '':
                self._umount_command = "umount -t nfs {}".format(output)
                self._conf_client.exec_command(self._umount_command)

        super(Nfs, self).__del__()

    def setup_server_client_infra(self):
        """
        setup infra on the server for nfs service to enable a file for sync up.
        """
        server = self._conf_server
        nfs_path = '/opt/nfs_folder'
        self._service = 'nfs-kernel-server'

        #umount before if mounted
        output  = self._conf_client.exec_command(\
            "df -h |grep %s |awk '{if ($6 == \"%s\") {print $1}}'" % (self._local_path,self._local_path))
        if output != '':
            self._umount_command = "umount -t nfs {}".format(output)
            self._conf_client.exec_command(self._umount_command)

        # clean file on nfs server before sending traffic.
        self._conf_server.remove_file(self._nfs_file)

        if not server.service_running(self._service):
            server.service_start(self._service)

        #create directory of nfs client if not exists
        output =self._conf_client.exec_command('ls {}'.format(self._local_path))
        if re.search(r'No such file or directory',output) is None :
            self._conf_client.exec_command('mkdir -p {}'.format(self._local_path))

    def _build_nfs_cmd(self):
        """
        helper method to build the nfs command to be run on the client.
        """
        self._cmd = "mount -t nfs {}:{} {}".format(self._dest_ip,self._nfs_path,self._local_path)