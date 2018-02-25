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
            archive = data['archive']
            
            for issue in archive['issues']:
                issues.append(issue)
            
            if len(issues)+1 < archive['issue_count']:
                u_params['offset'] += u_params['limit']
            else:
                break

        result = {'count': archive['issue_count'],
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
            for video in issue['video_list']:
                yield NTV._video_item(issue, video)

    @staticmethod
    def _video_item(issue, video):
        if video['comScore'].get('ns_st_en') is not None \
          and video['comScore']['ns_st_en'] !="*null" :
            episode = video['comScore']['ns_st_en'] 
        else:
            episode = ''

        if video['comScore'].get('ns_st_sn') is not None\
          and video['comScore']['ns_st_sn'] !="*null" :
            season = video['comScore']['ns_st_sn'] 
        else:
            season = ''
            
        item = {'program_title': issue.get('program_title', ''),
                'title': issue.get('title', ''),
                'description': issue.get('txt', ''),
                'rating': NTV._get_rating(video['r']),
                'allowed': video['allowed'],
                'img': video['img'],
                'id': video['id'],
                'episode': episode,
                'season': season,
                #'genre': video['comScore']['ns_st_ge'],
                #'date': video['comScore']['ns_st_ddt'],
                }
        return item

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

    def search( self, params ):

        keyword = params['keyword'].replace('-', ' ')
        keyword = keyword.replace('+', ' ')
        keyword = keyword.replace('\\', ' ')
        keyword = keyword.replace('/', ' ')
        keyword = keyword.replace('!', '')
        keyword = keyword.replace('#', '')
        keyword = keyword.replace('№', '')

        u_params = {'hasFullVideos': 'true',
                    'offset':    params.get('offset', 0),
                    'limit':  params.get('limit', self.default_limit),
                    'sort': params.get('sort', 'date'),
                    'search': keyword,
                    }

        r = self._http_request('search', u_params)
        json = self._extract_json(r)

        result = {'count': len(json['data']),
                  'pages': json['pagination']['pages'],
                  'list':  self._make_search_list(json, params)}
        return result

    def _make_video_list( self, json ):

        for item in json['data']:
            yield self._get_item_info(item)

    def _make_search_list( self, json, params ):
        full_list = params.get('full_list', True)
        keyword = params['keyword']
        
        for item in json['data']:
            if not full_list \
              and not self._video_have_keyword(item, keyword):
                continue
            
            yield self._get_item_info(item)

    def _get_item_info(self, brand, video=None, date_episode=0):
        if video is not None:
            mediatype = 'episode'
        else:
            mediatype = 'tvshow' if (brand['countFullVideos'] > 1) else 'movie'

        #Titles
        brand_title = self._get_title(brand['title'])
        brand_title_orig = self._get_title(brand.get('titleOrig')) if brand.get('titleOrig') else brand_title

        year = brand['productionYearStart']
        mpaa = self._get_mpaa(brand['ageRestrictions'])
        
        country = []
        for _country in brand['countries']:
            country.append(_country['title'])
        
        body = self._parse_body(brand['body'])

        if mediatype in ['tvshow', 'movie']:
            
            date = '%s.%s.%s' % (brand['dateRec'][0:2], brand['dateRec'][3:5], brand['dateRec'][6:10])
            
            picture = brand['pictures'][random.randint(0, len(brand['pictures'])-1)]
            banner = self._get_image(picture, u'prm')
            poster = self._get_image(picture, u'bq')
    
            picture = brand['pictures'][random.randint(0, len(brand['pictures'])-1)]
            thumb = self._get_image(picture, u'hdr')
            fanart = thumb

            tags = []
            for _tag in brand['tags']:
                tags.append(_tag['title'])

            video_info = {'type': mediatype,
                          'brand_id': brand['id'],
                          'sort': brand['sortBy'],
                          'count': brand['countFullVideos'],
                          'title': brand_title,
                          'have_trailer': brand['countVideos'] > brand['countFullVideos'],
                          'originaltitle': brand_title_orig,
                          }
    
            item_info = {'label': brand_title,
                         'cast': body.get('cast', []),
                         'info': {'video': {'date': date,
                                            'country': country,
                                            'year': year,
                                            'title': brand_title,
                                            'originaltitle': brand_title_orig,
                                            'sorttitle': brand_title,
                                            'plotoutline': brand['anons'],
                                            'plot': body['plot'],
                                            'mpaa': mpaa,
                                            'director': body.get('director', []),
                                            'writer': body.get('writer', []),
                                            'credits': body.get('credits', []),
                                            'mediatype': mediatype,
                                            'tag': tags,
                                            }
                                  },
                         'art': {'poster': poster,
                                 'banner': banner
                                 },
                         'fanart': fanart,
                         'thumb':  thumb,
                         'content_lookup': False,
                         }
        elif mediatype == 'episode':
    
            #Defaults
            poster = self._get_image(video['pictures'], u'bq')
            thumb = self._get_image(video['pictures'], u'hdr')
            fanart = thumb
    
            episode_title = self._get_title(video['episodeTitle'])
    
            #Date
            date = '%s.%s.%s' % (video['dateRec'][0:2], video['dateRec'][3:5], video['dateRec'][6:10])
            aired = '%s-%s-%s' % (video['dateRec'][6:10], video['dateRec'][3:5], video['dateRec'][0:2])
    
            episode = video['series'] if video['series'] != 0 else date_episode
            season = self._get_season(brand['title'])
    
            tags = []
            for _tag in video['tags']:
                tags.append(_tag['title'])

            video_info = {'type': mediatype,
                          'brand_id': video['brandId'],
                          'episode': episode,
                          'season': season,
                          'video_id': video['id'],
                          'title': brand_title,
                          'originaltitle': brand_title_orig,
                          }
    
            if episode == 0:
                season = 0
    
            item_info = {'cast': body.get('cast', []),
                         'info': {'video': {'date': date,
                                            'country': country,
                                            'year': year,
                                            'sortepisode': episode,
                                            'sortseason': season,
                                            'director': body.get('director', []),
                                            'season': season,
                                            'episode': episode,
                                            'tvshowtitle': brand_title,
                                            'plot': video['anons'],
                                            'mpaa': mpaa,
                                            'title': episode_title,
                                            'sorttitle': episode_title,
                                            'duration': video['duration'],
                                            'writer': body.get('writer', []),
                                            'aired': aired,
                                            'mediatype': mediatype,
                                            'tag': tags,
                                            }
                                  },
                         'art': {'poster': poster},
                         'fanart': fanart,
                         'thumb':  thumb,
                         'content_lookup': False,
                        }
            
        video_info = {'item_info':  item_info,
                      'video_info': video_info
                      }

        return video_info

    def get_trailer_url( self, params ):

        brand_info = self._get_brand_data(params)

        url_params = {'#brand_id': str(params['brand_id'])}
        
        for item_type in [3, 2]:
            u_params = {'limit': brand_info['countVideos'],
                        'type': item_type,
                        }
    
            r = self._http_request('videos', u_params, url_params=url_params)
            json = self._extract_json(r)
            if json['data']:
                while json['data']:
                    video = json['data'][random.randint(0, len(json['data'])-1)]
                    if video['series'] == 0 \
                      and video['duration'] <= 600:
                        return self._get_video_url(video)
                    else:
                        json['data'].remove(video)
        
        raise NTVApiError('Trailer not found')


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

    def _video_have_keyword(self, item, keyword):
        title = self._get_title(item['title'])
        originaltitle = self._get_title(item.get('titleOrig')) if item.get('titleOrig') else title

        kw = keyword.decode('utf-8').lower()
    
        result = (title.decode('utf-8').lower().find(kw) >= 0 or originaltitle.decode('utf-8').lower().find(kw) >= 0)
    
        return result

if __name__ == '__main__':
    ntv = NTV()
    genres = ntv.get_genres()
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
                    video_info = ntv.get_video_info(episode['id'])
                    print(video_info['video'])