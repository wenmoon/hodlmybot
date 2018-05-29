#!/usr/bin/env python3

class AbstractBot(object):
    async def post_message(self, message, channel):
        pass

    async def post_reply(self, message, channel):
        pass

    async def post_image(self, image, animated, channel):
        pass
