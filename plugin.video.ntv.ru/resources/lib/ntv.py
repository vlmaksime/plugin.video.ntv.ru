# -*- coding: utf-8 -*-
# Module: ntv
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import requests
import urllib
import re
import random

from future.utils import PY3, iteritems

if PY3:
    basestring = str

class NTVApiError(Exception):
    """Custom exception"""
    pass

class NTV(object):

    def __init__(self, params=None):
        params = params or {}

        api_url = 'http://www.ntv.ru/m/v10'

        self._actions = {'main': api_url + '/pr',
                         'program': api_url + '/prog/#prog_id',
                         'video': api_url + '/v/#video_id',
                         'archive': api_url + '/prog/#prog_id/archive/#archive_id',
                         }

        self._headers = {'User-Agent': 'ru.ntv.client_4.5.1',
                         'Accept-Encoding': 'gzip',
                         'Connection': 'keep-alive',
                         }

    def _http_request( self, action, params=None, url_params=None ):
        params = params or {}

        action_settings = self._actions.get(action)
        
        if isinstance(action_settings, dict):
            url = action_settings['url']
        else:
            url = action_settings

        if url_params is not None:
            for key, val in iteritems(url_params):
                url = url.replace('#{0}'.format(key), str(val))

        try:
            r = requests.get(url, params=params, headers=self._headers)
            r.raise_for_status()
        except requests.ConnectionError:
            raise NTVApiError('Connection error')

        return r

    @staticmethod
    def _extract_json(r):
        try:
            json = r.json()
        except ValueError as err:
            raise NTVApiError(err)

        return json

    @staticmethod
    def _get_menu(data, menu_type):
        menus = data['menus']
        
        result = []
        for menu in menus:
            if menu['type'] == menu_type:
                result.append(menu['data'])
        
        return result

    def get_genres( self ):
        r = self._http_request('main')

        json = self._extract_json(r)

        for index, genre in enumerate(json['data']['genres']):
            item = {'title': genre['title'],
                    'id': index,
                    }

            yield(item)

    def browse_programs( self, genre_id, params=None ):
        params = params or {}

        offset = int(params.get('offset', '0'))
        limit = int(params.get('limit', '10'))

        if isinstance(genre_id, basestring):
            genre_id = int(genre_id)

        r = self._http_request('main')

        json = self._extract_json(r)

        genre = json['data']['genres'][genre_id]
        
        result = {'count': min(limit, len(genre['programs']) - offset),
                  'total': len(genre['programs']),
                  'offset': offset,
                  'limit': limit,
                  'title': genre['title'],
                  'list': self._programs_list(genre['programs'], offset, limit),
                  }
        return result

    @staticmethod
    def _programs_list(programs, offset, limit):
        for program in programs[offset:(offset + limit)]:
            item = {'annotation': program['annotation'],
                    'id': program['id'],
                    'img': program['img'],
                    'shortcat': program['shortcat'],
                    'rating': NTV._get_rating(program['r']),
                    'title': program['title'],
                    }
            yield(item)

    def browse_seasons( self, prog_id ):

        url_params = {'prog_id': prog_id}

        r = self._http_request('program', url_params=url_params)
        json = self._extract_json(r)

        data = json['data']

        abouts = self._get_menu(data, 'about')
        if abouts:
            description = abouts[0]['txt']
        else:
            description = ''
        
        archives = self._get_menu(data, 'archive')
        
        result = {'count': len(archives),
                  'title': data['title'],
                  'type': data['type'],
                  'shortcat': data['shortcat'],
                  'rating': self._get_rating(data['r']),
                  'annotation': data['annotation'],
                  'description': description,
                  'img': data['preview'],
                  'list': self._season_list(archives)
                  }

        return result
    
    @staticmethod
    def _season_list(archives):
        for archive in archives:
            item = {'title': archive['title'],
                    'id': archive['id'],
                    }
            yield item

    def browse_episodes( self, prog_id, archive_id ):

        issues = []

        url_params = {'prog_id': prog_id,
                      'archive_id': archive_id}

        u_params = {'limit': 100, 'offset': 1}
        
        while True:
            r = self._http_request('archive', u_params, url_params)
            json = self._extract_json(r)
    
            data = json['data']
            archive = data.get('archive')
            if archive is None:
                break

            issue_count = archive['issue_count']
            
            for issue in archive['issues']:
                issues.append(issue)
            
            u_params['offset'] += u_params['limit']
            
            if issue_count < u_params['offset']:
                break 

        issues.sort(key=NTV._sort_by_ts)

        result = {'count': issue_count,
                  'title': data['title'],
                  'type': data['type'],
                  'shortcat': data['shortcat'],
                  'rating': self._get_rating(data['r']),
                  'annotation': data['annotation'],
                  'list': self._episode_list(issues)
                  }

        return result

    @staticmethod
    def _episode_list(issues):

        for issue in issues:
            if len(issue['video_list']) == 1:
                video = issue['video_list'][0]
                yield NTV._video_item(issue, video)
            else:
                for part, video in enumerate(issue['video_list']):
                    yield NTV._video_item(issue, video, part+1)

    @staticmethod
    def _video_item(issue, video, part=None):

        item = {'program_title': issue.get('program_title', ''),
                'title': issue.get('title', ''),
                'description': issue.get('txt', ''),
                'rating': NTV._get_rating(video['r']),
                'allowed': video['allowed'],
                'img': video['img'],
                'id': video['id'],
                'timestamp': float(video['ts'])/1000
                ,
                'duration': video['tt'],
                'subtitles': video.get('subtitles'),
                'episode': NTV._comScore_val(video['comScore'], 'ns_st_en'),
                'season': NTV._comScore_val(video['comScore'], 'ns_st_sn'),
                'genre': NTV._comScore_val(video['comScore'], 'ns_st_ge'),
                'part': part,
                #'date': video['comScore']['ns_st_ddt'],
                }
        return item

    @staticmethod
    def _sort_by_ts(item):
        return item['ts']

    @staticmethod
    def _comScore_val(data, key):
        data = data or {}
        
        if data.get(key) is not None \
          and data[key] !="*null" :
            value = data[key] 
        else:
            value = None
        
        return value

    def get_video_info(self, video_id):

        url_params = {'video_id': video_id}

        r = self._http_request('video', url_params=url_params)
        json = self._extract_json(r)

        info = json['info']
        if info['linked_entities'].get('linked_issues') is not None:
            issue = info['linked_entities']['linked_issues'][0]
        else:
            issue = {}
        result = {'item': NTV._video_item(issue, info),
                  'video': info['video'],
                  'hi_video': info.get('hi_video',''),
            }
        return result
        
    def _get_season(self, title):
        parts = title.split('-')
        if parts[-1].isdigit():
            result = int(parts[-1])
        else:
            result = 1
        return result

    @staticmethod
    def _get_rating(rating):
        rars = rating['v']
        if rating['k'] <= 0:
            mpaa = 'G'
            rars = '0+'
        elif rating['k'] == 1:
            mpaa = 'PG'
        elif rating['k'] == 2:
            mpaa = 'PG-13'
        elif rating['k'] == 3:
            mpaa = 'R'
        elif rating['k'] == 4:
            mpaa = 'NC-17'
        else:
            mpaa = ''
        
        result = {'rars': rars,
                  'mpaa': mpaa,
                  }
        
        return result

if __name__ == '__main__':
    import time
    ntv = NTV()
    genres = ntv.get_genres()
    #genres = [{'id':10, 'title': 'Auto'}]
    for genre in genres:
        print('id-{0}, title-{1}'.format(genre['id'], genre['title']))
        programs_info = ntv.browse_programs(genre['id'], {'limit': 1})
        for program in programs_info['list']:
            print('{0} {1}'.format(program['title'], program['rating']['rars']))
            seasons_info = ntv.browse_seasons(program['shortcat'])
            for season in seasons_info['list']:
                print(season['title'])
                episodes_info = ntv.browse_episodes(program['shortcat'], season['id'])
                for episode in episodes_info['list']:
                    print(episode['title'])
                    print(episode['timestamp'])
                    st_time = time.gmtime(float(episode['timestamp']))     
                    print(time.strftime('%Y-%m-%d', st_time))
#                    video_info = ntv.get_video_info(episode['id'])
#                    print(video_info['video'])