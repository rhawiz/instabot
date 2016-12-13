
# Instabot #

**Automatically follow and post to Instagram without official API**

## Prerequisites
 * Python 2.7
 * ```pip install -r requirements.txt```


## Usage
 * clone repo ```git clone https://github.com/rhawiz/instabot.git```
 * InstaFollow
     * run ```python instafollow.py --username <param> --password <param> --follows <param> --wait <param> --similar_users <param>```
     * params
        * **username:** Account username
        * **password:** Account password
        * **follows:** Number of followers per wait period
        * **wait:** Wait time between x follows in seconds
        * **similar_users:** Similar user accounts to retrieve user list seperated by a comma (,) without any spaces 
            (e.g. ig_user1,ig_user2,ig_user3)
 * InstaUnfollow    
     * run ```python instaunfollow.py --username <param> --password <param> --unfollows <param> --wait <param>```
     * params
        * **username:** Account username
        * **password:** Account password
        * **follows:** Number of followers per wait time
        * **wait:** Wait time between n follows
        * **similar_users:** Similar user accounts to retrieve user list