# coding: utf-8
# Module: tests

from __future__ import print_function, unicode_literals
import os
import sys
import unittest
import imp
import mock
import shutil
import xbmcaddon
import xbmc

addon_name = 'plugin.video.ntv.ru'

cwd = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(cwd, 'config')
addon_dir = os.path.join(cwd, addon_name)

xbmcaddon.init_addon(addon_dir, config_dir, True)

xbmc._set_log_level(-1)

default_script = os.path.join(addon_dir, 'default.py')

# Import our module being tested
sys.path.append(addon_dir)


def tearDownModule():
    shutil.rmtree(config_dir, True)


class PluginActionsTestCase(unittest.TestCase):

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/'.format(addon_name), '1', ''])
    def test_01_root():
        print('# test_root')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/genre/%D0%A1%D0%B5%D1%80%D0%B8%D0%B0%D0%BB%D1%8B'.format(addon_name), '2', ''])
    def test_02_genre():
        print('# test_genre')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/seasons/Beregovaya_ohrana'.format(addon_name), '3', ''])
    def test_03_seasons():
        print('# test_seasons')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/episodes/Beregovaya_ohrana/69020'.format(addon_name), '4', ''])
    def test_04_episodes():
        print('# test_episodes')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/video/829700'.format(addon_name), '5', ''])
    def test_04_video():
        print('# test_video')
        imp.load_source('__main__', default_script)


if __name__ == '__main__':
    unittest.main()
