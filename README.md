
# Instabot #

**Automatically follow and post to Instagram without official API**

## Prerequisites
 * Python 2.7
 * Click: http://click.pocoo.org/
    * ```pip install click```


## Usage
 * clone repo ```git clone https://github.com/rhawiz/instabot.git```
 * run ```python instafollow.py --username <param> --password <param> --follows <param> --wait <param> --similar_users <param>```
 * params
    * **username:** Account username
    * **password:** Account password
    * **follows:** Number of followers per wait time
    * **wait:** Wait time between n follows
    * **similar_users:** Similar user accounts to retrieve user list
