"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Http implements the abstraction needed to simulate or run http traffic across a
given client and server.

.. moduleauthor:: xliu@sigma-rt.com
"""
import time
from vautils.traffic.linux import Traffic

LFTP_TIMEOUT = 10


class Http(Traffic):
    """
    HTTP implements the Http traffic class.
    """
    def __init__(self,*args,**kwargs) :
        """
        Initializes the Http Traffic object. It calls the initializer of the
        parent first to set the common instance attributes.

        kwargs:
            :client (LinuxVm): linux vm object type
            :server (LinuxVm): linux vm object type
            :dest_intf (str): destination interface that receives the request
            :debug (bool): enable debug logging, True/False
        """

        if 'client' not in kwargs or \
                        'server' not in kwargs or \
                        'dest_intf' not in kwargs:
            raise ValueError("'client', 'server' and 'dest_intf' are \
                          mandatory parameters!")

        self._client = kwargs.get('client')
        self._server = kwargs.get('server')
        self._dest_intf = kwargs.get('dest_intf')
        super(Http, self).__init__(self._client, self._server, self._dest_intf)

    def start(self,**kwargs):
        """
        method used to start the Http traffic process in the background on the
        client. It launches the wget client tool in the background, using the
        test interface.
        kwargs:
            :http_size (str): size of the file to be put or get in terms of MB
            :http_file (str): file name with absolute path specified that is downloaded
            :port (int) : port of http server, default is 80
        Example : http.start(**{'port':5080})
        """
        self._file_size = kwargs.get('file_size',5)
        self._debug = kwargs.get('debug',False)
        self._ctrl_port = kwargs.get('port',80)
        self._timeout = 4 * int(self._file_size) + 20
        self._clientpid = None


        self.setup_server_infra()
        self._build_http_cmd()
        self._transfer_file = self._local_file()
        home =self._conf_client.get_home_dir()
        self._local_file = '{}/{}'.format(home,self._local_file())
        self._cmd += "{} {}".format(self._transfer_file,self._local_file)

        #clean local file before sending traffic.
        self._transfer_cleanup_util(local=True)

        pid, outfile = self._conf_client.exec_background(self._cmd, search_expr='wget',redirect=True)
        self._log.info('Ftp pid: {}'.format(pid))
        self._log.info('Outfile: {}'.format(outfile))
        self._clientpid = pid
        mgt_ip = self._conf_client._access._resource.get_mgmt_ip()

        self.started = False
        if self._clientpid:
            self.started = True
            self._log.info("started http traffic on {} pc".format(mgt_ip))

        return self.started

    def check_transfer(self):
        '''
        Check the file if it is transfer complete and the file if it is correct. compare the file
        via md5sum tool
        Returns: True/False
        '''
        self._log.info("Check transfer if it was completed")
        return self._check_transfer('start', 'http')

    def stop(self):
        """
        method to stop the Http traffic process spawned by the start method. It
        checks if the file transfer is complete. It then stops the vsftpd
        daemon, does a post transfer cleanup, and sets the traffic started
        boolean to false. It calls the del function to de-link references to
        the instances created by the traffic object, this also forces any
        open paramiko channels to the remote devices to be closed.
        """
        server = self._conf_server
        if not self.started:
            self._log.error("Http traffic not started - cannot stop!")
        else:
            server.service_stop(self._service)
            self.started = False

        self._transfer_cleanup_util(True, True)
        if int(self._ctrl_port) != 80 :
            self._log.info("reset port of http service on http server")
            server.exec_command("sed -i '/^Listen /d' /etc/apache2/ports.conf")
            server.exec_command("sed -i '$a\Listen 80' /etc/apache2/ports.conf")

        self._conf_server.exec_command('rm -f {}/temp_*.txt'.format(self._conf_client.get_home_dir()))
        super(Http, self).__del__()

    def setup_server_infra(self):
        """
        setup infra on the server for http service to enable a file download.
        """
        server = self._conf_server
        service = 'httpd'
        service_doc_root = '/var/www/html'

        if self._server.get_version() == 'Ubuntu':
            service = 'apache2'

        if int(self._ctrl_port) != 80 :
            self._log.info("config port of http service to {} on http server".format(self._ctrl_port))
            server.exec_command("sed -i '/^Listen /d' /etc/apache2/ports.conf")
            server.exec_command("sed -i '$a\Listen {}' /etc/apache2/ports.conf".format(self._ctrl_port))
            server.service_stop(service)
            server.service_start(service)

        self._service = service

        if not server.service_running(service):
            server.service_start(service)

        self._file_info = server.create_file(
                              path=service_doc_root,
                              size=self._file_size
                          )

    def _build_http_cmd(self):
        """
        helper method to build the http command to be run on the client.
        """
        self._cmd = "wget --limit-rate=256K http://{}:{}/".format(self._dest_ip,self._ctrl_port)