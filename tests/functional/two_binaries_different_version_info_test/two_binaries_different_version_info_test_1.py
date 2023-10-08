import sys
import file_info_utils

file_data = file_info_utils.get_file_version_info(sys.executable)
assert file_data["ProductVersion"] == "1.1.1"
assert file_data["FileDescription"] == "Binary's 1 description"
assert file_data["Comments"] == "Comments for binary 1"
assert file_data["CompanyName"] == "Binary 1 developers and testers"
assert file_data["LegalCopyright"] == "2023 - binary1  author"
assert file_data["ProductName"] == "Binary 1"
assert file_data["FileVersion"] == "1.1.1"
