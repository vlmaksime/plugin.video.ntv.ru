# -*- coding: utf-8 -*-
# Module: default
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals
from future.utils import iteritems

import xbmc
import xbmcgui
import xbmcplugin

from simpleplugin import RoutedPlugin, SimplePluginError

from resources.lib.ntv import *

# Create plugin instance
plugin = RoutedPlugin()
_ = plugin.initialize_gettext()

def _init_api():
    return NTV()

def _show_api_error(err):
    plugin.log_error(err)
    try:
        text = _(str(err))
    except SimplePluginError:
        text = str(err)

    xbmcgui.Dialog().notification(plugin.addon.getAddonInfo('name'), text, xbmcgui.NOTIFICATION_ERROR)

def _show_notification(text):
    xbmcgui.Dialog().notification(plugin.addon.getAddonInfo('name'), text)

@plugin.route('/')
def root():
    create_directory(_list_root())

def _list_root():

    try:
        genres = _get_genres()
    except NTVApiError as err:
        _show_api_errosr(err)
        genres = []

    for genre in genres:
        url = plugin.url_for('genre', genre_id=genre['id'])
        list_item = {'label': genre['title'],
                     'url': url,
                     'icon': plugin.icon,
                     'fanart': plugin.fanart,
                     'content_lookup': False,
                     }
        yield list_item

@plugin.route('/genre/<genre_id>')
def genre(genre_id):
    params = {'offset': plugin.params.offset or 0,
              'limit': plugin.params.limit or plugin.get_setting('limit'),
              }
    update_listing = (params['offset'] > 0)

    programs_info = _api.browse_programs(genre_id, params)

    create_directory(_list_programs(programs_info, genre_id), content='movies', category=programs_info['title'], update_listing=update_listing)

