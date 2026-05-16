from sys import maxsize

from spryng.application.module import Module

from spryng_web.dispatcher import DefaultRequestDispatcher
from spryng_web.post_collection_hook import WebProcessingPostCollectionHook
from spryng_web.server import Server

module = Module(__name__)
module.add_hook(WebProcessingPostCollectionHook(order=maxsize))
module.component()(DefaultRequestDispatcher)
module.component()(Server)

