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

#This will attempt to connect to each Juniper device and backup its configuration. It will also write the configuration in set format in the respective folders.
def juniper_bgp_summary(result):
    if 'fpc' not in result['name']: 
        #this command cannot be run on EX3400's
        if 'EX3400' not in result['device_type']['model']:
            hostname = result['name'] + #cant show this
            junos_username = #cant show this
            junos_password = network_password
            
            dev = Device(host=hostname, user=junos_username, passwd=junos_password)
            
            try:
                dev.open()
                bgp_summary = dev.rpc.get_bgp_summary_information()
                
                data = []
                headers = ["Peer", "AS", "Flaps", "Last Up/Down", "State", "Description"]
                data.append(headers)
                bgp_summary = xmltodict.parse(etree.tostring(bgp_summary))
                
                #Check if any bgp is running, if not return nothing (essentially skip this host)
                if 'bgp-information' not in bgp_summary.keys():
                    return
                
                #iterate through all bgp peers and add them to the table
                for peer in bgp_summary['bgp-information']['bgp-peer']:
                    data.append([peer['peer-address'], peer['peer-as'], peer['flap-count'], peer['elapsed-time']['#text'], 
                                peer['peer-state']['#text'] if '#text' in peer['peer-state'] else peer['peer-state'], 
                                peer['description'] if 'description' in peer.keys() else "No Description"])
                table = tabulate(data, headers="firstrow", tablefmt="pipe")
                    #write to a text file in human readable format
                with open(f"bgp_summary/{hostname}_bgp_summary.md", "w") as outfile:
                    outfile.write(table)
                    
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
                
            except KeyError as err:
                print (f"KEY ERROR ********************: {err}")
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
        futures = [executor.submit(juniper_bgp_summary, result) for result in devices['results']]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)
    
if __name__ == "__main__":
    main()