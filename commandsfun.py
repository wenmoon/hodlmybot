import random

def fomo(bot, update):
    fomo_pics = [
        'http://recruitingdaily.com/wp-content/uploads/sites/6/2017/10/fomo1.jpg',
        'https://4.bp.blogspot.com/-AlE0-SaJD9o/VxQa79mwrQI/AAAAAAABp4g/wLAX-ziiVFACgL-EC5aFJI4NNFYdfhfigCLcB/s1600/FOMO.png',
        'http://www.fomofestival.com.au/wp-content/uploads/2017/07/logo.png',
        'https://smartliving365.com/wp-content/uploads/2014/07/FOMO.jpg',
        'https://image.slidesharecdn.com/dontfightthefomo-170213055538/95/dont-fight-the-fomo-6-638.jpg?cb=1487025166',
        'https://victimtocharm.files.wordpress.com/2015/03/fomo-like-a-mofo.jpg?w=640',
        'https://d1qb2nb5cznatu.cloudfront.net/startups/i/4111244-7522ae6e53f25cf0e01ce9c9479bf3c6-medium_jpg.jpg?buster=1494303361',
        'http://www.2uomaha.org/wp-content/uploads/2013/10/YOLO-FOMO.png',
        'http://lovemindbodyheart.com/wp-content/uploads/2016/06/do-i-have-fomo-940x675.jpg',
        'https://s3.amazonaws.com/ns.images/newspring/collection/series_fuse/web.fightingfomo_promo.2x1.jpg',
        'https://i.amz.mshcdn.com/lUiSMH_1GICPM2TblSbwtCt09BI=/950x534/filters:quality(90)/2013%2F07%2F09%2F81%2FSocialNetwo.3f53a.jpg',
    ]
    bot.send_photo(chat_id=update.message.chat_id, photo=random.choice(fomo_pics))


def fud(bot, update):
    fud_pics = [
        'https://cdn-images-1.medium.com/max/827/1*ulMcUA-Kmbk5vBw3vIobVw.png',
        'https://www.smallcapasia.com/wp-content/uploads/2017/09/crypto-lingo.jpg',
        'https://res.cloudinary.com/teepublic/image/private/s--tvWB4gBj--/t_Preview/b_rgb:ffffff,c_limit,f_jpg,h_630,q_90,w_630/v1516580235/production/designs/2297248_0.jpg'
    ]
    bot.send_photo(chat_id=update.message.chat_id, photo=random.choice(fud_pics))


def hodl(bot, update):
    hold_pics = [
        'http://i0.kym-cdn.com/photos/images/newsfeed/001/325/560/cbc.jpg',
        'https://i.redd.it/23hgyh92wtaz.jpg',
        'https://i.imgur.com/vWUqfc1.jpg',
        'http://i.imgur.com/Gr4I4sM.jpg',
        'http://i0.kym-cdn.com/entries/emojis/original/000/024/987/hodlittt.jpg'
    ]
    bot.send_photo(chat_id=update.message.chat_id, photo=random.choice(hold_pics))


def carlos(bot, update):
    carlos_gifs = [
        'https://i.warosu.org/data/biz/img/0066/59/1516312521744.gif',
        'https://everipedia-storage.s3-accelerate.amazonaws.com/ProfilePics/carlos-matos__02520.gif',
        'https://thumbs.gfycat.com/PleasedEducatedGalah-size_restricted.gif',
        'https://thumbs.gfycat.com/QueasyPlaintiveAmberpenshell-max-1mb.gif',
        'https://thumbs.gfycat.com/SecondaryDistinctCapybara-max-1mb.gif',
        'https://thumbs.gfycat.com/IllfatedDismalAracari-size_restricted.gif',
        'https://media1.tenor.com/images/df4fc55538e36393840781b8531486da/tenor.gif',
        'https://media.tenor.com/images/8e52d994707190980f71d1867b498257/tenor.gif',
        'https://thumbs.gfycat.com/DelayedSillyImpala-size_restricted.gif',
        'https://thumbs.gfycat.com/MeaslySpecificHarrierhawk-size_restricted.gif'
    ]
    bot.sendDocument(chat_id=update.message.chat_id, document=random.choice(carlos_gifs))


def racklehahn(bot, update):
    rackle_gifs = [
        'https://media.giphy.com/media/4PUj9Ueww5tlrhC8ET/giphy.gif',
        'https://media.giphy.com/media/9Dg89jzSNeojyGDCpg/giphy.gif',
        'https://media.giphy.com/media/hTEtcqdYpadJwnTPLo/giphy.gif',
        'https://media.giphy.com/media/fs9B75LDKNXdkHASCB/giphy.gif',
    ]
    bot.sendDocument(chat_id=update.message.chat_id, document=random.choice(rackle_gifs))


def shouldi(bot, update):
    update.message.reply_text(random.choice(['Yes.', 'No.']))


def diceroll(bot, update):
    update.message.reply_text(random.choice(['1', '2', '3', '4', '5', '6']))
