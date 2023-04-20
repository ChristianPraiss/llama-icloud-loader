from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException, PyiCloudException
import os
from shutil import copyfileobj

# Folders names to ignore
blacklist = ['Backups', 'AHSQ', 'Design Resources', '3D Printing']

# Replace these with your iCloud credentials
try:
    APPLE_ID = os.environ['APPLE_ID']
    PASSWORD = os.environ['APPLE_PASSWORD']
except KeyError:
    print("Please set the environment variables APPLE_ID and APPLE_PASSWORD")
    exit(1)

try:
    # Authenticate with your iCloud account
    api = PyiCloudService(APPLE_ID, PASSWORD)
except PyiCloudFailedLoginException as e:
    print("Invalid username or password.")
    exit(1)

if api.requires_2fa:
    print("Two-factor authentication required.")
    code = input(
        "Enter the code you received of one of your approved devices: ")
    result = api.validate_2fa_code(code)
    print("Code validation result: %s" % result)

    if not result:
        print("Failed to verify security code")
        sys.exit(1)

    if not api.is_trusted_session:
        print("Session is not trusted. Requesting trust...")
        result = api.trust_session()
        print("Session trust result %s" % result)

        if not result:
            print(
                "Failed to request trust. You will likely be prompted for the code again in the coming weeks")
elif api.requires_2sa:
    import click
    print("Two-step authentication required. Your trusted devices are:")

    devices = api.trusted_devices
    for i, device in enumerate(devices):
        print(
            "  %s: %s" % (i, device.get('deviceName',
                                        "SMS to %s" % device.get('phoneNumber')))
        )

    device = click.prompt('Which device would you like to use?', default=0)
    device = devices[device]
    if not api.send_verification_code(device):
        print("Failed to send verification code")
        sys.exit(1)

    code = click.prompt('Please enter validation code')
    if not api.validate_verification_code(device, code):
        print("Failed to verify verification code")
        sys.exit(1)


def find_pdf_files(node, path=None, limit=3):
    if path is None:
        path = []

    pdf_files = []

    for item_name in node.dir():
        if limit == 0:
            return pdf_files
        current_path = path + [item_name]
        current_node = node[item_name]

        if current_node.type == 'folder' and item_name not in blacklist:
            pdf_files.extend(find_pdf_files(
                current_node, current_path, limit=limit))

        elif item_name.lower().endswith('.pdf'):
            print('found pdf file', current_path)
            pdf_files.append((current_node, '/'.join(current_path)))
            limit -= 1

    return pdf_files


def save_file_to_disk(file_node, file_path, output_directory):
    # Create the necessary directories
    local_path = os.path.join(output_directory, file_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # Save the file to the local path
    with file_node.open(stream=True) as response:
        with open(local_path, 'wb') as file_out:
            copyfileobj(response.raw, file_out)


output_directory = 'downloaded_pdfs'

all_pdf_files = find_pdf_files(api.drive)

for pdf_file, file_path in all_pdf_files:
    print(f"Saving PDF file: {file_path}")
    save_file_to_disk(pdf_file, file_path, output_directory)
