# -*- coding: utf-8 -*-
# Module: plugin.video.xnxx
# Author: moedje (Roman V. M. SimplePlugin/example framework)
# Created on: 27.08.2017
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys, json, os, re, simpleutils
import xbmc, xbmcgui
from urllib import quote_plus
from simpleplugin import Plugin, Params
from operator import itemgetter

plugin = Plugin()   # Get the plugin url in plugin:// notation.
_url = sys.argv[0]  # Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
__addondir__ = xbmc.translatePath(plugin.addon.getAddonInfo('path'))
__resources__ = os.path.join(__addondir__, 'resources/')
__next__ = os.path.join(__resources__, "next.png")
__filtersex__ = plugin.get_setting('filterorientation')
__sortby__ = plugin.get_setting('sortby')

VIDEOS = json.load(file(os.path.join(__resources__, 'tags.json')))
webreq = simpleutils.CachedWebRequest(cookiePath=os.path.join(xbmc.translatePath('special://profile'), 'addon_data/', plugin.id))
revidblock = re.compile(ur'<div id="(video_.*?)</p></div>', re.DOTALL)
revidparts = re.compile(ur'video_([\d]+).*? src="(.*?)".*?href="(.*?)".*?itle="(.*?)".*?"duration">[\(](.+?)[\)]</span',re.DOTALL)


def parsepageforvideos(html):
    matches = revidblock.findall(html)
    listitems = []
    for vidhtml in matches:
        vmatches = revidparts.findall(vidhtml)
        if vmatches is not None:
            for vidid, img, link, title, length in vmatches:
                linkfull = 'https://flashservice.xvideos.com/embedframe/' + vidid
                label = title + " [COLOR white][I][B]({0})[/B][/I][/COLOR]".format(length)
                label2 = str(length)
                itempath = plugin.get_url(action='play', url=linkfull)
                img = img.replace('THUMBNUM', '{0}')
                icon = img.format(5)
                thumb = img.format(25)
                fanart = img.format(10)
                clearart = img.format(15)
                artwork = {'clearart': clearart, 'thumb': thumb, 'icon': icon, 'fanart': fanart, 'thumb': thumb}
                mitem = {'label': label, 'label2': label2, 'icon': icon, 'thumb': thumb, 'url': itempath,
                         'is_playable': True, 'is_folder': False, 'art': artwork, 'mime': 'video/mp4', 'info': {'video': {'Runtime': length}}}
                mitem.update(ctx(linkfull))
                listitems.append(mitem)
    return listitems

def DL(url):
    resp = None
    html = None
    try:
        resp = webreq.getSource(url)
        html = resp.encode('latin-1', 'ignore')
    except:
        try:
            resp = webreq.getSource(url)
            html = simpleutils.try_coerce_native(resp)
        except:
            html = resp
    return html

def setView(id=500):
    try:
        xbmc.executebuiltin("Container.SetViewMode({0})".format(str(id)))
    except:
        pass

def ctx(url):
    #pathdl = "plugin://plugin.video.tumblrv/download/" + vidurl
    pathdl = plugin.get_url(action='download', vidurl=url)
    citem = ('Download', 'RunPlugin({0})'.format(pathdl),)
    return {'context_menu': [citem]}

def notify(msg):
    xbmc.executebuiltin("Notification('{0}')".format(msg))

def getinput(title='Search', default=None):
    search_term = None
    if default is None:
        default = plugin.get_setting('lastsearch')
    kb = xbmc.Keyboard('default', 'heading')
    kb.setDefault(default)
    kb.setHeading(title)
    kb.setHiddenInput(False)
    kb.doModal()
    if (kb.isConfirmed()):
        search_term = kb.getText()
    if search_term is not None:
        plugin.set_setting('lastsearch', search_term)
    else:
        search_term = False
    return search_term

@plugin.action()
def root():
    """
    Root virtual folder
    This is mandatory item.
    """
    listitems = []
    searchitem = None
    for tagkey in VIDEOS.iterkeys():
        numtags = str(len(VIDEOS[tagkey]))
        if tagkey.lower() != 'search':
            label = "{0} [COLOR white][I]({1})[/I][/COLOR]".format(tagkey, numtags)
            tagpath = plugin.get_url(action='taglistforletter', tagkey=tagkey)
            listitems.append({'label': label, 'label2': numtags, 'url': tagpath})
        else:
            label = "[COLOR yellow][B]{0}[/B][/COLOR]".format(tagkey)
            tagpath = plugin.get_url(action='newsearch')#, page=0)
            searchitem = {'label': label, 'label2': numtags, 'url': tagpath}
    listitems.sort(key=itemgetter('label'), reverse=False)
    listitems.insert(0, searchitem)
    return listitems

