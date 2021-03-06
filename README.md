
# Instabot #

**Automatically follow and post to Instagram without official API**

## Prerequisites
 * Python 2.7
 * ```pip install -r requirements.txt```


## Usage
 
### Instafollow
 * clone repo with ```git clone https://github.com/rhawiz/app.git``` or download through github.
 * ```cd app/app```
 * run ```python instafollow.py --username <param> --password <param> --rate <param> --wait <param> --similar_users <param>```
 * params
    * **username:** Account username
    * **password:** Account password
    * **rate:** Number of followers per wait period (e.g 100)
    * **wait:** Wait time between x follows in seconds (e.g. 60,90)
    * **similar_users:** Similar user accounts to retrieve user list seperated by a comma (,) (e.g. ig_user1,ig_user2,ig_user3)

### Instaunfollow
 * clone repo with ```git clone https://github.com/rhawiz/app.git``` or download through github.
 * ```cd app/app```
 * run ```python instaunfollow.py --username <param> --password <param> --rate <param> --wait <param> --unfollow```
 * params
    * **username:** Account username
    * **password:** Account password
    * **rate:** Number of unfollows per wait time (e.g 100)
    * **wait:** Wait time between n follows (e.g. 60,90)
    * **unfollow:** Add this parameter to unfollow all users. Don't include the parameter to only unfollow those who aren't following back.

### TODO

* Create separate bots for:
    * Posting content
    * Following users
    * Unfollowing users (needs additional logic, i.e. don't follow immediately)
* Tag generator
    * Tags from caption content
    * Tags from image
* Upload image from URL
* Content collector
* Dashboard
* Verify insta account before adding


