# -*- coding: utf-8 -*-

# Basic implementation taken from
# http://davisagli.com/blog/using-tiles-to-provide-more-flexible-plone-layouts

from collective.cover.tiles.base import IPersistentCoverTile
from collective.cover.tiles.base import PersistentCoverTile
from plone.app.textfield import RichText
from plone.app.textfield.interfaces import ITransformer
from plone.app.textfield.value import RichTextValue
from plone.tiles.interfaces import ITileDataManager
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone import api
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from collective.portlet.mybookmarks import mybookmarksportlet
from Products.CMFCore.utils import getToolByName
from plone.memoize.instance import memoize

import logging
logger = logging.getLogger("bookmark")

class IMyBookmarksTile(IPersistentCoverTile):

    pass

class myBookmarksTile(PersistentCoverTile):

    index = ViewPageTemplateFile("templates/mybookmarks_tile.pt")

    is_configurable = False 

    def populate_with_object(self, obj):
        super(myBookmarksTile, self).populate_with_object(obj)

        data_mgr = ITileDataManager(self)

        data_mgr.set()

    @property
    @memoize
    def results(self):
        """
        Return a list of user bookmarks
        """
        pc = getToolByName(self.context, 'portal_catalog')
        pm = getToolByName(self.context, 'portal_membership')
        user = pm.getAuthenticatedMember()
        fullname = user.getProperty('fullname', None)
        bookmarks = [x for x in user.getProperty('bookmarks', ())]
        #external_bookmarks = [x for x in user.getProperty('external_bookmarks', ())]
        bookmarks_list = []
        if bookmarks:
            portal_types = getToolByName(self.context, 'portal_types')
            portal_properties = getToolByName(self.context, 'portal_properties')
            site_properties = getattr(portal_properties, 'site_properties')
            if site_properties.hasProperty('types_not_searched'):
                search_types = [x for x
                              in portal_types.keys()
                              if x not in site_properties.getProperty('types_not_searched')]
        for bookmark in bookmarks:
            res = pc.searchResults(UID=bookmark, portal_type=search_types)
            if res:
                bookmark_dict = {}
                bookmark_dict['Title'] = res[0].Title
                bookmark_dict['Description'] = res[0].Description
                bookmark_dict['url'] = "%s/view" % res[0].getURL()
                bookmark_dict['removeValue'] = bookmark
                bookmark_dict['bookmark_type'] = 'bookmarks'
                bookmarks_list.append(bookmark_dict)

            else:
                logger.error("Bookmark '%s' for user %s: this content is not available and the bookmark will be removed" % (bookmark, fullname))
                bookmarks.remove(bookmark)
                bookmarks = tuple(bookmarks)
                user.setMemberProperties({'bookmarks': bookmarks})

        #for bookmark in external_bookmarks:
        #    bookmark_values = bookmark.split('|')
        #    if len(bookmark_values) == 2:
        #        bookmark_infos = self.parseExternalBookmark(bookmark_values)
        #        if bookmark_infos:
        #            bookmarks_list.append(bookmark_infos)
        bookmarks_list.sort(lambda x, y: cmp(x['Title'].lower(), y['Title'].lower()))
        return bookmarks_list

