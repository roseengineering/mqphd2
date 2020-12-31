
import os, subprocess 

def copy(filename, path):
    command = f"base64 -w60 {filename} | sed 's/^/        /'"
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    buf = proc.stdout.read().decode()
    proc.wait()
    return f"""\
  - become: yes
    copy:
      mode: 0755
      dest: {path}
      content: !!binary |\n{buf}
"""

print(f"""\
---

  # headless

  - become: yes
    apt:
      name:
      - xvfb

  # pip

  - become: yes
    pip:
      name:
      - paho-mqtt

  # code

{copy("mqphd2.py", "/usr/local/bin/mqphd2")}

  - become: yes
    copy:
      dest: /lib/systemd/system/mqphd2.service
      content: |
        [Service]
        ExecStart=/usr/bin/python3 -u /usr/local/bin/mqphd2
        User={os.environ['USER']}
        Restart=on-failure
        RestartSec=10s
        [Install]
        WantedBy=multi-user.target

  - become: yes
    shell: |
      sudo systemctl enable mqphd2
      sudo systemctl restart mqphd2
""")


