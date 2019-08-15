# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import os
import sys
import unittest
import imp
import mock
import shutil
import xbmcaddon

cwd = os.path.dirname(os.path.abspath(__file__))

addon_name = 'plugin.video.ntv.ru'
sm_name = 'script.module.simplemedia'

temp_dir = os.path.join(cwd, 'addon_data')

if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

sm_dir = os.path.join(cwd, sm_name)
sm_config_dir = os.path.join(temp_dir, sm_name)
xbmcaddon.init_addon(sm_dir, sm_config_dir)

addon_dir = os.path.join(cwd, addon_name)
addon_config_dir = os.path.join(temp_dir, addon_name)
xbmcaddon.init_addon(addon_dir, addon_config_dir, True)

default_script = os.path.join(addon_dir, 'default.py')
run_script = lambda : imp.load_source('__main__', default_script)


# Import our module being tested
sys.path.append(addon_dir)


def tearDownModule():

    print('Removing temporary directory: {0}'.format(temp_dir))
    shutil.rmtree(temp_dir, True)


class PluginActionsTestCase(unittest.TestCase):

    def setUp(self):

        print("Running test: {0}".format(self.id().split('.')[-1]))

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/'.format(addon_name), '1', ''])
    def test_01_root():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/genre/Сериалы'.format(addon_name), '2', ''])
    def test_02_genre():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/seasons/Beregovaya_ohrana'.format(addon_name), '3', ''])
    def test_03_seasons():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/episodes/Beregovaya_ohrana/69020'.format(addon_name), '4', ''])
    def test_04_episodes():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/video/829700'.format(addon_name), '5', ''])
    def test_05_video():

        run_script()



if __name__ == '__main__':
    unittest.main()
