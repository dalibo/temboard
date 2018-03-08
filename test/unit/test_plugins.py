from __future__ import unicode_literals

import pytest


def test_fetch_plugins(mocker):
    iter_ep = mocker.patch('temboardagent.pluginsmgmt.iter_entry_points')
    from temboardagent.pluginsmgmt import PluginManager

    manager = PluginManager(mocker.Mock(name='config'))
    manager.config.temboard.plugins = ['myplugin']
    manager.config.plugins = dict()
    iter_ep.return_value = [mocker.Mock(name='found', ep='found')]

    eps = list(manager.fetch_plugins())

    assert 1 == len(eps)
    assert 'found' == eps[0].ep


def test_fetch_plugins_legacy(mocker):
    iter_ep = mocker.patch('temboardagent.pluginsmgmt.iter_entry_points')
    from temboardagent.pluginsmgmt import PluginManager

    manager = PluginManager(mocker.Mock(name='config'))
    manager.config.temboard.plugins = ['legacy']
    manager.config.plugins = dict(legacy=None)
    iter_ep.side_effect = Exception('not called')

    assert not list(manager.fetch_plugins())


def test_fetch_missing(mocker):
    iter_ep = mocker.patch('temboardagent.pluginsmgmt.iter_entry_points')
    from temboardagent.pluginsmgmt import PluginManager, ConfigurationError

    manager = PluginManager(mocker.Mock(name='config'))
    manager.config.temboard.plugins = ['myplugin']
    manager.config.plugins = dict()
    iter_ep.return_value = []

    with pytest.raises(ConfigurationError):
        list(manager.fetch_plugins())


def test_load_plugins(mocker):
    from temboardagent.pluginsmgmt import PluginManager, ConfigurationError

    manager = PluginManager()
    ep = mocker.Mock()
    ep.name = 'myplugin'
    manager.load_plugins([ep])
    assert 'myplugin' in manager.plugins

    manager = PluginManager()
    ep = mocker.Mock()
    ep.load.side_effect = Exception('fail to load')
    with pytest.raises(ConfigurationError):
        manager.load_plugins([ep])
    assert not manager.plugins
