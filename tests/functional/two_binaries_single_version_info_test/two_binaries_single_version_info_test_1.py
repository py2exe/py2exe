import sys
import file_info_utils

file_data = file_info_utils.get_file_version_info(sys.executable)
assert file_data["ProductVersion"] == "1.2.3"
assert file_data["FileDescription"] == "My binary"
assert file_data["Comments"] == "Comments for my binary"
assert file_data["CompanyName"] == "My avesome company"
assert file_data["LegalCopyright"] == "2023 - binary author"
assert file_data["ProductName"] == "Sample binary"
assert file_data["FileVersion"] == "1.2.3"
