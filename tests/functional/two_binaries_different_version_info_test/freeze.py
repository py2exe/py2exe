import os
import sys

from py2exe import freeze

sys.path.append(os.path.join("..", "..", "_helpers"))  # So that file version utils can be found when freezing.


freeze(
    console=[
        {
            "script": "two_binaries_different_version_info_test_1.py",
            "version_info": {
                "version": "1.1.1",
                "description": "Binary's 1 description",
                "comments": "Comments for binary 1",
                "company_name": "Binary 1 developers and testers",
                "copyright": "2023 - binary1  author",
                "product_name": "Binary 1",
                "product_version": "1.1.1",
            }
        },
        {
            "script": "two_binaries_different_version_info_test_2.py",
            "version_info": {
                "version": "2.2.2",
                "description": "Binary's 2 description",
                "comments": "Comments for binary 2",
                "company_name": "Binary 2 developers and testers",
                "copyright": "2023 - binary2  author",
                "product_name": "Binary 2",
                "product_version": "2.2.2",
            }
        }
    ],
)
