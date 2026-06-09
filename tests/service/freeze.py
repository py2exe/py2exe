from py2exe import freeze

freeze(
    service=[
        {
            "modules": ["service_test"],
            "cmdline_style": "pywin32",
        }
    ],
)