@plugin.action()
def taglistforletter(params):
    """Virtual subfolder"""
    # Create 1-item list with a link to a playable video.
    #plugin.log(message=str("** Taglist: " + str(repr(params))), level=xbmc.LOGERROR)
    listitems = []
    for item in VIDEOS.get(params.tagkey, []):
        tagname = item.get('tagname', None)
        if tagname is not None:
            tagpath = plugin.get_url(action='videosfortag', tagname=tagname, page=1)
            litem = {'label': item.get('name', tagname), 'thumb': item.get('thumb', 'DefaultFolder.png'), 'url': tagpath}
            listitems.append(litem)
    #setView(551)
    return listitems
    #return plugin.create_listing(listitems, succeeded=True, update_listing=True, cache_to_disk=False, view_mode=51, content='movies')

@plugin.action()
def videosfortag(params):
    tagname = params.tagname
    pagenum = '1'
    doup = False
    if params.page is not None:
        pagenum = params.page
    tagurl = "http://www.xnxx.com/tags/{0}/{1}/t:{2}/s:{3}".format(tagname, str(pagenum), __filtersex__, __sortby__)
    pagenum = str(1 + int(pagenum))
    nexturl = "http://www.xnxx.com/tags/{0}/{1}/t:{2}/s:{3}".format(tagname, str(pagenum), __filtersex__, __sortby__)
    nextpagepath = plugin.get_url(action='videosfortag', tagname=tagname, page=pagenum)
    nextitem = {'label': 'Next -> #{0}'.format(pagenum), 'label2': nexturl, 'thumb': os.path.join(__resources__, 'next.png'), 'url': nextpagepath}
    html = DL(tagurl)
    '''
    try:
        resp = webreq.getSource(url=tagurl).encode('latin-1', 'ignore')
        html = resp.partition('div class="mozaique"')[-1].rpartition('class="no-page">Next</a>')[0]
    except:
        plugin.log('Error downloading page', xbmc.LOGERROR)
    try:
        resp = webreq.getSource(url=tagurl)
        html = simpleutils.try_coerce_native(resp).partition('div class="mozaique"')[-1].rpartition('class="no-page">Next</a>')[0]
    except:
        plugin.log('Error downloading page', xbmc.LOGERROR)
    '''
    matches = revidblock.findall(html)
    listitems = []
    listitems = parsepageforvideos(html)
    if len(listitems) > 0:
      listitems.append(nextitem)
    return listitems
    '''
    for vidhtml in matches:
        vmatches = revidparts.findall(vidhtml)
        if vmatches is not None:
            for vidid, thumb, link, title, length in vmatches:
                linkfull = 'https://flashservice.xvideos.com/embedframe/' + vidid
                label = title + " [COLOR white][I][B]({0})[/B][/I][/COLOR]".format(length)
                label2 = linkfull
                itempath = plugin.get_url(action='play', url=linkfull)
                mitem = {'label': label, 'label2': label2, 'thumb': thumb.replace('THUMBNUM', '1'), 'url': itempath, 'is_playable': True}
                mitem.update(ctx(linkfull))
                listitems.append(mitem)
    listitems.append(nextitem)
    return listitems
    '''

@plugin.action()
def download(params):
    try:
        urlvideo = params.vidurl
        plugin.log(message=str("** download: " + str(repr(params))), level=xbmc.LOGINFO) 
        try:
            import YDStreamExtractor
            from YDStreamExtractor import getVideoInfo
            from YDStreamExtractor import handleDownload
        except:
            notify("Couldn't load YouTubeDL Addon")
        info = getVideoInfo(urlvideo, resolve_redirects=True)
        dlpath = plugin.get_setting('downloadpath')
        if not os.path.exists(dlpath):
            dlpath = xbmc.translatePath("home://")
        handleDownload(info, bg=True, path=dlpath)
    except:
        if urlvideo is not None:
            notify("Failed " + urlvideo)
        else:
            notify("No video URL was found to download")
    return None

@plugin.action()
def newsearch():
    term = getinput()
    if not term:
        notify('No search terms provided')
        return None
    nextpathurl = plugin.get_url(action='search', page=0, term=term)
    surl = "http://www.xnxx.com/?k={0}&p={1}&typef={2}&sort={3}&datef=all&durf=all".format(term, 0, __filtersex__,__sortby__)
    nexturl = "http://www.xnxx.com/?k={0}&p={1}&typef={2}&sort={3}&datef=all&durf=1-10min".format(term, 1,__filtersex__,__sortby__)
    nextpathurl = plugin.get_url(action='search', page=1, term=term)
    nextlbl = "[B]Next[/B] -> Page [COLOR green]#{0}[/COLOR]".format(2)
    nextitem = {'label': nextlbl, 'label2': "1", 'thumb': __next__, 'url': nextpathurl}
    html = DL(surl)
    listitems = []
    listitems = parsepageforvideos(html)
    if len(listitems) > 0:
        listitems.append(nextitem)
    return listitems

