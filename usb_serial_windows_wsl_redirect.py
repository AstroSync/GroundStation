import subprocess
import re
import time
proc = subprocess.Popen(["usbipd", "wsl", "list"], stdout=subprocess.PIPE)
out, err = proc.communicate()
data = " ".join(out.decode('utf-8').split())
matches = re.findall( r'\d+-\d', data)
print(f'busid: {matches}')
for val in matches:
    data = data.replace(val, f'\n{val}')
print(data)
busid_list = [s.split()[0] for s in data.split('\n') if 'USB Serial Converter' in s]
for busid in busid_list:
    subprocess.Popen(["usbipd", "wsl", "attach", "--busid", busid])
    time.sleep(1)