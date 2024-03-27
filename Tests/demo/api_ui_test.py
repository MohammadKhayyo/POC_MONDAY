import unittest
import pytest
from Utils import users
from infra.infra_ui.browser_wrapper import WebDriverManager
from logic.logic_ui.login_page import LoginPage
from logic.logic_api.work_space import WorkSpace
from logic.logic_api.board import Board
from logic.logic_ui.Home_page import HomePage
from infra.infra_api.api_wrapper import MondayApi
from logic.logic_api.column import Column
from logic.logic_api.item import Item
from logic.logic_api.group import Group
from parameterized import parameterized_class
from Utils.configurations import ConfigurationManager
from Utils import generate_string
from Utils.error_handling import test_decorator
from Utils.read_file import read_file
from infra.infra_jira.jira_wrapper import JiraWrapper

config_manager = ConfigurationManager()
settings = config_manager.load_settings()
browser_types = [(browser,) for browser in settings["browser_types"]]


@pytest.mark.serial
@parameterized_class(('browser',), browser_types)
class AddBoardTests(unittest.TestCase):
    VALID_USERS = users.authentic_user

    def setUp(self):
        self.browser_wrapper = WebDriverManager()
        default_browser = 'chrome'
        self.browser = getattr(self.__class__, 'browser', default_browser)
        self.driver = self.browser_wrapper.initialize_web_driver(browser_name=self.browser)
        self.login_page = LoginPage(self.driver)
        user = self.VALID_USERS[0]
        self.login_page.login(user['email'], user['password'])
        self.home_page = HomePage(self.driver)
        self.home_page.changeEnvironment(environment_name="dev")
        self.send_request = MondayApi()
        self.work_space_name = "MY_TEAM"
        self.board_name = generate_string.create_secure_string()
        self.folder_name = "My Team"
        self.group_name = generate_string.create_secure_string()
        self.work_space = WorkSpace(work_space_name=self.work_space_name)
        self.board = Board(work_space=self.work_space, board_name=self.board_name, folder_name=self.folder_name,
                           exists=False)
        self.group = Group(board=self.board, group_name=self.group_name, exist=False)
        self.jira_client = JiraWrapper()
        self.test_failed = False
        self.error_msg = ""

    @test_decorator
    def test_add_file(self):
        file_path = "file1.txt"
        data_column = {"title": "Attached Files", "column_type": "file", "description": "",
                       "files_paths": [file_path]}
        Column(board=self.board, title=data_column['title'], description=data_column['description'],
               column_type=data_column['column_type'])
        item_name = generate_string.create_secure_string()
        item = Item(group=self.group, item_name=item_name, exist=False)
        item.upload_files(column_title=data_column['title'], files_paths=data_column["files_paths"])
        self.home_page.switch_board(_name=self.board_name)
        text = self.home_page.click_Attached_Files(name_item=item.item_name)
        contents = read_file(file_path)
        self.assertEqual(text, contents)

    def tearDown(self):
        self.board.delete_board()
        if self.driver:
            self.driver.quit()
        if self.test_failed:
            self.test_name = self.id().split('.')[-1]
            summary = f"{self.test_name} "
            description = f"{self.error_msg} browser {self.browser}"
            try:
                issue_key = self.jira_client.create_issue(summery=summary, description=description,
                                                          issue_type='Bug', project_key='KP')
                print(f"Jira issue created: {issue_key}")
            except Exception as e:
                print(f"Failed to create Jira issue: {e}")
