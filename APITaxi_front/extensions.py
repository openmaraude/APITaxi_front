#coding:utf-8

from APITaxi_utils.cache_user_datastore import CacheUserDatastore
user_datastore = CacheUserDatastore()
from flask.ext.uploads import (UploadSet, IMAGES)
images = UploadSet('images', IMAGES)
