import os
import random
import time

import requests
from imgurpython import ImgurClient
from pexels_api import API
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import praw
import spacy

import connectionconstants

imgurApi = ImgurClient(connectionconstants.IMGUR_ID, connectionconstants.IMGUR_SECRET)
pexelsApi = API(connectionconstants.PEXELS_API_KEY)

nlp = spacy.load("en_core_web_sm")

subredditsToSearch = [
    'adhdmeme',
    'AdviceAnimals',
    'Art',
    'Automate',
    'aww',
    'blursedimages',
    'BrandNewSentence',
    'comics',
    'ContagiousLaughter',
    'coolguides',
    'Damnthatsinteresting',
    'DeepRockGalactic',
    'dndmemes',
    'facepalm',
    'forbiddensnacks',
    'funny',
    'gaming',
    'halo',
    'hellsomememes',
    'hmmm',
    'HolUp',
    'humor',
    'interestingasfuck',
    'LifeProTips',
    'MadeMeSmile',
    'meirl',
    'memes',
    'me_irl',
    'mildlyinteresting',
    'MonsterHunter',
    'movies',
    'MurderedByWords',
    'nevertellmetheodds',
    'nonononoyes',
    'pics',
    'ProgrammerHumor',
    'somethingimade',
    'starterpacks',
    'suspiciouslyspecific',
    'technicallythetruth',
    'technology'
    'therewasanattempt',
    'tifu',
    'todayilearned',
    'Unexpected',
    'WatchPeopleDieInside',
    'Wellthatsucks',
    'wholesomememes',
    'youseeingthisshit',
]


# Log in to reddit
def bot_login():
    print("Logging in to Reddit...")
    reddit = praw.Reddit(username=connectionconstants.R_USERNAME,
                         password=connectionconstants.R_PASSWORD,
                         client_id=connectionconstants.R_CLIENT_ID,
                         client_secret=connectionconstants.R_CLIENT_SECRET,
                         user_agent=connectionconstants.R_USER_AGENT)
    print("Logged in!")
    return reddit


def get_saved_comments():
    if os.path.isfile("comments_replied_to.txt"):
        with open("comments_replied_to.txt", "r") as f:
            comments = f.read()
            comments = comments.split("\n")
    else:
        comments = []

    return comments


# Retrieve pexels-api Photo object
photographer = ""
originalImageLink = ""


def retrieve_photo(query):
    # Search for alot_word photo
    pexelsApi.search(query, page=1, results_per_page=15)

    # Get photo entries
    photos = pexelsApi.get_entries()

    photo_idx = 0
    if len(photos) > 1:
        photo_idx = random.randint(0, (len(photos) - 1))

    global photographer
    photographer = photos[photo_idx].photographer
    global originalImageLink
    originalImageLink = photos[photo_idx].original

    response = requests.get(photos[photo_idx].original, stream=True)
    with open('wordPhoto.png', 'wb') as file:
        for chunk in response.iter_content(1024):
            file.write(chunk)


# Image manipulation - an ALOT is born!
def create_alot(alot_word, is_alot_of):
    img_background = Image.open("alot-background.png")
    img_mask = Image.open("alot-mask.png").convert('L')
    img_details = Image.open("alot-details.png").convert("RGBA")
    img_word = Image.open("wordPhoto.png").resize(img_mask.size)
    img_alot = Image.composite(img_background, img_word, img_mask)
    img_alot.paste(img_details, img_details)
    alot_font = ImageFont.truetype("Roboto-Bold.ttf", 48)
    i1 = ImageDraw.Draw(img_alot)
    if is_alot_of:
        i1.text((410, 36), ("ALOT OF\n" + alot_word.upper()), font=alot_font, fill=(0, 0, 0), align="center")
    else:
        i1.text((410, 36), (alot_word.upper() + "\nALOT"), font=alot_font, fill=(0, 0, 0), align="center")
    return img_alot


def run_bot(r, comments_replied_to):
    sub_idx = 0
    if len(subredditsToSearch) > 1:
        sub_idx = random.randint(0, (len(subredditsToSearch) - 1))

    is_alot_of = False
    alot_word = ""

    print("Searching in subreddit " + subredditsToSearch[sub_idx])
    for comment in r.subreddit(subredditsToSearch[sub_idx]).comments(limit=1000):
        if "alot" in comment.body and comment.id not in comments_replied_to and comment.author != r.user.me():
            print("String with \"alot\" found in comment " + comment.id + " by author " + comment.author.name
                  + " in subreddit " + subredditsToSearch[sub_idx])
            if "alot of" in comment.body:
                is_alot_of = True
                print(comment.body)
                words_after = comment.body.split("alot of", 1)[1]
                alot_word = words_after.split()[0]
                print("new alot_word = " + alot_word)
            else:
                print(comment.body)
                words = comment.body.lower().split()
                print(words)
                if 'alot' in words[1:]:
                    alot_word = words[words.index('alot') - 1]
                    print("new alot_word = " + alot_word)

            if alot_word != "":
                global nlp
                doc = nlp(alot_word)
                tag = doc[0].pos_
                if (tag == "NOUN") or ((tag == "ADJ") and not is_alot_of):
                    print(alot_word + " is a usable word.")
                    print("Creating ALOT...")
                    retrieve_photo(alot_word)
                    img_alot = create_alot(alot_word, is_alot_of)
                    path_to_img = ("alots/" + comment.id + ".png")
                    img_alot.save(path_to_img)
                    img_alot.show()

                    # Upload to Imgur and get direct link to image
                    img_link = imgurApi.upload_from_path(path=path_to_img)['link']

                    reply_text = ""
                    if is_alot_of:
                        reply_text += ("> [alot of " + alot_word + "](" + img_link + ")")
                    else:
                        reply_text += ("> [" + alot_word + " alot](" + img_link + ")")
                    reply_text += ("\n \n \n*This bot is dedicated to (but in no way endorsed by) Allie Brosh " +
                                   "for her [groundbreaking documentation on these fantastic creatures]" +
                                   "(http://hyperboleandahalf.blogspot.com/2010/04/alot-is-better-than-you-at" +
                                   "-everything.html).*")
                    reply_text += ("\n\n*[Original photo](" + originalImageLink + ") by " + photographer +
                                   "on Pexels.*")

                    comment.reply(body=reply_text)
                    print("Replied to comment " + comment.id)
                    comments_replied_to.append(comment.id)
                    with open("comments_replied_to.txt", "a") as f:
                        f.write(comment.id + "\n")
                    break
                else:
                    print(alot_word + " is not a usable word. Ending this search.")
    print("Search Completed.")

    print(comments_replied_to)
    print("Sleeping for 300 seconds...")
    time.sleep(300)


reddit = bot_login()
comments_replied_to = get_saved_comments()

# Swap this out for the while loop to only run the bot once:
# run_bot(reddit, comments_replied_to)

# Use this to run the bot indefinitely (until the program is stopped)
# while True:
#     run_bot(reddit, comments_replied_to)

# Use this to generate an alot for a specific word
# test = "money"
# retrieve_photo(test)
# img_test = create_alot(test, True)
# path_to_img = ("alots/" + test + ".png")
# img_test.save(path_to_img)
