import requests
from lxml import etree
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
import concurrent.futures
import os

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
def backup_juniper_configs(result):
    if 'fpc' not in result['name']:
        hostname = result['name'] + #cant show this
        if '#cant show this' in result['name'] or '#cant show this#' in result['name']:
            hostname = result['primary_ip']['address']
            hostname = hostname[:-3]
        junos_username = #cant show this
        junos_password = network_password

        dev = Device(host=hostname, user=junos_username, passwd=junos_password)

        try:
            dev.open()
            backup = dev.rpc.get_config(options={'format':'text'})
            set_backup = dev.rpc.get_config(options={'format':'set'})
            dev.close()
            
            print(f"Sucessful backup for: {hostname}")
            with open(f"set_format_backups/{hostname}.conf", "w") as outfile:
                outfile.write(etree.tostring(set_backup, encoding='unicode', pretty_print=True))
            with open(f"backups/{hostname}.conf", "w") as outfile:
                outfile.write(etree.tostring(backup, encoding='unicode', pretty_print=True))
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
            print((connection_result))
            
def main():
    print("Getting devices from netbox.")
    devices = get_devices()
    print("Done getting devices from netbox!")
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(backup_juniper_configs, result) for result in devices['results']]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)
    
if __name__ == "__main__":
    main()
