import random
import unittest
from Utils import users
from infra.infra_ui.browser_wrapper import WebDriverManager
from logic.logic_ui.login_page import LoginPage
from logic.logic_ui.Epics_page import EpicsPage
from logic.logic_ui.Home_page import HomePage
from Utils import generate_string
from infra.infra_jira.jira_wrapper import JiraWrapper
from parameterized import parameterized_class
from Utils.configurations import ConfigurationManager
from Utils.error_handling import test_decorator

config_manager = ConfigurationManager()
settings = config_manager.load_settings()
browser_types = [(browser,) for browser in settings["browser_types"]]


@parameterized_class(('browser',), browser_types)
class ParallelEpicsTests(unittest.TestCase):
    VALID_USERS = users.authentic_users

    def setUp(self):
        self.browser_wrapper = WebDriverManager()
        default_browser = 'chrome'
        self.browser = getattr(self.__class__, 'browser', default_browser)
        self.driver = self.browser_wrapper.initialize_web_driver(browser_name=self.browser)
        self.login_page = LoginPage(self.driver)
        user = self.VALID_USERS[0]
        self.login_page.login(user['email'], user['password'])
        self.epics_Page = EpicsPage(self.driver)
        self.home_page = HomePage(self.driver)
        self.home_page.changeEnvironment(environment_name="dev")
        self.jira_client = JiraWrapper()
        self.test_failed = False
        self.error_msg = ""

    def test_bulk_epic_removal_by_name(self):
        unique_epic_name = generate_string.create_secure_string()
        random_number = random.randint(2, 5)
        for i in range(random_number):
            creationOutcome = self.epics_Page.add_new_epic(unique_epic_name)
            self.assertTrue(creationOutcome, "Failed to create a new epic")
        operationStatus = self.epics_Page.bulkDeleteEpics(unique_epic_name, "all")
        self.assertTrue(operationStatus, "Bulk deletion of epics by name failed")

    @test_decorator
    def test_create_and_remove_epic(self):
        epic_name = generate_string.create_secure_string()
        creationOutcome = self.epics_Page.add_new_epic(epic_name)  # Use a unique name to ensure the test is reliable
        self.assertTrue(creationOutcome, "Failed to create a new epic")
        deletionOutcome = self.epics_Page.bulkDeleteEpics(epic_name)
        self.assertTrue(deletionOutcome, "Failed to delete the epic")

    # def test_find_sprints_by_name(self):
    #     search_result = self.epics_Page.findTasksByName(name="New epic")
    #     self.assertTrue(search_result, "Failed to find the specified epic")

    def tearDown(self):
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
