from instabot.instagramapi import InstagramAPI

class InstaPost():
    def __init__(self, username, password):
        pass

if __name__ == '__main__':
    api = InstagramAPI("hwzearth", "raw12743")
    api.login()


    api.upload_photo("../data/content/Half Dome, Yosemite, CA, United States.jpg", "Half Dome, Yosemite, CA, United States. #earth #earthporn #scenery #photography #stars #half #dome #yosemite #ca #usa")


    print api.last_response.content