@plugin.action()
def search(params):
    page = params.page
    term = params.term
    if page is None:
        page = 0
    nextpage = int(page) + 1
    if term is None:
        return None
    term = quote_plus(term)
    surl = "http://www.xnxx.com/?k={0}&p={1}&typef={2}&sort={3}&datef=all&durf=all".format(term, page, __filtersex__, __sortby__)
    nexturl = "http://www.xnxx.com/?k={0}&p={1}&typef={2}&sort={3}&datef=all&durf=1-10min".format(term, nextpage, __filtersex__,  __sortby__)
    nextpathurl = plugin.get_url(action='search', page=nextpage, term=term)
    nextlbl = "[B]Next[/B] -> Page [COLOR green]#{0}[/COLOR]".format(nextpage)
    nextitem = {'label': nextlbl, 'label2': str(nextpage), 'thumb': __next__, 'url': nextpathurl}
    html = DL(surl)
    listitems = []
    listitems = parsepageforvideos(html)
    if len(listitems) > 0:
        listitems.append(nextitem)
    return listitems

@plugin.action()
def play(params):
    """Play video"""
    # Return a string containing a playable video URL
    plugin.log(message=str("** play: " + str(repr(params))), level=xbmc.LOGINFO)
    vidurl = params.url
    webreq = simpleutils.CachedWebRequest(cookiePath=os.path.join(xbmc.translatePath('special://profile'), 'addon_data/', plugin.id))
    resp = simpleutils.to_unicode(webreq.getSource(vidurl))
    movurl = resp.split("html5player.setVideoUrlHigh('",1)[-1].split("'",1)[0]
    if not movurl.startswith('http'):
        matches = re.compile(ur"html5player.setVideoUrlHigh\('(.*?)'").findall(resp)
        if matches is not None:
            if isinstance(matches, list):
                movurl = matches.pop()
            else:
                moveurl = matches
    plugin.log(message="Video url: " + movurl, level=xbmc.LOGINFO)
    litem = plugin.create_list_item({"url": movurl})
    litem.setInfo(type='video', infoLabels={"Genre": "porn"})
    litem.setMimeType("video/mp4")
    return plugin.create_listing(listing=plugin.resolve_url(path=movurl, play_item=litem, succeeded=True), update_listing=False)
    #return movurl

'''
def get_categories(ITEMS):
    """
    Get the list of video categories.

    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.

    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :return: The list of video categories
    :rtype: list
    """
    if isinstance(ITEMS, list):
        keys = []
        for ITEM in ITEMS:
            keys.append(ITEM.iterkeys())
        return keys
    else:
        return ITEMS.iterkeys()

def get_videos(category):
    """
    Get the list of videofiles/streams.

    Here you can insert some parsing code that retrieves
    the list of video streams in the given category from some site or server.

    .. note:: Consider using `generators functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :param category: Category name
    :type category: str
    :return: the list of videos in the category
    :rtype: list
    """
    return VIDEOS[category]

def list_tags(ITEMS):
    list_items = []
    for ITEM in ITEMS:
        thumbimg = ITEM.get('thumb', 'DefaultFolder.png')
        name = ITEM.get('name', '')
        tagname = ITEM.get('tagname', '')
        genre = ITEM.get('genre', '')
        list_item = xbmcgui.ListItem(label=name, label2=genre)
        list_item.setArt({'thumb': thumbimg, 'icon': thumbimg, 'fanart': thumbimg})
        list_item.setInfo('video', {'title': name, 'genre': tagname})
        url = get_url(action='list_videos', tagname=tagname)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def get_tag(tagname):
    xurl = 'http://www.xnxx.com/tags/{0}/t:gay/s:uploaddate'.format(tagname)

def list_categories(ITEMS=VIDEOS):
    """
    Create the list of video categories in the Kodi interface.
    """
    # Get video categories
    #categories = get_categories(ITEMS)
    # Iterate through categories
    for category in VIDEOS.iterkeys():
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        thumbimg = ITEMS.get(category, [{'thumb': 'DefaultFolder.png'}])[0].get('thumb', 'DefaultVideo.png')
        list_item.setArt({'thumb': thumbimg,
                          'icon': thumbimg,
                          'fanart': thumbimg})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': category, 'genre': category})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_videos(category, **kwargs):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    # Get the list of videos in the category.
    if isinstance(kwargs, list):
        videos = kwargs
    else:
        videos = get_videos(category)
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        list_item.setInfo('video', {'title': video['name'], 'genre': video['genre']})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(action='play', video=video['video'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

'''

if __name__ == '__main__':
    plugin.run()  # Start plugin
