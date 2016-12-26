from src.instagramapi import InstagramAPI

if __name__ == '__main__':
    api = InstagramAPI("hwzearth", "")
    api.login()

    #api.upload_photo("../data/content/Bora_Bora_Lagoon.jpg", "Bora Bora Island, French Polynesia. #earth #earthporn #scenery #photography #bora #borabora #island #french #polynesia")


    api.upload_photo("../data/content/Mesa Arch, Canyonlands National Park, Utah, United States.jpg", "Mesa Arch, Canyonlands National Park, Utah, United States. #earth #earthporn #scenery #photography #mesa #arch #canyonlands #national #park #utah #us #usa")


    print api.last_response.content