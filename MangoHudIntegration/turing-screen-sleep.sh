# 1) copy this script to /usr/lib/systemd/system-sleep/turing-screen-sleep.sh
# 2) make it executable with chmod +x /usr/lib/systemd/system-sleep/turing-screen-sleep.sh
#
# this script will stop the turing-smart-screen-python service before suspend/hibernate and restart it after resume
# if the device is not connected, it will not restart the service

#!/bin/bash

case $1 in
  pre)
    # Stop service before suspend/hibernate
    systemctl stop turing-smart-screen-python.service
    ;;
  post)
    # Optionally restart after resume (only if device is connected)
    # Remove this section if you want UDEV to handle restart on device detection
    if [ -e /dev/ttyACM0 ]; then
      systemctl start turing-smart-screen-python.service
    fi
    ;;
esac
