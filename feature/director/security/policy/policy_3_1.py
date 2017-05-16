
import sys
import copy
import re

from feature.common import VaFeature
from feature import logger


class VaPolicy(VaFeature):
    """
    Policy  implements methods that configure policy of the
    varmour director product.
    """
    def va_unset_policy(self, pname=None,pcommit=None):
        """

        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not pname:
            raise ValueError(" Policy name is mandatory for setting policy")
        cmd = "unset policy name {}".format(pname)
        # TODO : Need to implement remaining option for unset
        if pcommit:
            logger.info("Now commiting the configs")
            #cstatus = self._access.va_config(cmd, True)
            cstatus = self._access.va_config(cmd)
            cstatus = self._access.va_commit()
            logger.info("the commit status :" + str(cstatus))
            return cstatus
        else:
            cstatus = self._access.va_config(cmd)
            return cstatus

    def va_config_policy (self, data, *args, **kwargs):
        """
            API to config policy
            param    :
                data1 = {
                     'type'        : 'id' or 'name' or 'new'
                     'name'       : 'policy name'
                     'szone'      : 'From zone'
                     'dzone'      : 'To zone'
                     'saddr'      : 'source address' or source address list
                     'daddr'      : 'destination address' or destination list
                     'service'    : 'service name' or service list
                     'action'     : 'action, deny or permit'
                     'rtlog'      : 'rtlog'
                     'httplog'    : 'httplog'
                     'application': application name. eg icmp or ssh
                     'app-group'  : app-group name
                     'precedence' : Modify the order of rules (
                                  precedence_type: precedence type after|before|highest|lowest
                                  target_name    : Policy name
                                  target_id      : Policy name
                                  )
                     'description': Configure policy description
                     'app_control': Application control profile name
                     'app_log'    : Application logging profile name
                     'source-address-negate' : Configure source address or address group
                     'is_commit" : Commit pending configuration
     
            example  : va_config_policy(data1)
            return   : True/False
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        
        data1 = copy.deepcopy(data)
        
        pol_type = data1['type']

        # handle default value
        if not 'szone' in data1 :
            data1['szone'] = 'Trust'
        
        if not 'dzone' in data1 :
            data1['dzone'] = 'Untrust'
        
        if not 'saddr' in data1 :
            data1['saddr'] = 'any'
        
        if not 'daddr' in data1 :
            data1['daddr'] = 'any'
        
        if not 'service' in data1 :
            data1['service'] = 'any'
        
        if not 'action' in data1 :
            data1['action'] = 'permit'
        
        if not 'is_commit' in data1 :
            data1['is_commit'] = 'ON'
        
        if type(data1['saddr']) != list:
            saddr = [data1['saddr']]
        else :
            saddr = data1['saddr']

        if type(data1['daddr']) != list:
            daddr = [data1['daddr']]
        else :
            daddr = data1['daddr']

        if type(data1['service']) != list:
            service = re.split(' ',data1['service'])
        else :
            service = data1['service']

        cmds = []

        if (pol_type == "name") :
            policy_type = "name %s" % data1['name']
        elif (pol_type == 'id') :
            policy_type = "id %s" % data1['id']
        else :
            policy_type = "new" 

        cmds.append('set policy %s from %s to %s' % (policy_type, \
            data1['szone'], data1['dzone']))

        for saddr_name in saddr:
            cmds.append('set policy %s match source-address %s' % \
                (policy_type, saddr_name))
        
        for daddr_name in daddr:
            cmds.append('set policy %s match destination-address %s' % \
                (policy_type, daddr_name))

        for serv_name in service:
            cmds.append('set policy %s match service %s' % (policy_type, serv_name))

        cmds.append('set policy %s action %s' % (policy_type, data1['action']))

        if 'application' in data1 :
            cmds.append('set policy %s match application %s' % \
                        (policy_type, data1['application']))
            
        if 'app-group' in data1 :
            cmds.append('set policy %s match app-group %s' % \
                        (policy_type, data1['app-group']))

        if 'source-address-negate' in data1:
            cmds.append('set policy %s match source-address-negate %s'\
            %(policy_type, data1['source-address-negate']))

        if 'rtlog' in args :
            cmds.append('set policy %s rtlog enable' % policy_type)
        if 'httplog' in args :
            cmds.append('set policy %s httplog enable' % policy_type)
        if 'precedence' in data1 :
            if 'precedence_type' in data1['precedence'] :
                if re.search(r'after|before',data1['precedence']['precedence_type'], re.I) :
                    if 'target_name' in data1['precedence']['precedence_type'] :
                        cmds.append('set policy %s precedence %s target-name %s' % \
                                    (policy_type,data1['precedence']['precedence_type'],\
                                    data1['precedence']['precedence_type']['target_name']))
                    elif 'target_id' in data1['precedence']['precedence_type'] :
                        cmds.append('set policy %s precedence %s target-id %s' % \
                                    (policy_type,data1['precedence']['precedence_type'],\
                                    data1['precedence']['precedence_type']['target_id']))
                else :
                    cmds.append('set policy %s precedence %s' % (policy_type,\
                                 data1['precedence']['precedence_type']))
            else :
                userlog("ERROR","Please define precedence type 'after|before|highest|lowest'")
                return False
        if 'app_control' in data1 :
            cmds.append('set policy %s app-profile app-control %s' % (policy_type,data1['app_control']))

        if 'app_log' in data1 :
            cmds.append('set policy %s app-profile app-log %s' % (policy_type,data1['app_log']))

        if 'description' in data1 :
            cmds.append('set policy %s description "%s"' % (policy_type,data1['description']))
                    
        retcmds = cmds

        if not 'is_commit' in data1 :
            is_commit = "ON"
        else :
            is_commit = data1['is_commit']    

        ret_val, err_msg = self._access.va_config(cmds, commit=is_commit)
        
        if ret_val is not None :
            return False

        return True 
        

    def va_config_app_group(self, dataDict, *args, **kwargs):
        """
            API to config app group
    
            param    : 
                dataDict = {
                            name         :  Define custom app group name
                            application  : application name or application list
                            is_commit    : Whether commit command
                            }
            return   : True/False
            example  : app_group_data({
                                'name'        : 'test',
                                'application' : [],
                                'is_commit'   : 'ON'
                               })
                        va_config_app_group(app_group_data)
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        
        set_cmds = []
        data = copy.deepcopy(dataDict)
        
        # handle default value
        if 'name' in data :
            name = data['name']
        else:
            name = 'app_group_test'
        
        if 'application' in data :
            application = data['application']
            if not isinstance(application, list):
                app_list = [application]
            else:
                app_list = application
            for app in app_list:
                set_cmds.append('set profile app-group %s add application %s'  % (name, app))
        
        set_cmds.append('set profile app-group %s' % name)
        retcmds = copy.deepcopy(set_cmds)
        if not 'is_commit' in data :
            is_commit = 'ON'
        else :
            is_commit = data['is_commit']
        if is_commit.upper() == 'ON':
            set_cmds.append('commit')

        self._access.va_config(set_cmds)
        if is_commit.upper() == "ON" :
            if self._access.va_commit() is False:
                return False
        return True 

    def va_update_policy(self, *args, **kwargs):
        """
        API to update policy
        Param  :  kwargs : dict
                    kwargs = {
                                'mode'       : 'set or unset policy'
                                'name'       : 'policy name',
                                'id'         : 'policy id',
                                'szone'      : 'source zone',
                                'dzone'      : 'destination zone',
                                'saddr'      : 'source address',
                                'daddr'      : 'destination address',
                                'service'    : 'service name',
                                'action'     : 'action, deny or permit',
                                'application': 'application name. eg icmp or ssh',
                                'app-group'  : 'app-group name',
                                'precedence_type' : the order of rules, 
                                'target_name': precedence policy name,
                                'target_index': precedence police index,
                                'app_log'    : 'Application logging profile name',
                                'app-control': 'Application control profile name',
                                'description': 'set or unset policy description',
                                'source-address-negate' : 'Configure source address or address group',
                                'is_commit"  :  True|False (Default True)
                        }
                    args = [ 'rtlog'      : 'configure real time logging',
                             'httplog'    : 'configure http logging'
                                ]
        Return : Tuple
            True,cmd
            False,err_msg
        
        Example : va_update_policy(*args,**kwargs)
                kwargs = {
                    'mode' : 'set',
                    'name' : 'pol_test',
                    'szone': 'Intc',
                    'dzone': 'Intc',
                    'saddr': 'pc1',
                    'daddr': 'pc2',
                    'service' : 'DNS',
                    'action' : 'permit'
                    'application' : 'facebook'
                    }
                args = ['rtlog','httplog']
                
        """                
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        mode = kwargs.get('mode','set')        
        cmd = mode + ' policy '
        cmds = []
        
        if 'name' in kwargs:
            cmd = cmd + 'name {}'.format(kwargs['name'])
        elif 'id' in kwargs:
            cmd = cmd + 'id {}'.format(kwargs['id'])
        else:
            raise ValueError("name or id are mandatory parameters!\n")

        if len(kwargs.keys()) < 2 :
            error = "Please provide more parameters,example szone,saddr,daddr,service" 
            logger.error(error)
            return False,error
        
        if 'szone' in kwargs and 'dzone' in kwargs:
            cmds.append('{} from {} to {}'.format(cmd,kwargs['szone'],kwargs['dzone']))

        if 'saddr' in kwargs:
            cmds.append('{} match source-address {}'.format(cmd,kwargs['saddr']))

        if 'daddr' in kwargs:
            cmds.append('{} match destination-address {}'.format(cmd,kwargs['daddr']))

        if 'service' in kwargs:
            cmds.append('{} match service {}'.format(cmd,kwargs['service']))

        if 'application' in kwargs:
            cmds.append('{} match application {}'.format(cmd,kwargs['application']))

        if 'app-group' in kwargs:
            cmds.append('{} match app-group {}'.format(cmd,kwargs['app-group']))

        if 'source-address-negate' in kwargs:
            cmds.append('{} match source-address-negate {}'.format(cmd,kwargs['source-address-negate']))

        if 'action' in kwargs:
            cmds.append('{} action {}'.format(cmd,kwargs['action']))

        if 'rtlog' in args:
            cmds.append('{} rtlog enable'.format(cmd))

        if 'httplog' in args:
            cmds.append('{} httplog enable'.format(cmd))

        if mode == 'set' :
            if 'description' in kwargs:
                cmds.append('{} description {}'.format(cmd,kwargs['description']))                
            if 'precedence_type' in kwargs:
                if re.search(r'after|before',kwargs['precedence_type'],re.I):
                    if 'target_name' in kwargs :
                        cmds.append('{} precedence {} target-name {}'.format(cmd,kwargs['precedence_type'],\
                        kwargs['target_name']))
                    elif 'target_index' in kwargs :
                        cmds.append('{} precedence {} target-index {}'.format(cmd,kwargs['precedence_type'],\
                        kwargs['target_index']))                       
                    else :
                        error = "precedence type is after or before,must be set target-index or target-name"
                        logger.error(error)
                        return False,error
                else:
                    cmds.append('{} precedence {}'.format(cmd,kwargs['precedence_type']))
        else:
            if 'description' in kwargs:
                cmds.append('{} description'.format(cmd))

        if 'app_control' in kwargs:
            cmds.append('{} app-profile app-control {}'.format(cmd,kwargs['app_control']))
        
        if 'app_log' in kwargs:
            cmds.append('{} app-profile app-log {}'.format(cmd,kwargs['app_log']))
        
        is_commit = kwargs.get('is_commit',True)        
        rt,err_msg = self._access.va_config(cmds, commit=is_commit)

        if rt is not None or err_msg is not None:
            logger.error("Failed to {} policy".format(mode))
            return False,err_msg
        else:
            logger.info("Succeed to {} policy".format(mode))
            cmd_str = ','.join(cmds)
            cmds_list = (cmd_str.replace('unset','set')).split(',')
            return True,cmds_list
            
                    
