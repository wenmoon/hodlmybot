#!/usr/bin/env python

class AbstractBot(object):
    def post_message(self, message, channel):
        pass

    def post_reply(self, message, channel):
        pass

    def post_image(self, image, animated, channel):
        pass

    # TODO
    # def start_job(sefl, job, )