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
def juniper_ospf_neighbors(result):
    if 'fpc' not in result['name']: 
        hostname = result['name'] + #cant show this 
        junos_username = #cant show this
        junos_password = network_password
        
        dev = Device(host=hostname, user=junos_username, passwd=junos_password)
        
        try:
            dev.open()
            ospf_neighbors = dev.rpc.get_ospf_neighbor_information(instance='all')
            
            data = []
            headers = ["Instance", "Address", "Interface", "State", "ID"]
            data.append(headers)
            ospf_neighbors = xmltodict.parse(etree.tostring(ospf_neighbors))
            #Check if any ospf is running, if not return nothing (essentially skip this host)
            if 'ospf-neighbor-information-all' not in ospf_neighbors.keys():
                return
            
            #Need to check if there are multiple instances of OSPF running on the device
            if isinstance(ospf_neighbors['ospf-neighbor-information-all']['ospf-instance-neighbor'], list):
                #iterate through the list of instances
                for ospf_instance_neighbor in ospf_neighbors['ospf-neighbor-information-all']['ospf-instance-neighbor']:
                    #check if there are ospf neighbors within the particular instance
                    if 'ospf-neighbor' in ospf_instance_neighbor.keys():
                        #check if there is one or multiple ospf neighbors
                        if isinstance(ospf_instance_neighbor['ospf-neighbor'], list):
                            #iterate through all ospf neighbors and add them to the table
                            for ospf_neighbor in ospf_instance_neighbor['ospf-neighbor']:
                                ospf_neighbor_information = [ospf_instance_neighbor['ospf-instance-name'], ospf_neighbor['neighbor-address'], ospf_neighbor['interface-name'], ospf_neighbor['ospf-neighbor-state'], ospf_neighbor['neighbor-id']]
                                data.append(ospf_neighbor_information)
                            data.append(["---", "---", "---", "---", "---"])
                        #if there is a single ospf neighbor this is where we add it to the table
                        else:
                            ospf_neighbor_information = [ospf_instance_neighbor['ospf-instance-name'], ospf_instance_neighbor['ospf-neighbor']['neighbor-address'], ospf_instance_neighbor['ospf-neighbor']['interface-name'], ospf_instance_neighbor['ospf-neighbor']['ospf-neighbor-state'], ospf_instance_neighbor['ospf-neighbor']['neighbor-id']]
                            data.append(ospf_neighbor_information)
                            data.append(["---", "---", "---", "---", "---"])
                    #if there is no neighbors in the instance, then just add the instance name and a message
                    else:
                        data.append([ospf_instance_neighbor['ospf-instance-name'], "No Neighbors Found in this Instance", "---", "---", "---"])
            
            #if there is only one instance of ospf running on the device
            else:
                instance_name = ospf_neighbors['ospf-neighbor-information-all']['ospf-instance-neighbor']['ospf-instance-name']
                for ospf_neighbor in ospf_neighbors['ospf-neighbor-information-all']['ospf-instance-neighbor']['ospf-neighbor']:
                    ospf_neighbor_information = [instance_name, ospf_neighbor['neighbor-address'], ospf_neighbor['interface-name'], ospf_neighbor['ospf-neighbor-state'], ospf_neighbor['neighbor-id']]
                    data.append(ospf_neighbor_information)
                
            table = tabulate(data, headers="firstrow", tablefmt="pipe")
            #write to a text file in human readable format
            with open(f"ospf_neighbors/{hostname}_ospf_neighbors.md", "w") as outfile:
                outfile.write(table)
                
            print(f"Host: {hostname} show ospf neighbors done")
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
        futures = [executor.submit(juniper_ospf_neighbors, result) for result in devices['results']]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)
    
if __name__ == "__main__":
    main()