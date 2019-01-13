"""Experimental behavioral test api for dash apps."""
import pytest
from ruamel import yaml

from pytest_dash.application_runners import DashSubprocess


class DashBehaviorTestFile(pytest.File):
    """A yaml test file definition"""
    def __init__(self, fspath, parent, plugin):
        super(DashBehaviorTestFile, self).__init__(fspath, parent)
        self.plugin = plugin

    def collect(self):
        raw = yaml.safe_load(self.fspath.open())
        tests = raw.pop('Tests')
        if not tests:
            raise Exception('No tests definition for the file in')

        for test in tests:
            if isinstance(test, str):
                yield DashBehaviorTestItem(
                    self.plugin.driver, test, self, raw.get(test)
                )
            else:
                behavior_name = list(test.keys())[0]
                behavior = raw.get(behavior_name)
                kwargs = test[behavior_name]
                test_name = behavior_name + '-' + '-'.join(
                    '[{}={}]'.format(k, v) for k, v in kwargs.items()
                )

                yield DashBehaviorTestItem(
                    self.plugin.driver, test_name, self, behavior, **kwargs
                )


class DashBehaviorTestItem(pytest.Item):
    """A single test of a test file."""

    def __init__(self, driver, name, parent, spec, **kwargs):
        super(DashBehaviorTestItem, self).__init__(name, parent)
        self.driver = driver
        self.spec = spec
        self.parameters = kwargs

    # pylint: disable=missing-docstring
    def runtest(self):
        application = self.spec.get('application', {})
        app_path = application.get('path')
        app_options = application.get('options', {})
        app_port = app_options.get('port', 8051)
        events = self.spec.get('event')

        with DashSubprocess(self.driver) as starter:
            starter(app_path, port=app_port)
            for e in events:
                self.execute_event(e)

    # pylint: disable=missing-docstring
    def reportinfo(self):
        return self.fspath, 0, "usecase: %s" % self.name

    def execute_event(self, event):
        print(event)
