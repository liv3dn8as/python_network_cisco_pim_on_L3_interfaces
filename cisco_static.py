from netmiko import ConnectHandler
from device_credientials import lab_devices
from datetime import datetime

# Time stamp to understand how long the entire job took, will factor in after job is complete
begin_time = datetime.now()

# for loop to iterate over all devices within the all_physical dictionary within device_credientials
for a_device in lab_devices:
    # additional time stamp to understand how long each device takes
    start_time = datetime.now()  # logging timestamps
    # create a variable to manage the SSH session
    ssh_session = ConnectHandler(**a_device)
    # finds the prompt from the Cisco IOS device
    hostname = ssh_session.find_prompt()
    # removes the # sign and stores as variable hostname
    hostname = hostname.replace("#", "")
    # some pretty printing to display which host we're currently working on within terminal
    print("=" * 64 + "\n" + 29 * " " + "% s \n" + "=" * 64) % hostname
    # sends command 'show ip interface b | ex ass|Interface' and stores data in variable
    # here we exclude the word Interface to assist in the screen scraping. We only want interfaces, not the headers
    # Cisco provides within the 'show' output.
    output = ssh_session.send_command('show ip interface b | ex ass|Interface')
    # here we split the return value to begin iterating over
    ip_interface_split = output.splitlines()
    # lambda function splits up the ip_interface_split output by blank space, stores the 1st column (0) as interface variable
    ip_interface = map(lambda temp: temp.split()[0], ip_interface_split)
    # here we say: for every ip_interface...
    for interface in ip_interface:
        # the purpose of the try/except is prevent the loop from failing if there aren't any entries to reference
        # on that line (empty lines). if this part of the loop was missing, the loop would fail when trying to create
        # a variable from an empty list.
        try:
            # we store this as a variable show_run_interface_pim, and will later perform a matching sequence against
            show_run_interface_pim = ssh_session.send_command('show run inter ' + interface + ' | include pim')
            # some console output to let us know which interface is being worked on.
            print "\nInterface {0} ".format(interface)
            # magic starts here. if the word 'pim' is found within show_run_interface_pim, then PIM has been configured
            # terminal output is produced to let the user know that no further actions are taken.
            # if 'pim' is not found, then enter the interface's configuration mode and properly update the configuration
            # produce some output within the terminal as well.
            if 'pim' in show_run_interface_pim:
                print "Multicast Enabled: True"
                print "Action Taken: None"
                pass
            else:
                print "Multicast Enabled: False"
                print "PIM Sparse-Mode added to interface configuration"
                # here is the command we wish to send to the incorrectly configured interface
                updatePIM = ['interface % s \n ip pim sparse-mode\n' % interface]
                # netmiko command to send to the switch
                ssh_session.send_config_set(updatePIM)
        # this allows the loop to continue when running into an IndexError
        except IndexError:
            continue

    # additional time stamp
    end_time = datetime.now()
    # subtracts end_time from start_time to receive total_time
    total_time = end_time - start_time
    # prints out total_time spent on device
    print("\ntotal time spent on " + hostname + ": " + str(total_time) + '\n')

# additional time stamp
final_time = datetime.now()
# subtracts begin_time from final_time to receive complete_time
complete_time = final_time - begin_time
# prints out total time to run the job
print("\n\nFinished running the script in " + str(complete_time) + " seconds")
