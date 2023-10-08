import sys
import file_info_utils

file_data = file_info_utils.get_file_version_info(sys.executable)
assert file_data["ProductVersion"] == "2.2.2"
assert file_data["FileDescription"] == "Binary's 2 description"
assert file_data["Comments"] == "Comments for binary 2"
assert file_data["CompanyName"] == "Binary 2 developers and testers"
assert file_data["LegalCopyright"] == "2023 - binary2  author"
assert file_data["ProductName"] == "Binary 2"
assert file_data["FileVersion"] == "2.2.2"
