"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

System abstracts system related features. A superset of features apply
to the product 'dir', while a subset of features apply to other products
- cp, ep, epi. It inherits from Feature - the base class for all features.

.. moduleauthor:: ppenumarthy@varmour.com
"""
import re,os,inspect,copy,time,sys
from feature.common import VaFeature
from vautils.dataparser.string import va_parse_basic
from time import gmtime, strftime
from vautils import logger


class VaSystem(VaFeature):
    """
    System implements methods to configure or view the system related
    features.
    """
    def va_show_system(self):
        """
        method to execute cli command 'show system' and return the parsed info.
        """
        cmd = "show system"
        result = self._access.va_cli(cmd)

        return va_parse_basic(result)

    def va_wait(self, duration=10):
        '''

        :param duration:
        :return:
        '''
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        logger.info('WAITING for {} seconds'.format(duration))
        for i in range(0,int(duration/2)):
            print('*', end='', flush=True)
            # TODO: Need to replace print with logger once logger
            # TODO: supports end and flush option - VATF-450
            time.sleep(2)
        return True

    def va_log_monitor_start(
        self,
        logfile='va_access.log',
        logpath='/usr-varmour/log/varmour_log/current',
        redirect_path='/tmp',
    ):
        """
        method to start the tail -f process on a file in the background

        kwargs:
            :logfile (str): name of the log file to be monitored
            :logpath (str): absolute path of the log file to be monitored
            :redirect_path (str): absolute path for redirected output

        returns:
            tuple of pid (tail -f process), redirected output
        """
        file_id = strftime("%H:%M:%S", gmtime()).replace(':', '')
        filename, extension = os.path.splitext(logfile)

        mon_file = '_'.join((filename, file_id))
        logfile = os.path.join(logpath, '{}'.format(logfile))

        redirect_file = os.path.join(redirect_path, '.'
                                     .join((mon_file, 'txt')))

        ps_cmd = "tail -f {}".format(logfile)
        cmd = "nohup {} > {} 2>&1 &".format(ps_cmd, redirect_file)

        self._access.va_shell(cmd)
        pid = self._get_pid(ps_cmd)

        return pid, redirect_file

    def va_log_monitor_stop(
        self,
        outfile=None,
        pid=None,
        expr=None
    ):
        """
        method to stop the tail -f process running in the background

        kwargs:
            :outfile (str): redirected output file for tail -f
            :pid (str): pid of the tail -f process
            :expr (str): search str to retrieve the process info from
                         ps output
        """
        if pid:
            self._access.va_shell("kill -2 {}".format(pid))

        if outfile and expr:
            cmd = "grep {} {}".format(expr, outfile)
            output = self._access.va_shell(cmd)
            return output

    def va_reboot(self, timeout=60, persistent=True, reconnect_delay=5, type_mode='cli'):
        """
        method performs a reboot on cli or shell mode on the varmour vm. default is cli mode

        kwargs:
            :timeout (int): wait time for device to come back up.
            :persistent (bool): after reboot need access to device
            :reconnect_delay (int): sleep period before trying to reconnect
            :type_mode (str): shell or cli. default is cli.
        """
        if type_mode == 'shell':
            cmd = 'sudo reboot'
        else:
            cmd = 'request system reboot'

        self._access.va_reboot(cmd, timeout, persistent, reconnect_delay,typemode=type_mode)

    def va_connect(self, timeout=60):
        """
        method performs a reboot on the varmour vm.

        kwargs:
            :timeout (int): wait time for device to come back up.
        """
        self._access.va_connect(timeout)

    def va_disconnect(self):
        """
        method performs disconnect varmour vm

        kwargs:
            None
        """
        self._access.va_disconnect()

    def _get_pid(self, search_expr=None):
        """
        method to get the pid of the remote process running in the
        background.

        kwargs:
            :search_expr (str): search criteria for the process
        """
        output = self._access.va_shell("ps ax | grep '{}'"
                                       .format(search_expr))

        ps_output = [tuple(line.split()) for line in output.splitlines()]
        running = [line for line in ps_output if 'grep' not in line]

        if running:
            pid = ps_output[0][0]
            return pid

        return False


    def va_check_core_file(self):
        """
        check core file

        kwargs:
            None

        Return:
            False : not found any core file
            core files (list) : all core files
        """
        dev_type = self._access._resource.get_nodetype()
        core_files = []

        if dev_type == "dir" :
            set_cmds = "ls -l /usr-varmour/core | awk '{print $9}'"
        else :
            set_cmds = "ls -l /usr-varmour/core | awk '{print $8}'"

        try :
            corefile = self._access.va_shell(set_cmds)
        except Exception as err:
            logger.error(err)

        build_version = self._va_get_version()
        if (len(corefile.split("\n")) == 3) :
            return False
        else :

            for core in corefile.split("\n") :
                core = core.strip()
                if re.search(r'\.core',core, re.I) is not None and \
                        re.search(r'%s' % build_version, core, re.I|re.M):
                   core_files.append(core)

            return(self._va_get_first3_core_file(core_files))

    def _va_get_first3_core_file(self,core_files):
        sort_cores = sorted(core_files)
        return_cores = []
        tmp_cores = copy.deepcopy(sort_cores)
        if (len(core_files) ==1) :
            return (core_files)

        # If multiple same core on same build, \
        # moving the first 3 should be good enough
        for corename in sort_cores:
            index = 1
            dupc_tag = 0
            get_lcn_in = re.search(r'(.*)-\d+\.core', corename, re.I | re.M)
            get_lcn = get_lcn_in.group(1)
            new_cores = tmp_cores.remove(corename)
            check_done = 0
            for tc in return_cores:
                if re.search(r'%s' % get_lcn, tc) is not None:
                    check_done = 1
                    break

            if check_done:
                continue

            for core in tmp_cores:
                get_cn_in = re.search(r'(.*)-\d+\.core', core, re.I | re.M)
                get_cn = get_cn_in.group(1)
                if get_cn == get_lcn:
                    if (dupc_tag < 3):
                        return_cores.append(core)

                    dupc_tag += 1
                index += 1
        return (return_cores)

    def va_get_mode (self,*args,**kwargs) :
        """
        get mode

        kwargs: None

        returns: str: PB/M/B/root

        Examples:
            va_get_mode()
        """
        rt = self._access.va_cli('show system')
        if re.search(\
                r'@[\d\w\-\_]+((#vsys#ROOT)|(#ROOT)|)\(config.*\)\(M\)?>[ \t]*$',\
                     rt,re.I|re.M) is not None :
            logger.info("Master")
            return 'M'
        elif re.search(\
                r'@[\d\w\-\_]+((#vsys#ROOT)|(#ROOT)|)\(config.*\)\(PB\)?>[ \t]*$',\
                rt,re.I|re.M) is not None :
            logger.info("PB")
            return "PB"
        elif re.search(\
                r'@[\d\w\-\_]+((#vsys#ROOT)|(#ROOT)|)\(config.*\)\(B\)?>[ \t]*$', \
                rt,re.I|re.M) is not None :
            logger.info("B")
            return "B"
        elif re.search(\
                r'@[\d\w\-\_]+((#ROOT)|(#))\(PB\)?>[ \t]*$', \
                rt,re.I|re.M) is not None :
            logger.info("PB")
            return "PB"
        elif re.search(\
                r'@[\d\w\-\_]+((#ROOT)|(#))\(M\)?>[ \t]*$', \
                rt,re.I|re.M) is not None :
            logger.info("Master")
            return "M"
        elif re.search(\
                r'@[\d\w\-\_]+((#ROOT)|(#))\(B\)?>[ \t]*$', \
                rt,re.I|re.M) is not None :
            logger.info("B")
            return "B"
        else :
            logger.info("root")
            return "root"

    def va_move_log_file(self):
        """
        Move log file to external log server.

        kwargs:
            None
        """
        log_server2_tag = False
        if testdata.va_get_control().get('move_log').upper() == 'N' :
            logger.debug('Noe need to move log file to external log server')
            return True

        ip = log_server1._access._resource.get_mgmt_ip()
        user = log_server1._access._resource.get_user()
        user_name = user.get('name')
        user_pwd = user.get('password')
        #check log_server2 if it is in topo file.
        if 'log_server2' in testdata.va_get_test_vms() :
            log_server2_tag = True
            ip2 = log_server2._access._resource.get_mgmt_ip()
            user2 = log_server2._access._resource.get_user()
            user_name2 = user2.get('name')
            user_pwd2 = user2.get('password')
        jobid = os.getpid()
        try :
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            caller_name = calframe[4][3]
            casename = caller_name
        except Exception as error:
            casename = 'test'

        destdir = "/var/log/varmour_log/%s/%s" % (jobid, casename)
        log_server1.exec_command("mkdir -p %s " % destdir)
        node_type = self._access._resource.get_nodetype()
        name =self._resource.get_uniq_id()
        curr_mode = self.va_get_mode()

        # download debug log file from all EPs.
        if (node_type == "dir"):
            if name == "dir_1" and curr_mode != "PB" or curr_mode== "M":
                self._access.va_cli("request download debug-log device all all",600)

            if (curr_mode == "PB"):
                dev_num = 1
            else:
                output = self._access.va_cli('show chassis')
                match1 = re.search(r'total devices connected:\s+(\d+)\s+',output,re.I|re.M)
                match2 = re.search(r'inactive devices:\s+(\d+)\s+', output, re.I | re.M)
                if match1 is None or match2 is None:
                    dev_num = 1
                else :
                    dev_num = int(match1.group(1)) - int(match2.group(1))
        else:
            dev_num = 1

        logdir = "/var/log/varmour_log"
        apachedir = "/var/log/apache2"
        destdir = "/var/log/varmour_log/%s/%s" % (jobid,casename)
        log_server1.exec_command("mkdir -p %s " % destdir)
        self._access.va_shell("sudo ls -l %s/*" % logdir)
        self._access.va_shell("sudo grep \"Exception\" %s/current/*.log" % logdir)
        cmd_tar = "sudo tar -zcvf %s/log_%s.tar %s/current/* %s/*" % \
                  (logdir, name, logdir, apachedir)
        if (int(dev_num) >= 2):
            dev_num = int(dev_num) + 1
            for i in range(2, int(dev_num)):
                cmd_tar = cmd_tar + " %s/dev_%d/*" % (logdir, i)

        set_cmds = []
        set_cmds.append(cmd_tar)
        self._access.va_shell(set_cmds,200)

        set_cmd2 ="sudo scp -o 'StrictHostKeyChecking no'"
        set_cmd2 += " %s/log_%s.tar* %s@%s:%s" % (logdir, name, user_name, ip, destdir)
        self._access.va_shell(set_cmd2,200,**{'handle_password':user_pwd})

        #check the file if it exist on log server.
        #it will move to backup logserver if failure.
        output = log_server1.exec_command('ls {}'.format(destdir))
        if re.search(r'No such file or directory',output,re.I|re.M) is not None:
            logger.error('Failed to copy log file to logserver {}'.format(ip))
            if log_server2_tag :
                log_server2.exec_command("mkdir -p %s " % destdir)
                set_cmd2 = "sudo scp -o 'StrictHostKeyChecking no'"
                set_cmd2 += " %s/log_%s.tar* %s@%s:%s" % \
                            (logdir, name, user_name2, ip2, destdir)
                self._access.va_shell(set_cmd2, 200, **{'handle_password': user_pwd2})
                output = log_server2.exec_command('ls {}'.format(destdir))
                if re.search(r'No such file or directory', output, re.I | re.M) is not None:
                    logger.error('Failed to copy log file to logserver {}'.format(ip2))
                    return False
            else :
                return False
        set_cmds = []
        set_cmds.append("sudo rm -f %s/current/*" % logdir)

        if (int(dev_num) >= 2):
            for i in range(2, int(dev_num)):
                set_cmds.append("sudo rm -rf %s/dev_%d" % (logdir, i))

        set_cmds.append("sudo rm -f %s/log_%s.tar*" % (logdir, name))
        self._access.va_shell(set_cmds)

        logger.error("The log files have been moved to %s@%s:%s/" % \
                     (user_name, ip, destdir))
        return True

    def _va_get_version(self):
        try:
            version_info = self._access.va_shell("cat /version")
        except Exception as err:
            logger.error(err)

        build_version = re.search(r'cat /version\s+(.*)', \
                                  version_info, re.I | re.M).group(1).strip()
        return(build_version)

    def va_check_move_core_file(self):
        """
        check core file. It will move all log and core files to external server.
        default directory is /var/log/varmour_log/pid/testcase_name

        kwargs:
            log_server: object of log server. default is pc5.

        Return:
            False: if found any core file and remove it.
            True: Not found any core file
        """
        curr_core_tag = 0
        try :
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            caller_name = calframe[4][3]
            casename = caller_name
        except Exception as error:
            casename = 'test'

        logger.info('Case name is %s' % casename)
        try:
            version_info = self._access.va_shell("cat /version")
        except Exception as err:
            logger.error(err)

        build_version = re.search(r'cat /version\s+(.*)', \
                                  version_info, re.I | re.M).group(1).strip()
        core_file = self.va_check_core_file()

        if isinstance(core_file, list) and (len(core_file) != 0) :
            logger.warn("Found core file!\n")
            self.va_move_core_file(core_file, casename)
            return False
        else:
            logger.info("Not found any core file")
            return True

    def va_move_core_file(self,core_file, casename='test') :
        """
        move core file to external log server

        kwargs:
            log_server: object of log server
        Return :
           True
        """
        log_server2_tag = False
        if testdata.va_get_control().get('move_core').upper() == 'N' :
            logger.debug('Not need to move core file to external log server')
            return True

        ip = log_server1._access._resource.get_mgmt_ip()
        user = log_server1._access._resource.get_user()
        user_name = user.get('name')
        user_pwd = user.get('password')
        #check log_server2 if it is in topo file.
        if 'log_server2' in testdata.va_get_test_vms() :
            ip2 = log_server2._access._resource.get_mgmt_ip()
            user2 = log_server2._access._resource.get_user()
            user_name2 = user2.get('name')
            user_pwd2 = user2.get('password')
            log_server2_tag = True
        jobid = os.getpid()
        destdir = "/var/log/varmour_log/%s/%s" % (jobid, casename)
        log_server1.exec_command("mkdir -p %s " % destdir)
        coredir = "/usr-varmour/core"

        set_cmds = []
        index = 1
        exec_files = ""
        for core in core_file:
            core = core.strip()
            core = '/usr-varmour/core/{}'.format(core)
            match_core = re.search(r'(.*).gz|.tar', core, re.I)
            if match_core is not None:
                # uncompress core file
                self._access.va_shell("sudo gunzip -d %s" % core)
                un_compress_core_file = match_core.group(1)
                self.print_coredump_to_debug(un_compress_core_file)
                # compress core file
                self._access.va_shell("sudo gzip %s" % un_compress_core_file,200)
            else:
                self.print_coredump_to_debug(core)

            if (index == 1):
                tar_file_name = "%s.tar" % core

            exefile = self._va_get_full_exe_name_from_core(core)
            exec_files += " " + exefile
            index += 1

        logger.info("compress core file")
        cmd = "sudo tar -zcvf {} ".format(tar_file_name)
        for corename in core_file:
            cmd += "/usr-varmour/core/{} ".format(corename)
        cmd +="{} /etc/syslog-ng/*".format(exec_files)
        cmd += " /etc/pam.d/* /opt/varmour/conf/* /var/log/varmour_log/current/*"
        cmd += " /etc/nsswitch.conf "
        set_cmds.append(cmd)
        self._access.va_shell(set_cmds, 200)
        set_cmd = "sudo scp -o 'StrictHostKeyChecking no' "
        set_cmd += "{} {}@{}:{}".format(tar_file_name, user_name, ip, destdir)
        self._access.va_shell(set_cmd,200,**{'handle_password':user_pwd})

        #check the file if it exist on log server.
        #it will move to backup logserver if failure.
        output = log_server1.exec_command('ls {}'.format(destdir))

        #check log_server2 if it is in topo file.
        if re.search(r'No such file or directory',output,re.I|re.M) is not None:
            logger.error('Failed to copy core file to logserver {}'.format(ip))
            if log_server2_tag :
                log_server2.exec_command("mkdir -p %s " % destdir)
                set_cmd = "sudo scp -o 'StrictHostKeyChecking no' "
                set_cmd += "{} {}@{}:{}".format(tar_file_name, user_name2, ip2, destdir)
                self._access.va_shell(set_cmd, 200, **{'handle_password': user_pwd2})
                output = log_server2.exec_command('ls {}'.format(destdir))
                if re.search(r'No such file or directory', output, re.I | re.M) is not None:
                    logger.error('Failed to copy core file to logserver {}'.format(ip2))
                    return False
            else :
                return False

        # delete all core files.
        cmd = "sudo rm -f "
        for corename in core_file:
            cmd += "/usr-varmour/core/{} ".format(corename)
        cmd += "{} ".format(tar_file_name)
        self._access.va_shell(cmd)
        logger.error("The device have core file!\n")
        log_msg = "The core, log, and cfg file have been moved to"
        logger.error(log_msg+" %s@%s:%s/\n" % (user_name, ip, destdir))
        return True

    def va_dump_coredump_backtrace(self, corefile, *args, **kwargs):
        """
        Print core file information via gdb

        kwargs:
            corefile: core file name
        Return :
           None
        """
        exefile = self._va_get_full_exe_name_from_core(corefile)
        cmd = "sudo gdb {} --batch --core {} --quiet".format(exefile,corefile)
        cmd += " --ex 'set pagination off' -ex 'bt full' -ex 'quit'"
        cmd1 = "sudo gdb {} --batch --core {} --quiet".format(exefile,corefile)
        cmd1 += " --ex 'set pagination off' -ex 'thread apply all bt full' -ex 'quit'"

        logger.debug("+++++++++++++++++++++++++++++++++++++++++++++++")
        logger.debug("+          gdb with bt full                   +")
        logger.debug("+++++++++++++++++++++++++++++++++++++++++++++++")
        self._access.va_shell(cmd,200)

        logger.debug("+++++++++++++++++++++++++++++++++++++++++++++++")
        logger.debug("+      gdb with thread apply all bt full      +")
        logger.debug("+++++++++++++++++++++++++++++++++++++++++++++++")
        self._access.va_shell(cmd1,240)
        return True

    def print_coredump_to_debug(self, corefile, *args, **kwargs):
        """
        Print core dump information for debug.

        kwargs:
            corefile: core file name
        Return :
           None
        """
        logger.debug("+------------------- Coredump ------------------------+")
        logger.debug("!")
        logger.debug("Corefilename: %s" % corefile)
        logger.debug("stack trace:")
        logger.debug(self.va_dump_coredump_backtrace(corefile))
        logger.debug("end of stack trace")
        logger.debug("!")
        logger.debug("+------------------- End of Coredump -----------------+")
        return True

    def _va_get_full_exe_name_from_core(self, corefile, *args, **kwargs):
        """
        get bin file according to core file

        kwargs:
            corefile: core file name
        Return :
            bin file. for example /opt/varmour/bin/sw_node
            False : Not found bin file according to corefile
        """
        info = re.search(r'/usr-varmour/core/([a-zA-Z0-9_]+)', corefile, re.M|re.I)

        try:
            exefile = info.group(1)

        except Exception as err:
            logger.error(err)
            return False

        if (exefile == "sshd"):
            exefile = "/usr/sbin/sshd"
        else:
            exefile = "/opt/varmour/bin/%s" % exefile

        #check exefile if it exist.
        rt_val = self._access.va_shell('ls {}'.format(exefile))
        if re.search(r'No such file or directory',rt_val,re.M|re.I) is not None :
            logger.error('Not found the bin file {}'. format(exefile))
            return False
        else :
            logger.info("exec file is {}".format(exefile))

        return(exefile)

    def va_check_process(self, name, *args) :
        """
        Check process if it exists. it will return 0 if not exists.
        return pid of the process. the type of return value is dict.

        kwargs:
            name: process name, sw, agent, fw, cn,
                                re, konfd,turbo,monitor
        Return :
            dict: {'process name' : 'pid'},  process id if up running.
            for example:
            {'konfd': 2048} or
            {'orchestration':
                {'varmour_main': 31807,
                 'deploymanager': 1887,
                 'vcenter': [2454, 2455, 2456, 2457, 2458, 2462, 2463, 2466, 2467, 2469],
                 'aci_plugin': 2468}
            }

            False : Not found the process
        Examples :
            va_check_process('konfd')
        """
        pids = {}
        pid = 0
        if name != 'orchestration' :
            cmd = 'sudo ps -ewf | grep %s | awk \'{if(NR==1){print $2}}\'' % name
            return_vlan = self._access.va_shell(cmd,exit=False)

        try :
            if name != 'orchestration' :
                pid = re.split(r'\n',return_vlan)[1]
                logger.info("The process of {} is {}".format(name, pid))
                pids[name] = int(pid)
            else :
                # many process of vcenter, varmour_main, aci_plugin, deploymanager
                sub_names = ['vcenter','varmour_main','aci_plugin','deploymanager']
                pids[name] = {}
                for s_name in sub_names :
                    cmd = 'sudo ps -ewf | grep %s|grep %s| awk \'{if(NR==1){print $2}}\''\
                          % (name,s_name)
                    if s_name == 'vcenter' :
                        cmd = 'sudo ps -ewf | grep %s|grep %s| awk \'{print $2}\''\
                          % (name,s_name)

                    return_vlan = self._access.va_shell(cmd)
                    if s_name != 'vcenter' :
                        pid = re.split(r'\n', return_vlan)[1]
                        pids[name][s_name] = int(pid)
                    else :

                        pid_v = []
                        pid = re.split(r'\n', return_vlan)
                        pid.remove(pid[0])
                        pid.remove(pid[-1])
                        for p_n in pid :
                            pid_v.append(int(p_n))

                        pids[name][s_name] = pid_v
                logger.info("The process of {} is {}".format(name, pids))

            return pids
        except Exception as err:
            logger.error(err)
            logger.error("Failed to get {} process".format(name))
            return False

    def va_kill_process(self, name, *args):
        """
        it should start automatically after kill the process.

        kwargs:
            name: process name, sw, agent, fw, cn,orchestration
            re, konfd,turbo,monitor
        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples : va_kill_process('sw_node')
        """
        #get pid of the process.
        logger.info('Restart {} process'.format(name))
        pids = self.va_check_process(name)
        sub_names = ['vcenter', 'varmour_main', 'aci_plugin', 'deploymanager']

        #kill the process
        if name != 'orchestration':
            self._access.va_shell('sudo kill -9 %s' % pids[name], exit=False)
            stime = 2
        else :
            cmds = []
            stime = 30
            for s_name in sub_names :
                pid = pids['orchestration'][s_name]
                if isinstance(pid, list) :
                    pid = ' '.join(map(str, pid))

                cmds.append('sudo kill -9 %s' % pid,exit=False)
            self._access.va_shell(cmds)

        #sleep 2 seconds. the service will start automatically.
        time.sleep(stime)

        #new pid should not the same as before.
        pids1 = self.va_check_process(name)

        logger.info('Expect: New pid should not the same as before')
        if name == 'orchestration':
            pids_vcenter = pids['orchestration']['vcenter']
            pids1_vcenter = pids1['orchestration']['vcenter']
            pids['orchestration'].pop('vcenter')
            pids1['orchestration'].pop('vcenter')
            pids = pids['orchestration']
            pids1 = pids1['orchestration']

            if len(set(pids_vcenter) & set(pids1_vcenter)) != 0 :
                logger.error('Failed to kill vcenter of orchestration process')
                logger.error('The pids is {} before kill vcenter of {}'.format(pids_vcenter,name))
                logger.error('The pids is {} after kill vcenter of {}'.format(pids_vcenter, name))
                return False

        if len(set(pids1.items()) & set(pids.items())) == 0 :
            logger.info('Succeed to kill {} process, new pid is {}'.format(name, pids1))
            return True
        else :
            logger.error('Failed to kill {} process'.format(name))
            logger.error('The pids is {} before kill {}'.format(pids, name))
            logger.error('The pids is {} after kill {}'.format(pids1, name))
            return False


    def va_kill_sw_process(self, *args):
        """
        kill sw process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_sw_process()
        """

        return self.va_kill_process('sw_node')

    def va_kill_turbo_process(self, *args):
        """
        kill turbo process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_turbo_process()
        """

        return self.va_kill_process('turbo_node')

    def va_kill_agent_process(self, *args):
        """
        kill agent process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_agent_process()
        """

        return self.va_kill_process('agent')

    def va_kill_fw_process(self, *args):
        """
        kill fw process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_fw_process()
        """

        return self.va_kill_process('fw')

    def va_kill_cn_process(self, *args):
        """
        kill cn process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_cn_process()
        """

        return self.va_kill_process('control_node')

    def va_kill_re_process(self, *args):
        """
        kill re process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_re_process()
        """

        return self.va_kill_process('re_node')

    def va_kill_konfd_process(self, *args):
        """
        kill konfd process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_konfd_process()
        """

        return self.va_kill_process('konfd')

    def va_kill_monitor_process(self, *args):
        """
        kill monitor process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_monitor_process()
        """

        return self.va_kill_process('monitor')

    def va_kill_orchestration_process(self, *args):
        """
        kill orchestration process.

        kwargs:
            None

        Return :
             True: Succeed to restart the process.
             False : Failed to restart the process

        Examples :
            va_kill_orchestration_process()
        """

        return self.va_kill_process('orchestration')

    def va_bring_interface(self, intf='eth0', action='up', *args, **kwargs):
        """
        API to bring up or down interface.
        param   : intf : interface name
                  action : up | down
        return: 
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if intf == 'fabric':
            setup_ini_file = '/config-varmour/configuration/varmour_conf/setup.ini'
            intf_info = self._access.va_shell('grep "fabric_interface=" {}'.format(
                setup_ini_file), exit=False)
            if 'intf_info' not in dir():
                logger.error('Failed to get fabric interface from file {}'.format(
                setup_ini_file))
                return False

            match_result = re.search(r'(eth\d+)',intf_info)
            if match_result is None:
                logger.error('Not matched "eth", Info: {}'.format(intf_info))
                return False

            intf = match_result.group(1)
        
        self._access.va_shell('ifconfig {} {}'.format(intf, action), exit=False)
        time.sleep(0.1)
        inf_info = self._access.va_shell('ifconfig {}'.format(intf), exit=False)
        pat = re.compile(r'UP BROADCAST')
        match_result = pat.search(inf_info, re.I)
        if action.upper() == 'UP' and match_result is not None:
            logger.info('Succeed to bring up interface')
            return True
        elif action.upper() == 'DOWN' and match_result is None:
            logger.info('Succeed to bring down interface')
            return True
        else:
            logger.error('Failed to bring {} interface'.format(action))
            return False

    def va_get_version(self, *args, **kwargs):
        """
        API to get version of system.
        param   : kwargs : dict
        example : va_get_version(**kwargs)
            kwargs = {
                    'mode' : 'cli' | 'shell',
                    'partition' : 'primary' | 'secondary'
            }
        return:
            :string - None or version
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        version = None

        if 'mode' in kwargs:
            mode = kwargs.get('mode')
        else :
            mode = "cli"

        if (mode == "cli" ) :
            system_info = self.va_show_system()
            version = system_info.get('software version')
        elif (mode == "shell" ) :
            if 'partition' in kwargs:
                partition = kwargs.get('partition')
            else :
                partition = 'primary'

            version_info = self._access.va_shell("cat /boot/{}/version".format(
                partition))
            version_info = version_info.split('\n')
            version = version_info[1].strip()
            version = re.sub(r'-epi|-ep','',version)

        logger.info("Current version: {}".format(version))
        return version

    def va_debug_toggle(self, *args, **kwargs):
        dev_type = ''
        user = ''
        debug_on = ''
        if ((dev_type == 'cp' or dev_type == 'ep') and user  == 'varmour') :
            cmdslist = ["enable_re_debug", "enable_agent_debug", "enable_io_debug", \
                        "enable_sn_debug", "enable_konfd_debug", "enable_vadb_debug"]
        elif(dev_type == 'epi' and user  == 'varmour'):
            cmdslist = ["enable_agent_debug", "enable_turbo_debug", "enable_konfd_debug", \
                        "enable_vadb_debug"]
        elif (user == 'varmour'):
            cmdslist = ["enable_konfd_debug", "enable_cn_debug", "enable_re_debug", \
                        "enable_agent_debug", "enable_io_debug", "enable_sn_debug", \
                        "enable_vadb_debug"]
        else :
            pass

        inifile = "/opt/varmour/conf/setup.ini"
        origfile = "/opt/varmour/conf/setup.ini.orig"
        newfile = "/opt/varmour/conf/setup.ini.new"

        if (debug_on  is not None):
            self.shell("sudo cp %s %s " % (inifile, origfile))
            found_debug = 0

            if debug_on == 'Y' :
                expect_val = 1
                actual_val = 0
            else :
                expect_val = 0
                actual_val = 1

            for cmd in cmdslist:
                if (self.grepfound(cmd, inifile) == -1):
                    self.va_shell('sed -i \'$a{}={}\' {}'.format (cmd,expect_val,inifile))
                    found_debug = 1
                elif:
                    self.shell("sed -i 's/%s={}/%s={}/g' {}" % (cmd,actual_val,cmd,expect_val,inifile))
                    found_debug = 1

            if (found_debug == 1):
                self.reboot()

    def grepfound (self, cmd, file, *args, **kwargs) :
        cmdsend =  "grep -c %s %s" % (cmd, file)
        output = self.va_shell(cmdsend)
        ret = re.sub(r'grep -c %s' % cmd , "" , ret)
        match_ret = re.search(r'\d+',ret, re.I|re.M|re.S)
        if (match_ret is not None ):
            return(int(match_ret.group(0)))
        else :
            return(-1)