def _list_programs(data, genre_id):

    mediatype = 'tvshow'
    for program in data['list']:
        url = plugin.url_for('program_seasons', prog_id=program['shortcat'])

        list_item = {'label': program['title'],
                     'info': {'video': {#'date': date,
                                        #'country': country,
                                        #'year': year,
                                        'title': program['title'],
                                        'originaltitle': program['title'],
                                        'sorttitle': program['title'],
                                        'plotoutline': program['annotation'],
                                        'plot': program['annotation'],
                                        'mpaa': program['rating']['mpaa'],
                                        #'director': body.get('director', []),
                                        #'writer': body.get('writer', []),
                                        #'credits': body.get('credits', []),
                                        'mediatype': mediatype,
                                        }
                              },
                     'art': {'poster': program['img'],
                             },
                     'fanart': program['img'],
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
        url = plugin.url_for('genre', genre_id=genre_id, **params)
        item_info = {'label': _('Previous page...'),
                     'url':   url}
        yield item_info

    if (data['offset'] + data['limit']) < data['total']:
        params = {'limit': data['limit'],
                  'offset': data['offset'] + data['limit']}
        url = plugin.url_for('genre', genre_id=genre_id, **params)
        item_info = {'label': _('Next page...'),
                     'url':   url}
        yield item_info

@plugin.route('/seasons/<prog_id>')
def program_seasons(prog_id):

    seasons_info = _api.browse_seasons(prog_id)

    if seasons_info['count'] == 1:
        for season in seasons_info['list']:
            url = plugin.url_for('program_episodes', prog_id=seasons_info['shortcat'], archive_id=season['id'])
            xbmc.executebuiltin('Container.Update("%s")' % url)
            return
            
    create_directory(_list_seasons(seasons_info), content='seasons', category=seasons_info['title'])

def _list_seasons(data):
    mediatype = 'season'
    for season in data['list']:
        url = plugin.url_for('program_episodes', prog_id=data['shortcat'], archive_id=season['id'])

        list_item = {'label': season['title'],
                     'info': {'video': {#'date': date,
                                        #'country': country,
                                        #'year': year,
                                        'title': season['title'],
                                        'originaltitle': season['title'],
                                        'sorttitle': season['title'],
                                        'plotoutline': data['annotation'],
                                        'plot': data['description'],
                                        'mpaa': data['rating']['mpaa'],
                                        #'director': body.get('director', []),
                                        #'writer': body.get('writer', []),
                                        #'credits': body.get('credits', []),
                                        'mediatype': mediatype,
                                        }
                              },
                     'art': {'poster': data['img'],
                             },
                     'fanart': data['img'],
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

@plugin.route('/episodes/<prog_id>/<archive_id>')
def program_episodes(prog_id, archive_id):

    episodes_info = _api.browse_episodes(prog_id, archive_id)

    create_directory(_list_episodes(episodes_info), content='episodes', category=episodes_info['title'],
                     total_items=episodes_info['count'], sort_methods=_get_sort_methods('episodes'))

def _list_episodes(data):
    mediatype = 'episode'
    for episode in data['list']:
        url = plugin.url_for('play_video', video_id=episode['id'])

        list_item = {'label': episode['title'],
                     'info': {'video': {#'date': date,
                                        #'country': country,
                                        #'year': year,
                                        'season': episode['season'],
                                        'sortseason': episode['season'],
                                        'episode': episode['episode'],
                                        'sortepisode': episode['episode'],
                                        'title': episode['title'],
                                        'originaltitle': episode['title'],
                                        'tvshowtitle': episode['program_title'],
                                        'sorttitle': episode['title'],
                                        'plotoutline': data['annotation'],
                                        'plot': episode['description'],
                                        'mpaa': episode['rating']['mpaa'],
                                        #'director': body.get('director', []),
                                        #'writer': body.get('writer', []),
                                        #'credits': body.get('credits', []),
                                        'mediatype': mediatype,
                                        }
                              },
                     'art': {'poster': episode['img'],
                             },
                     'fanart': episode['img'],
                     'thumb':  episode['img'],
                     'content_lookup': False,
                     'is_folder': False,
                     'is_playable': True,
                     'url': url,
                     'path': url,
                     }
        yield list_item

def _get_item(data, episode):
    mediatype = 'episode'
    list_item = {'label': episode['title'],
                 'info': {'video': {#'date': date,
                                    #'country': country,
                                    #'year': year,
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
                                    #'director': body.get('director', []),
                                    #'writer': body.get('writer', []),
                                    #'credits': body.get('credits', []),
                                    'mediatype': mediatype,
                                    }
                          },
                 'art': {'poster': episode['img'],
                         },
                 'fanart': episode['img'],
                 'thumb':  episode['img'],
                 'content_lookup': False,
                 'is_folder': False,
                 'is_playable': True,
                 }
    return list_item
    
@plugin.route('/video/<video_id>')
def play_video(video_id):
    video_info = _api.get_video_info(video_id)
    list_item = _get_item(video_info, video_info['item']) 
    list_item['path'] = _get_video_path(video_info)
    resolve_url(list_item)

def _get_video_path(data):

    video_quality = plugin.get_setting('video_quality')
    
    path = ''
    if (not path or video_quality >= 0) and data['video']:
        path = data['video']
    if (not path or video_quality >= 1) and data['hi_video']:
        path = data['hi_video']

    return path

def _get_sort_methods( cat, sort='' ):
    sort_methods = []

    if cat == 'episodes' \
      and not plugin.get_setting("use_atl_names"):
        if sort == 'date':
            sort_methods.append(xbmcplugin.SORT_METHOD_DATE)
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

def create_list_item(item):
    major_version = xbmc.getInfoLabel('System.BuildVersion')[:2]
    if major_version >= '18':
        list_item = xbmcgui.ListItem(label=item.get('label', ''),
                                     label2=item.get('label2', ''),
                                     path=item.get('path', ''),
                                     offscreen=item.get('offscreen', False))
    else:
        list_item = xbmcgui.ListItem(label=item.get('label', ''),
                                     label2=item.get('label2', ''),
                                     path=item.get('path', ''))

    if major_version < '18':
        if item.get('info') \
          and item['info'].get('video'):
            for fields in ['genre', 'writer', 'director', 'country', 'credits']:
                if item['info']['video'].get(fields) \
                  and isinstance(item['info']['video'][fields], list):
                    item['info']['video'][fields] = ' / '.join(item['info']['video'][fields])
    if major_version < '15':
        if item['info']['video'].get('duration'):
            item['info']['video']['duration'] = (item['info']['video']['duration'] / 60)

    if major_version >= '16':
        art = item.get('art', {})
        art['thumb'] = item.get('thumb', '')
        art['icon'] = item.get('icon', '')
        art['fanart'] = item.get('fanart', '')
        item['art'] = art
        cont_look = item.get('content_lookup')
        if cont_look is not None:
            list_item.setContentLookup(cont_look)
    else:
        list_item.setThumbnailImage(item.get('thumb', ''))
        list_item.setIconImage(item.get('icon', ''))
        list_item.setProperty('fanart_image', item.get('fanart', ''))
    if item.get('art'):
        list_item.setArt(item['art'])
    if item.get('stream_info'):
        for stream, stream_info in iteritems(item['stream_info']):
            list_item.addStreamInfo(stream, stream_info)
    if item.get('info'):
        for media, info in iteritems(item['info']):
            list_item.setInfo(media, info)
    if item.get('context_menu') is not None:
        list_item.addContextMenuItems(item['context_menu'])
    if item.get('subtitles'):
        list_item.setSubtitles(item['subtitles'])
    if item.get('mime'):
        list_item.setMimeType(item['mime'])
    if item.get('properties'):
        for key, value in iteritems(item['properties']):
            list_item.setProperty(key, value)
    if major_version >= '17':
        cast = item.get('cast')
        if cast is not None:
            list_item.setCast(cast)
        db_ids = item.get('online_db_ids')
        if db_ids is not None:
            list_item.setUniqueIDs(db_ids)
        ratings = item.get('ratings')
        if ratings is not None:
            for rating in ratings:
                list_item.setRating(**rating)
    return list_item

def create_directory(items, content='files', succeeded=True, update_listing=False, category=None, sort_methods=None, cache_to_disk=False, total_items=0):
    xbmcplugin.setContent(plugin._handle, content)

    if category is not None:
        xbmcplugin.setPluginCategory(plugin._handle, category)
        
    if sort_methods is not None:
        if isinstance(sort_methods, int):
            xbmcplugin.addSortMethod(plugin._handle, sort_methods)
        elif isinstance(sort_methods, (tuple, list)):
            for method in sort_methods:
                xbmcplugin.addSortMethod(plugin._handle, method)
        else:
            raise TypeError(
                'sort_methods parameter must be of int, tuple or list type!')

    for item in items:
        is_folder = item.get('is_folder', True)
        list_item = create_list_item(item)
        if item.get('is_playable'):
            list_item.setProperty('IsPlayable', 'true')
            is_folder = False
        xbmcplugin.addDirectoryItem(plugin._handle, item['url'], list_item, is_folder, total_items)
    xbmcplugin.endOfDirectory(plugin._handle, succeeded, update_listing, cache_to_disk)

def resolve_url(item, succeeded=True):
    list_item = create_list_item(item)
    xbmcplugin.setResolvedUrl(plugin._handle, succeeded, list_item)

if __name__ == '__main__':
    _api = _init_api()
    plugin.run()