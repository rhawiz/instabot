
# Instabot #

**Automatically follow and post to Instagram without official API**

## Prerequisites
 * Python 2.7
 * ```pip install -r requirements.txt```


## Usage
 * clone repo ```git clone https://github.com/rhawiz/instabot.git```
### Instafollow
 * ```cd instabot/src```
 * run ```python instafollow.py --username <param> --password <param> --rate <param> --wait <param> --similar_users <param>```
 * params
    * **username:** Account username
    * **password:** Account password
    * **rate:** Number of followers per wait period (e.g 100)
    * **wait:** Wait time between x follows in seconds (e.g. 60,90)
    * **similar_users:** Similar user accounts to retrieve user list seperated by a comma (,) (e.g. ig_user1,ig_user2,ig_user3)
### Instaunfollow
 * ```cd instabot/src```
 * run ```python instaunfollow.py --username <param> --password <param> --rate <param> --wait <param> --unfollow```
 * params
    * **username:** Account username
    * **password:** Account password
    * **rate:** Number of unfollows per wait time (e.g 100)
    * **wait:** Wait time between n follows (e.g. 60,90)
    * **unfollow:** Add this parameter to unfollow all users. Don't include the parameter to only unfollow those who aren't following back.