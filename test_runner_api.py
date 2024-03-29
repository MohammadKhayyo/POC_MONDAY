# from pathlib import Path
from typing import Type
import unittest
from concurrent.futures import ThreadPoolExecutor
import sys

# try:
#     sys.path.insert(0, '/usr/src/tests')
# except:
#     pass

# Now try importing ConfigurationManager

from Utils.configurations import ConfigurationManager
from Tests.api.work_space_test import WorkSpaceTest
from Tests.api.board_test import BoardTest
from Tests.api.group_test import GroupTest
from Tests.api.column_test import ColumnTest
from Tests.api.item_test import ItemTest

all_test_groups = [WorkSpaceTest, BoardTest, GroupTest, ColumnTest, ItemTest]


def execute_test_with_browser(browser_name: str, test_group: Type[unittest.TestCase]):
    test_group.browser = browser_name
    test_suite = unittest.TestLoader().loadTestsFromTestCase(test_group)
    unittest.TextTestRunner().run(test_suite)


def run_tests_for_browser_serial(browser_list, test_groups):
    for test in test_groups:
        for browser in browser_list:
            execute_test_with_browser(browser, test)


def run_tests_for_browser_parallel(browser_list, test_groups):
    task_list = [(browser, test_case) for browser in browser_list for test_case in test_groups]

    with ThreadPoolExecutor(max_workers=len(all_test_groups)) as executor:
        [executor.submit(execute_test_with_browser, browser, test) for browser, test in task_list]


if __name__ == "__main__":
    config_manager = ConfigurationManager()
    settings = config_manager.load_settings()
    is_parallel = settings['parallel']
    is_serial = not settings['parallel']
    browsers = settings["browser_types"]
    grid_url = settings["hub"]
    if is_parallel:
        run_tests_for_browser_parallel(browsers, all_test_groups)
    elif is_serial:
        run_tests_for_browser_serial(browsers, all_test_groups)
