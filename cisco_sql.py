import mysql.connector
from netmiko import ConnectHandler, NetMikoTimeoutException
from datetime import datetime

begin_time = datetime.now() # Time stamp to understand how long the entire job took, will factor in after job is complete

'''
    This app is logs into a cisco device and enables PIM on all layer 3 interfaces
        - retrieves list of all layer 3 interfaces
        - configures each interface with pim sparse-mode
    The following block of code handles the database functions.
        - establish SQL server and configuration elements to login
        - retrieve a list of network devices
'''

config = {
  'user': 'calvin',
  'password': 'password',
  'host': '172.16.96.130',
  'database': 'devices',
  'raise_on_warnings': True,
}

cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()

query = ("SELECT hostname, device_vendor, device_type, mgmt_ip FROM network_devices "
         "WHERE device_vendor LIKE 'Cisco'")

cursor.execute(query)

'''
    The following block handles the username and password for network devices.
'''

username = raw_input('please enter your username:\n')
password = raw_input('please enter your password:\n')

'''
    The following block of code is the meat and potatoes of the app.
        - creates a dictionary named device to hold values of device
        - creates a login session for every device retrieved from the database
        - sends 'show ip interface b | ex ass|Interface', splits up output by horizontal line
        - lambda function splits up the ip_interface_split output by blank space, stores the 1st column as interface variable
'''

for (hostname, device_vendor, device_type, mgmt_ip) in cursor:
    start_time = datetime.now()  # logging timestamps
    device = {'device_type': 'cisco_ios',
              'ip': mgmt_ip,
              'username': username,
              'password': password,
              'verbose': False,}
    try:
        ssh_session = ConnectHandler(**device)
        hostname = ssh_session.find_prompt() # removes the # sign and stores as variable hostname
        hostname = hostname.replace("#", "") # some pretty printing to display the hostname
        print("=" * 64 + "\n" + 29 * " " + "% s \n" + "=" * 64) % hostname
        output = ssh_session.send_command('show ip interface b | ex ass|Interface')
        ip_interface_split = output.splitlines()
        ip_interface = map(lambda temp: temp.split()[0], ip_interface_split)
        '''
            The following block of code handles the configuraiton compliance.
                - check for current PIM enabled interfaces with 'show run inter ' + interface + ' | include pim'
                    - if the word 'pim' is found within show_run_interface_pim, then PIM has been configured
                    - if 'pim' is not found, then enter the interface's configuration mode and properly update the configuration
        '''
        for interface in ip_interface:
            try:
                show_run_interface_pim = ssh_session.send_command('show run inter ' + interface + ' | include pim')
                print "\nInterface {0} ".format(interface) # some console output to let us know which interface we are on
                if 'pim' in show_run_interface_pim:
                    print "Multicast Enabled: True"
                    print "Action Taken: None"
                    pass
                else:
                    print "Multicast Enabled: False"
                    print "PIM Sparse-Mode added to interface configuration"
                    updatePIM = ['interface % s \n ip pim sparse-mode\n' % interface]
                    ssh_session.send_config_set(updatePIM) # netmiko command to send to the switch
            except IndexError: # this allows the loop to continue when running into an IndexError
                continue

        '''
            additional time stamp information
        '''
        end_time = datetime.now()
        total_time = end_time - start_time
        print("\ntotal time spent on " + hostname + ": " + str(total_time) + '\n')
    except NetMikoTimeoutException:
        print hostname + " timed out, bypassing"
        continue

'''
    additional time stamp information
'''
final_time = datetime.now()
complete_time = final_time - begin_time
print("\n\nFinished running the script in " + str(complete_time) + " seconds")
