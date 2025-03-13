
# APP Proxmox Test Automation Script

This script automates tests on new ISO files that you want to try before putting them into production. The tests executed are listed in the file **OBIETTIVI**.

### Setup Instructions

- If you're running the script on **Linux**, execute the `setup.sh` file located in the `setup` folder.
- If you're running the script on **Windows**, execute the `install_python.bat` file.

### Running the Script

To start the script, simply click on `app.py` and the script will begin. During the execution, it will request sensitive information, so be cautious not to share it. The information includes:

- Node name
- IP address
- Gateway
- **Token** (The tests were performed using a token with maximum authorization levels. It is unclear exactly which permissions are needed, so you might want to create a token with root privileges if you don’t have other indications.)
- Finally, the ID of the template to be tested.

### Final Notes

Please ensure that all the prerequisites are installed and configured before running the tests. Take necessary precautions regarding security and sensitive data during the process.

If you encounter any issues, check the setup files and the test objectives to ensure everything is configured properly.
