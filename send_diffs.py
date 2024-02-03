import requests
import json
import os

gitlab_url = #gitlab link
token = os.getenv('PRIVATE_TOKEN') # 

# Set the headers for the API requests
headers = {"PRIVATE-TOKEN": token}

# Fetch the most recent commits
response = requests.get(gitlab_url, headers=headers)
response.raise_for_status()  # Raise an exception if the request failed

commits = response.json()
latest_commit_id = commits[0]['id']  # Assumes the commits are sorted latest first

# Fetch the diff of the latest commit
diff_url = f"{gitlab_url}/{latest_commit_id}/diff"
response = requests.get(diff_url, headers=headers)
response.raise_for_status()  # Raise an exception if the request failed

diffs = response.json()
blocks = []
# Check each diff to see if 'backups/' is in the 'old_path'
for diff in diffs:
    if 'backups/' in diff['old_path']:
        #print(diff['diff'])
        s = diff['old_path']
        # remove "backups/" from the start
        if s.startswith("backups/"):
            s = s[len("backups/"):]
        
        # remove ".conf" from the end
        if s.endswith(".conf"):
            s = s[: -len(".conf")]
        
        # message_text += f"{s} has changed:\n"
        # message_text += diff['diff']
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{s} has changed:*"
            }
        })

        # Append a code block for the diff
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```\n{diff['diff']}\n```"
            }
        })

# Your bot's OAuth access token
token = os.getenv("O_AUTH_SLACK")

# ID of the target channel
channel_id = #cant show this

# Prepare headers
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer {}".format(token)
}

# Construct the JSON payload
payload = {
    "channel": channel_id,
    "blocks": blocks,
}

# Send the POST request
response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, data=json.dumps(payload))

# Check the response
if response.status_code != 200:
    
    raise Exception(
        "Request to slack returned an error %s, the response is:\n%s"
        % (response.status_code, response.text)
    )