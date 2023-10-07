import os
import sys

from py2exe import freeze

sys.path.append(os.path.join("..", "..", "_helpers"))  # So that file version utils can be found when freezing.


freeze(
    console=[{"script": "two_binaries_single_version_info_test_1.py"}, {"script": "two_binaries_single_version_info_test_2.py"}],
    version_info={
        "version": "1.2.3",
        "description": "My binary",
        "comments": "Comments for my binary",
        "company_name": "My avesome company",
        "copyright": "2023 - binary author",
        "product_name": "Sample binary",
        "product_version": "1.2.3",
    }
)
