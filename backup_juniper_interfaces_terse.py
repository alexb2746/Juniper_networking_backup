import os
import requests
from lxml import etree
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
import concurrent.futures
from tabulate import tabulate
import xmltodict

# Retrieve the value of the GitLab variable
network_password = os.getenv('NETWORK_PASSWORD')

#This will make an API call to netbox using Alex's API token. It will return a list of devices that are active and have a platform of junos.
def get_devices():
    
    url = #specific link to netbox url

    payload = {}
    headers = {
      'Authorization': ##'Token #secret Token'
    }
    
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)

    return(response.json())

#for each physical interface we are going to see if it has none, 1 or multiple logical interfaces and add them to the table
def check_for_logical_interface(interface, logical_interface):
    if logical_interface in interface.keys():
        #check for multiple logical interfaces
        if isinstance(interface[logical_interface], list):
            name = []
            adminstatus = []
            operstatus = []
            for i in interface[logical_interface]:
                name.append(i['name'])
                adminstatus.append(i['admin-status'])
                operstatus.append(i['oper-status'])
            return name, adminstatus, operstatus
        return interface[logical_interface]['name'], interface[logical_interface]['admin-status'], interface[logical_interface]['oper-status']
    else:
        #if no logical interfaces just return "none"
        return "none", "none", "none"

#This will attempt to connect to each Juniper device and backup its configuration. It will also write the configuration in set format in the respective folders.
def juniper_interfaces_terse(result):
    if 'fpc' not in result['name']:
        hostname = result['name'] + #cant show this
        junos_username = #cant show this
        junos_password = network_password
        
        dev = Device(host=hostname, user=junos_username, passwd=junos_password)
        
        try:
            dev.open()
            interfaces_terse = dev.rpc.get_interface_information(terse=True)
            
            data = []
            headers = ["Physical-Interface Name", "Physical-Interface Admin Status", "Physical-Interface Oper Status", "Logical-Interface Name", "Logical-Interface Admin Status", "Logical-Interface Oper Status"]
            data.append(headers)
            interfaces_terse = xmltodict.parse(etree.tostring(interfaces_terse))
            
            #iterate through all physical interfaces and add them to the table
            #this also calls the "check_for_logical_interface" function to see 
            #if there are any logical interfaces and add them to the table
            for interface in interfaces_terse['interface-information']['physical-interface']:
                interface_information = [interface['name'], interface['admin-status'], interface['oper-status'], *check_for_logical_interface(interface, 'logical-interface')]
                data.append(interface_information)
                
                table = tabulate(data, headers="firstrow", tablefmt="pipe")
                #write to a text file in human readable format
                with open(f"interfaces_terse/{hostname}_interfaces_terse.md", "w") as outfile:
                    outfile.write(table)
                
            print(f"Host: {hostname} show interfaces terse done")
            dev.close()

        except ConnectError as err:
            print ("Cannot connect to device: {0}".format(err))
            reason = str(err)
            connection_result = {
                "Hostname": hostname,
                "connection": "Unsuccessful",
                "reason": reason
            }
            print(connection_result)
            
        except Exception as err:
            print (err)
            reason = str(err)
            connection_result = {
                "Hostname": hostname,
                "connection": "Unsuccessful",
                "reason": reason
            }
            print(connection_result)
            
def main():
    print("Getting devices from netbox.")
    devices = get_devices()
    print("Done getting devices from netbox!")
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(juniper_interfaces_terse, result) for result in devices['results']]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)
    
if __name__ == "__main__":
    main()