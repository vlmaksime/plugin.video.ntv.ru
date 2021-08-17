# -*- coding: utf-8 -*-
# Module: default
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals
import time

import xbmc
import xbmcgui
import xbmcplugin

import resources.lib.ntv as ntv
import simplemedia

# Create plugin instance
plugin = simplemedia.RoutedPlugin()
_ = plugin.initialize_gettext()

use_subtitles = plugin.get_setting('use_subtitles')


def _init_api():

    settings = {'cache_dir': plugin.profile_dir}

    return ntv.NTV(settings)


def _show_api_error(err):
    plugin.log_error(err)
    try:
        text = _(str(err))
    except simplemedia.SimplePluginError:
        text = str(err)

    xbmcgui.Dialog().notification(plugin.addon.getAddonInfo('name'), text, xbmcgui.NOTIFICATION_ERROR)


def _show_notification(text):
    xbmcgui.Dialog().notification(plugin.addon.getAddonInfo('name'), text)


@plugin.route('/')
def root():
    plugin.create_directory(_list_root())


def _list_root():

    try:
        genres = _get_genres()
    except ntv.NTVApiError as err:
        _show_api_error(err)
        genres = []

#     url = plugin.url_for('play_live')
#     list_item = {'label': _('Live'),
#                  'url': url,
#                  'icon': plugin.icon,
#                  'fanart': plugin.fanart,
#                  'content_lookup': False,
#                  'is_folder': False,
#                  'is_playable': False,
#                  }
#     yield list_item
    
    for genre in genres:
        url = plugin.url_for('genre', genre_title=genre['title'])
        list_item = {'label': genre['title'],
                     'url': url,
                     'icon': plugin.icon,
                     'fanart': plugin.fanart,
                     'content_lookup': False,
                     }
        yield list_item

#     url = plugin.url_for('search')
#     list_item = {'label': _('Search'),
#                  'url': url,
#                  'icon': plugin.icon,
#                  'fanart': plugin.fanart,
#                  'content_lookup': False,
#                  }
#    yield list_item


@plugin.route('/genre/<genre_title>')
def genre(genre_title):

    offset = plugin.params.offset or '0'
    limit = plugin.params.limit or plugin.get_setting('limit', False)

    params = {'offset': int(offset),
              'limit': int(limit),
              }
    update_listing = (params['offset'] > 0)
    genre_id = _get_genre_id(genre_title)
    
    programs_info = _api.browse_programs(genre_id, params)

    plugin.create_directory(_list_programs(programs_info, genre_title), content='movies', category=programs_info['title'], update_listing=update_listing)


def _list_programs(data, genre_title):

    mediatype = 'tvshow'
    for program in data['list']:
        url = plugin.url_for('program_seasons', prog_id=program['shortcat'])

        list_item = {'label': program['title'],
                     'info': {'video': {  # 'date': date,
                                        # 'country': country,
                                        # 'year': year,
                                        'title': program['title'],
                                        'originaltitle': program['title'],
                                        'sorttitle': program['title'],
                                        'plotoutline': program['annotation'],
                                        'plot': program['annotation'],
                                        'mpaa': program['rating']['mpaa'],
                                        # 'director': body.get('director', []),
                                        # 'writer': body.get('writer', []),
                                        # 'credits': body.get('credits', []),
                                        'mediatype': mediatype,
                                        }
                              },
                     'art': {'poster': program['img'],
                             },
                     'fanart': plugin.fanart,
                     'thumb':  program['img'],
                     'content_lookup': False,
                     'is_folder': True,
                     'url': url,
                     }
        yield list_item

    if data['offset'] > 0:
        params = {'limit': data['limit']}
        prev_offset = data['offset'] - data['limit']
        if prev_offset > 0:
            params['offset'] = prev_offset
        url = plugin.url_for('genre', genre_title=genre_title, **params)
        item_info = {'label': _('Previous page...'),
                     'url':   url}
        yield item_info

    if (data['offset'] + data['limit']) < data['total']:
        params = {'limit': data['limit'],
                  'offset': data['offset'] + data['limit']}
        url = plugin.url_for('genre', genre_title=genre_title, **params)
        item_info = {'label': _('Next page...'),
                     'url':   url}
        yield item_info


@plugin.route('/seasons/<prog_id>')
def program_seasons(prog_id):

    seasons_info = _api.browse_seasons(prog_id)

#    if seasons_info['count'] == 1:
#        for season in seasons_info['list']:
#            url = plugin.url_for('program_episodes', prog_id=seasons_info['shortcat'], archive_id=season['id'])
#            plugin.create_directory([], succeeded=False)
#            xbmc.executebuiltin('Container.Update("%s")' % url)
#            return
            
    plugin.create_directory(_list_seasons(seasons_info), content='seasons', category=seasons_info['title'])


