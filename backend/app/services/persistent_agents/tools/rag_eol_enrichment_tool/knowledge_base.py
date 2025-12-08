# SKIP_FILE_LENGTH_CHECK - Pure EOL data dictionary (no code logic)
"""
EOL Knowledge Base

Embedded EOL knowledge from endoflife.date (cached locally).
This serves as the RAG knowledge base for EOL lookups.

Data structure contains vendor products with version information including:
- EOL dates
- Extended support dates
- Release dates
- Source attribution
"""

EOL_KNOWLEDGE_BASE = {
    # Operating Systems
    "rhel": {
        "vendor": "Red Hat",
        "product": "Red Hat Enterprise Linux",
        "versions": {
            "7": {
                "eol": "2024-06-30",
                "extended_support": "2028-06-30",
                "release": "2014-06-10",
            },
            "8": {
                "eol": "2029-05-31",
                "extended_support": "2032-05-31",
                "release": "2019-05-07",
            },
            "9": {
                "eol": "2032-05-31",
                "extended_support": "2035-05-31",
                "release": "2022-05-17",
            },
        },
        "source": "endoflife.date/rhel",
    },
    "oracle-linux": {
        "vendor": "Oracle",
        "product": "Oracle Linux",
        "versions": {
            "7": {
                "eol": "2024-12-31",
                "extended_support": None,
                "release": "2014-07-23",
            },
            "8": {
                "eol": "2029-07-31",
                "extended_support": None,
                "release": "2019-07-18",
            },
            "9": {
                "eol": "2032-06-30",
                "extended_support": None,
                "release": "2022-07-06",
            },
        },
        "source": "endoflife.date/oracle-linux",
    },
    "windows-server": {
        "vendor": "Microsoft",
        "product": "Windows Server",
        "versions": {
            "2012": {
                "eol": "2023-10-10",
                "extended_support": "2026-10-13",
                "release": "2012-09-04",
            },
            "2012-r2": {
                "eol": "2023-10-10",
                "extended_support": "2026-10-13",
                "release": "2013-10-18",
            },
            "2016": {
                "eol": "2027-01-12",
                "extended_support": "2027-01-12",
                "release": "2016-10-12",
            },
            "2019": {
                "eol": "2029-01-09",
                "extended_support": "2029-01-09",
                "release": "2018-11-13",
            },
            "2022": {
                "eol": "2031-10-14",
                "extended_support": "2031-10-14",
                "release": "2021-08-18",
            },
        },
        "source": "microsoft.com/lifecycle",
    },
    "aix": {
        "vendor": "IBM",
        "product": "AIX",
        "versions": {
            "7.1": {
                "eol": "2023-04-30",
                "extended_support": None,
                "release": "2010-09-10",
            },
            "7.2": {
                "eol": "2023-12-31",
                "extended_support": None,
                "release": "2015-12-11",
            },
            "7.3": {
                "eol": "2028-12-31",
                "extended_support": None,
                "release": "2021-12-10",
            },
        },
        "source": "ibm.com/support/lifecycle",
    },
    "zos": {
        "vendor": "IBM",
        "product": "z/OS",
        "versions": {
            "2.4": {
                "eol": "2024-09-30",
                "extended_support": None,
                "release": "2019-09-13",
            },
            "2.5": {
                "eol": "2026-09-30",
                "extended_support": None,
                "release": "2021-09-24",
            },
            "3.1": {
                "eol": "2028-09-30",
                "extended_support": None,
                "release": "2023-09-14",
            },
        },
        "source": "ibm.com/support/lifecycle",
    },
    "ubuntu": {
        "vendor": "Canonical",
        "product": "Ubuntu",
        "versions": {
            "18.04": {
                "eol": "2023-04-02",
                "extended_support": "2028-04-01",
                "release": "2018-04-26",
            },
            "20.04": {
                "eol": "2025-04-02",
                "extended_support": "2030-04-02",
                "release": "2020-04-23",
            },
            "22.04": {
                "eol": "2027-04-01",
                "extended_support": "2032-04-09",
                "release": "2022-04-21",
            },
            "24.04": {
                "eol": "2029-04-25",
                "extended_support": "2034-04-25",
                "release": "2024-04-25",
            },
        },
        "source": "endoflife.date/ubuntu",
    },
    # Databases
    "oracle-database": {
        "vendor": "Oracle",
        "product": "Oracle Database",
        "versions": {
            "11.2": {
                "eol": "2018-12-31",
                "extended_support": "2020-12-31",
                "release": "2009-09-01",
            },
            "12.1": {
                "eol": "2019-07-31",
                "extended_support": "2022-07-31",
                "release": "2013-06-25",
            },
            "12.2": {
                "eol": "2021-03-31",
                "extended_support": "2024-03-31",
                "release": "2017-03-01",
            },
            "18": {
                "eol": "2021-06-30",
                "extended_support": "2024-06-30",
                "release": "2018-02-16",
            },
            "19": {
                "eol": "2027-04-30",
                "extended_support": "2030-04-30",
                "release": "2019-01-23",
            },
            "21": {
                "eol": "2024-04-30",
                "extended_support": None,
                "release": "2020-12-08",
            },
            "23": {
                "eol": "2029-04-30",
                "extended_support": "2032-04-30",
                "release": "2023-09-11",
            },
        },
        "source": "oracle.com/support/lifetime-support",
    },
    "sql-server": {
        "vendor": "Microsoft",
        "product": "SQL Server",
        "versions": {
            "2012": {
                "eol": "2017-07-11",
                "extended_support": "2022-07-12",
                "release": "2012-03-06",
            },
            "2014": {
                "eol": "2019-07-09",
                "extended_support": "2024-07-09",
                "release": "2014-04-01",
            },
            "2016": {
                "eol": "2021-07-13",
                "extended_support": "2026-07-14",
                "release": "2016-06-01",
            },
            "2017": {
                "eol": "2022-10-11",
                "extended_support": "2027-10-12",
                "release": "2017-10-02",
            },
            "2019": {
                "eol": "2025-01-07",
                "extended_support": "2030-01-08",
                "release": "2019-11-04",
            },
            "2022": {
                "eol": "2028-01-11",
                "extended_support": "2033-01-11",
                "release": "2022-11-16",
            },
        },
        "source": "microsoft.com/lifecycle",
    },
    "postgresql": {
        "vendor": "PostgreSQL Global Development Group",
        "product": "PostgreSQL",
        "versions": {
            "11": {
                "eol": "2023-11-09",
                "extended_support": None,
                "release": "2018-10-18",
            },
            "12": {
                "eol": "2024-11-14",
                "extended_support": None,
                "release": "2019-10-03",
            },
            "13": {
                "eol": "2025-11-13",
                "extended_support": None,
                "release": "2020-09-24",
            },
            "14": {
                "eol": "2026-11-12",
                "extended_support": None,
                "release": "2021-09-30",
            },
            "15": {
                "eol": "2027-11-11",
                "extended_support": None,
                "release": "2022-10-13",
            },
            "16": {
                "eol": "2028-11-09",
                "extended_support": None,
                "release": "2023-09-14",
            },
        },
        "source": "endoflife.date/postgresql",
    },
    "mysql": {
        "vendor": "Oracle",
        "product": "MySQL",
        "versions": {
            "5.7": {
                "eol": "2023-10-31",
                "extended_support": None,
                "release": "2015-10-21",
            },
            "8.0": {
                "eol": "2026-04-30",
                "extended_support": None,
                "release": "2018-04-19",
            },
        },
        "source": "endoflife.date/mysql",
    },
    # Runtimes
    "java": {
        "vendor": "Oracle",
        "product": "Java SE",
        "versions": {
            "8": {
                "eol": "2022-03-31",
                "extended_support": "2030-12-31",
                "release": "2014-03-18",
            },
            "11": {
                "eol": "2024-09-30",
                "extended_support": "2032-01-31",
                "release": "2018-09-25",
            },
            "17": {
                "eol": "2027-09-30",
                "extended_support": "2029-09-30",
                "release": "2021-09-14",
            },
            "21": {
                "eol": "2028-09-30",
                "extended_support": "2031-09-30",
                "release": "2023-09-19",
            },
        },
        "source": "oracle.com/java/lifecycle",
    },
    "openjdk": {
        "vendor": "OpenJDK Community",
        "product": "OpenJDK",
        "versions": {
            "8": {
                "eol": "2030-12-31",
                "extended_support": None,
                "release": "2014-03-18",
            },
            "11": {
                "eol": "2027-10-31",
                "extended_support": None,
                "release": "2018-09-25",
            },
            "17": {
                "eol": "2029-09-30",
                "extended_support": None,
                "release": "2021-09-14",
            },
            "21": {
                "eol": "2031-09-30",
                "extended_support": None,
                "release": "2023-09-19",
            },
        },
        "source": "endoflife.date/openjdk",
    },
    "dotnet": {
        "vendor": "Microsoft",
        "product": ".NET",
        "versions": {
            "5": {
                "eol": "2022-05-10",
                "extended_support": None,
                "release": "2020-11-10",
            },
            "6": {
                "eol": "2024-11-12",
                "extended_support": None,
                "release": "2021-11-08",
            },
            "7": {
                "eol": "2024-05-14",
                "extended_support": None,
                "release": "2022-11-08",
            },
            "8": {
                "eol": "2026-11-10",
                "extended_support": None,
                "release": "2023-11-14",
            },
        },
        "source": "endoflife.date/dotnet",
    },
    "nodejs": {
        "vendor": "OpenJS Foundation",
        "product": "Node.js",
        "versions": {
            "16": {
                "eol": "2023-09-11",
                "extended_support": None,
                "release": "2021-04-20",
            },
            "18": {
                "eol": "2025-04-30",
                "extended_support": None,
                "release": "2022-04-19",
            },
            "20": {
                "eol": "2026-04-30",
                "extended_support": None,
                "release": "2023-04-18",
            },
            "22": {
                "eol": "2027-04-30",
                "extended_support": None,
                "release": "2024-04-24",
            },
        },
        "source": "endoflife.date/nodejs",
    },
    "python": {
        "vendor": "Python Software Foundation",
        "product": "Python",
        "versions": {
            "3.7": {
                "eol": "2023-06-27",
                "extended_support": None,
                "release": "2018-06-27",
            },
            "3.8": {
                "eol": "2024-10-31",
                "extended_support": None,
                "release": "2019-10-14",
            },
            "3.9": {
                "eol": "2025-10-31",
                "extended_support": None,
                "release": "2020-10-05",
            },
            "3.10": {
                "eol": "2026-10-31",
                "extended_support": None,
                "release": "2021-10-04",
            },
            "3.11": {
                "eol": "2027-10-31",
                "extended_support": None,
                "release": "2022-10-24",
            },
            "3.12": {
                "eol": "2028-10-31",
                "extended_support": None,
                "release": "2023-10-02",
            },
        },
        "source": "endoflife.date/python",
    },
}
