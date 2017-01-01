from instabot.instagramapi import InstagramAPI

if __name__ == '__main__':
    api = InstagramAPI("hwzearth", "")
    api.login()


    api.upload_photo("../data/content/Milky way over Arizona, United States.jpg", "Milky way over Arizona, United States. #earth #earthporn #scenery #photography #stars #arizona #milkyway #us #usa")


    print api.last_response.content