def _list_seasons(data):
    mediatype = 'season'
    for season in data['list']:
        url = plugin.url_for('program_episodes', prog_id=data['shortcat'], archive_id=season['id'])

        list_item = {'label': season['title'],
                     'info': {'video': {  # 'date': date,
                                        # 'country': country,
                                        # 'year': year,
                                        'title': season['title'],
                                        'originaltitle': season['title'],
                                        'sorttitle': season['title'],
                                        'plotoutline': data['annotation'],
                                        'plot': data['description'],
                                        'mpaa': data['rating']['mpaa'],
                                        # 'director': body.get('director', []),
                                        # 'writer': body.get('writer', []),
                                        # 'credits': body.get('credits', []),
                                        'mediatype': mediatype,
                                        }
                              },
                     'art': {'poster': data['img'],
                             },
                     'fanart': plugin.fanart,
                     'thumb':  data['img'],
                     'content_lookup': False,
                     'is_folder': True,
                     'url': url,
                     }
        yield list_item

    
@plugin.mem_cached(180)
def _get_genres():
    result = []
    for genre in _api.get_genres():
        result.append(genre)

    return result

    
@plugin.mem_cached(180)
def _get_genre_id(genre_title):
    for genre in _get_genres():
        if genre['title'] == genre_title:
            return genre['id']


@plugin.route('/episodes/<prog_id>/<archive_id>')
def program_episodes(prog_id, archive_id):

    episodes_info = _api.browse_episodes(prog_id, archive_id)

    plugin.create_directory(_list_episodes(episodes_info), content='episodes', category=episodes_info['title'],
                     total_items=episodes_info['count'], sort_methods=_get_sort_methods('episodes', 'date'))


def _list_episodes(data):
    mediatype = 'episode'
    for episode in data['list']:
        
        list_item = _get_item(data, episode)
        yield list_item


def _get_item(data, episode):
    mediatype = 'episode'
    url = plugin.url_for('play_video', video_id=episode['id'])

    st_time = time.gmtime(episode['timestamp'])     
    list_item = {'label': episode['title'],
                 'info': {'video': {'date': time.strftime('%d.%m.%Y', st_time),
                                    # 'country': country,
                                    'year': st_time[0],
                                    'season': episode['season'],
                                    'sortseason': episode['season'],
                                    'episode': episode['episode'],
                                    'sortepisode': episode['episode'],
                                    'title': episode['title'],
                                    'originaltitle': episode['title'],
                                    'tvshowtitle': episode['program_title'],
                                    'sorttitle': episode['title'],
                                    'plotoutline': data.get('annotation', ''),
                                    'plot': episode['description'],
                                    'mpaa': episode['rating']['mpaa'],
                                    'duration': episode['duration'],
                                    'premiered': time.strftime('%Y-%m-%d', st_time),
                                    'dateadded': time.strftime('%Y-%m-%d %H:%M:%S', st_time),
                                    # 'writer': body.get('writer', []),
                                    # 'credits': body.get('credits', []),
                                    'mediatype': mediatype,
                                    }
                          },
                 'art': {'poster': episode['img'],
                         },
                 'fanart': plugin.fanart,
                 'thumb':  episode['img'],
                 'content_lookup': False,
                 'is_folder': False,
                 'is_playable': True,
                 'url': url,
                 'path': url,
                 }

    if use_subtitles \
      and episode['subtitles'] is not None:
        list_item['subtitles'] = [episode['subtitles']]

    return list_item

    
@plugin.route('/video/<video_id>')
def play_video(video_id):
    video_info = _api.get_video_info(video_id)
    list_item = _get_item(video_info, video_info['item']) 
    list_item['path'] = _get_video_path(video_info)
    plugin.resolve_url(list_item)

    
@plugin.route('/live')
def play_live():
    live_info = _api.get_live_info()
    xbmc.executebuiltin('PlayMedia({})'.format(live_info['hls']))

    
@plugin.route('/search')
def search():
    pass


def _get_video_path(data):

    video_quality = plugin.get_setting('video_quality')
    
    path = ''
    if (not path or video_quality >= 0) and data['video']:
        path = data['video']
    if (not path or video_quality >= 1) and data['hi_video']:
        path = data['hi_video']

    return path


def _get_sort_methods(cat, sort=''):
    sort_methods = []

    if cat == 'episodes' \
      and not plugin.get_setting("use_atl_names"):
        if sort == 'date':
            sort_methods.append(xbmcplugin.SORT_METHOD_DATEADDED)
        else:
            sort_methods.append(xbmcplugin.SORT_METHOD_EPISODE)
    elif cat == 'search':
        sort_methods.append({'sortMethod': xbmcplugin.SORT_METHOD_UNSORTED, 'label2Mask': '%Y'})
        sort_methods.append(xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        sort_methods.append({'sortMethod': xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE, 'label2Mask': '%Y'})
    elif cat == 'category':
        sort_methods.append({'sortMethod': xbmcplugin.SORT_METHOD_UNSORTED, 'label2Mask': '%Y'})
    else:
        sort_methods.append(xbmcplugin.SORT_METHOD_UNSORTED)

    return sort_methods


def _get_image(image):
    return image if xbmc.skinHasImage(image) else plugin.icon


if __name__ == '__main__':
    _api = _init_api()
    plugin.run()
