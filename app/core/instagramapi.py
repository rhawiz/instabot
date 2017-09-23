#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import imageio
import requests
import random
import json
import hashlib
import hmac
import urllib
import uuid
import time
import copy
import math
from requests_toolbelt import MultipartEncoder
from moviepy.editor import VideoFileClip

import struct
import imghdr


def get_image_size(fname):
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            raise RuntimeError("Invalid Header")
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                raise RuntimeError("PNG: Invalid check")
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            fhandle.seek(0)  # Read 0xff next
            size = 2
            ftype = 0
            while not 0xc0 <= ftype <= 0xcf:
                fhandle.seek(size, 1)
                byte = fhandle.read(1)
                while ord(byte) == 0xff:
                    byte = fhandle.read(1)
                ftype = ord(byte)
                size = struct.unpack('>H', fhandle.read(2))[0] - 2
            # We are at a SOFn block
            fhandle.seek(1, 1)  # Skip `precision' byte.
            height, width = struct.unpack('>HH', fhandle.read(4))
        else:
            raise RuntimeError("Unsupported format")
        return width, height


class InstagramAPI:
    API_URL = 'https://i.instagram.com/api/v1/'
    DEVICE_SETTINTS = {
        'manufacturer': 'Xiaomi',
        'model': 'HM 1SW',
        'android_version': 18,
        'android_release': '4.3'
    }
    USER_AGENT = 'Instagram 9.2.0 Android ({android_version}/{android_release}; 320dpi; 720x1280; {manufacturer}; {model}; armani; qcom; en_US)'.format(
        **DEVICE_SETTINTS)
    IG_SIG_KEY = '012a54f51c49aa8c5c322416ab1410909add32c966bbaa0fe3dc58ac43fd7ede'
    EXPERIMENTS = 'ig_android_progressive_jpeg,ig_creation_growth_holdout,ig_android_report_and_hide,ig_android_new_browser,ig_android_enable_share_to_whatsapp,ig_android_direct_drawing_in_quick_cam_universe,ig_android_huawei_app_badging,ig_android_universe_video_production,ig_android_asus_app_badging,ig_android_direct_plus_button,ig_android_ads_heatmap_overlay_universe,ig_android_http_stack_experiment_2016,ig_android_infinite_scrolling,ig_fbns_blocked,ig_android_white_out_universe,ig_android_full_people_card_in_user_list,ig_android_post_auto_retry_v7_21,ig_fbns_push,ig_android_feed_pill,ig_android_profile_link_iab,ig_explore_v3_us_holdout,ig_android_histogram_reporter,ig_android_anrwatchdog,ig_android_search_client_matching,ig_android_high_res_upload_2,ig_android_new_browser_pre_kitkat,ig_android_2fac,ig_android_grid_video_icon,ig_android_white_camera_universe,ig_android_disable_chroma_subsampling,ig_android_share_spinner,ig_android_explore_people_feed_icon,ig_explore_v3_android_universe,ig_android_media_favorites,ig_android_nux_holdout,ig_android_search_null_state,ig_android_react_native_notification_setting,ig_android_ads_indicator_change_universe,ig_android_video_loading_behavior,ig_android_black_camera_tab,liger_instagram_android_univ,ig_explore_v3_internal,ig_android_direct_emoji_picker,ig_android_prefetch_explore_delay_time,ig_android_business_insights_qe,ig_android_direct_media_size,ig_android_enable_client_share,ig_android_promoted_posts,ig_android_app_badging_holdout,ig_android_ads_cta_universe,ig_android_mini_inbox_2,ig_android_feed_reshare_button_nux,ig_android_boomerang_feed_attribution,ig_android_fbinvite_qe,ig_fbns_shared,ig_android_direct_full_width_media,ig_android_hscroll_profile_chaining,ig_android_feed_unit_footer,ig_android_media_tighten_space,ig_android_private_follow_request,ig_android_inline_gallery_backoff_hours_universe,ig_android_direct_thread_ui_rewrite,ig_android_rendering_controls,ig_android_ads_full_width_cta_universe,ig_video_max_duration_qe_preuniverse,ig_android_prefetch_explore_expire_time,ig_timestamp_public_test,ig_android_profile,ig_android_dv2_consistent_http_realtime_response,ig_android_enable_share_to_messenger,ig_explore_v3,ig_ranking_following,ig_android_pending_request_search_bar,ig_android_feed_ufi_redesign,ig_android_video_pause_logging_fix,ig_android_default_folder_to_camera,ig_android_video_stitching_7_23,ig_android_profanity_filter,ig_android_business_profile_qe,ig_android_search,ig_android_boomerang_entry,ig_android_inline_gallery_universe,ig_android_ads_overlay_design_universe,ig_android_options_app_invite,ig_android_view_count_decouple_likes_universe,ig_android_periodic_analytics_upload_v2,ig_android_feed_unit_hscroll_auto_advance,ig_peek_profile_photo_universe,ig_android_ads_holdout_universe,ig_android_prefetch_explore,ig_android_direct_bubble_icon,ig_video_use_sve_universe,ig_android_inline_gallery_no_backoff_on_launch_universe,ig_android_image_cache_multi_queue,ig_android_camera_nux,ig_android_immersive_viewer,ig_android_dense_feed_unit_cards,ig_android_sqlite_dev,ig_android_exoplayer,ig_android_add_to_last_post,ig_android_direct_public_threads,ig_android_prefetch_venue_in_composer,ig_android_bigger_share_button,ig_android_dv2_realtime_private_share,ig_android_non_square_first,ig_android_video_interleaved_v2,ig_android_follow_search_bar,ig_android_last_edits,ig_android_video_download_logging,ig_android_ads_loop_count_universe,ig_android_swipeable_filters_blacklist,ig_android_boomerang_layout_white_out_universe,ig_android_ads_carousel_multi_row_universe,ig_android_mentions_invite_v2,ig_android_direct_mention_qe,ig_android_following_follower_social_context'
    SIG_KEY_VERSION = '4'

    # username            # Instagram username
    # password            # Instagram password
    # debug               # Debug
    # uuid                # UUID
    # device_id           # Device ID
    # username_id         # Username ID
    # token               # _csrftoken
    # isLoggedIn          # Session status
    # rank_token          # Rank token
    # IGDataPath          # Data storage path

    def __init__(self, username, password, debug=False, IGDataPath=None):
        try:
            from app import logger
        except ImportError:
            from utils import get_logger
            logger = get_logger()
        self.logger = logging.LoggerAdapter(logger, {'user': username, 'bot': 'API'})
        m = hashlib.md5()
        m.update(username.encode('utf-8') + password.encode('utf-8'))
        self.device_id = self.generate_device_id(m.hexdigest())
        self.set_user(username, password)
        self.is_logged_in = False
        self.last_response = None

    def set_user(self, username, password):
        self.username = username
        self.password = password
        self.uuid = self.generate_uuid(True)

    def login(self, force=False):
        if not self.is_logged_in or force:
            self.s = requests.Session()
            # if you need proxy make something like this:
            # self.s.proxies = {"https" : "http://proxyip:proxyport"}
            if (
                    self.send_request('si/fetch_headers/?challenge_type=signup&guid=' + self.generate_uuid(False), None,
                                      True)):

                data = {
                    'phone_id': self.generate_uuid(True),
                    '_csrftoken': self.last_response.cookies['csrftoken'],
                    'username': self.username,
                    'guid': self.uuid,
                    'device_id': self.device_id,
                    'password': self.password,
                    'login_attempt_count': '0'
                }

                if self.send_request('accounts/login/', self.generate_signature(json.dumps(data)), True):
                    self.is_logged_in = True
                    self.username_id = self.last_json["logged_in_user"]["pk"]
                    self.rank_token = "{}_{}".format(self.username_id, self.uuid)
                    self.token = self.last_response.cookies["csrftoken"]

                    self.sync_features()
                    self.auto_complete_user_list()
                    self.timeline_feed()
                    self.getv2_inbox()
                    self.get_recent_activity()

                    self.logger.info("Successfully logged in as user {}".format(self.username))

                    return True

    def sync_features(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'id': self.username_id,
            '_csrftoken': self.token,
            'experiments': self.EXPERIMENTS
        })
        return self.send_request('qe/sync/', self.generate_signature(data))

    def auto_complete_user_list(self):
        return self.send_request('friendships/autocomplete_user_list/')

    def timeline_feed(self):
        return self.send_request('feed/timeline/')

    def megaphone_log(self):
        return self.send_request('megaphone/log/')

    def expose(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'id': self.username_id,
            '_csrftoken': self.token,
            'experiment': 'ig_android_profile_contextual_feed'
        })
        return self.send_request('qe/expose/', self.generate_signature(data))

    def logout(self):
        logout = self.send_request('accounts/logout/')

    def upload_photo(self, photo, caption=None, upload_id=None):
        if upload_id is None:
            upload_id = str(int(time.time() * 1000))
        data = {
            'upload_id': upload_id,
            '_uuid': self.uuid,
            '_csrftoken': self.token,
            'image_compression': '{"lib_name":"jt","lib_version":"1.3.0","quality":"87"}',
            'photo': ('pending_media_%s.jpg' % upload_id, open(photo, 'rb'), 'application/octet-stream',
                      {'Content-Transfer-Encoding': 'binary'})
        }
        m = MultipartEncoder(data, boundary=self.uuid)
        self.s.headers.update({'X-IG-Capabilities': '3Q4=',
                               'X-IG-Connection-Type': 'WIFI',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'Accept-Encoding': 'gzip, deflate',
                               'Content-type': m.content_type,
                               'Connection': 'close',
                               'User-Agent': self.USER_AGENT})
        response = self.s.post(self.API_URL + "upload/photo/", data=m.to_string())
        if response.status_code == 200:
            if self.configure(upload_id, photo, caption):
                self.expose()
        return False

    def upload_video(self, video, thumbnail, caption=None, upload_id=None):
        if upload_id is None:
            upload_id = str(int(time.time() * 1000))
        data = {
            'upload_id': upload_id,
            '_csrftoken': self.token,
            'media_type': '2',
            '_uuid': self.uuid,
        }
        m = MultipartEncoder(data, boundary=self.uuid)
        self.s.headers.update({'X-IG-Capabilities': '3Q4=',
                               'X-IG-Connection-Type': 'WIFI',
                               'Host': 'i.instagram.com',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'Accept-Encoding': 'gzip, deflate',
                               'Content-type': m.content_type,
                               'Connection': 'keep-alive',
                               'User-Agent': self.USER_AGENT})
        response = self.s.post(self.API_URL + "upload/video/", data=m.to_string())

        if response.status_code == 200:
            body = json.loads(response.text)
            upload_url = body['video_upload_urls'][3]['url']
            upload_job = body['video_upload_urls'][3]['job']

            videoData = open(video, 'rb').read()
            request_size = int(math.floor(len(videoData) / 4))
            lastRequestExtra = (len(videoData) - (request_size * 3))

            headers = copy.deepcopy(self.s.headers)
            self.s.headers.update({'X-IG-Capabilities': '3Q4=',
                                   'X-IG-Connection-Type': 'WIFI',
                                   'Cookie2': '$Version=1',
                                   'Accept-Language': 'en-US',
                                   'Accept-Encoding': 'gzip, deflate',
                                   'Content-type': 'application/octet-stream',
                                   'Session-ID': upload_id,
                                   'Connection': 'keep-alive',
                                   'Content-Disposition': 'attachment; filename="video.mov"',
                                   'job': upload_job,
                                   'Host': 'upload.instagram.com',
                                   'User-Agent': self.USER_AGENT})
            for i in range(0, 4):
                start = i * request_size
                if i == 3:
                    end = i * request_size + lastRequestExtra
                else:
                    end = (i + 1) * request_size
                length = lastRequestExtra if i == 3 else request_size
                content_range = "bytes {start}-{end}/{lenVideo}".format(start=start, end=(end - 1),
                                                                        lenVideo=len(videoData)).encode('utf-8')

                self.s.headers.update({'Content-Length': str(end - start), 'Content-Range': content_range, })
                response = self.s.post(upload_url, data=videoData[start:start + length])

            self.s.headers = headers

            if response.status_code == 200:

                if self.configure_video(upload_id, video, thumbnail, caption):
                    self.expose()
        return False

    def direct_share(self, media_id, recipients, text=None):
        # TODO Instagram.php 420-490
        return False

    def configure_video(self, upload_id, video, thumbnail, caption=''):
        clip = VideoFileClip(video)
        self.upload_photo(photo=thumbnail, caption=caption, upload_id=upload_id)
        data = json.dumps({
            'upload_id': upload_id,
            'source_type': 3,
            'poster_frame_index': 0,
            'length': 0.00,
            'audio_muted': False,
            'filter_type': 0,
            'video_result': 'deprecated',
            'clips': {
                'length': clip.duration,
                'source_type': '3',
                'camera_position': 'back',
            },
            'extra': {
                'source_width': clip.size[0],
                'source_height': clip.size[1],
            },
            'device': self.DEVICE_SETTINTS,
            '_csrftoken': self.token,
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'caption': caption,
        })
        return self.send_request('media/configure/?video=1', self.generate_signature(data))

    def configure(self, upload_id, photo, caption=''):
        (w, h) = get_image_size(photo)
        data = json.dumps({
            '_csrftoken': self.token,
            'media_folder': 'Instagram',
            'source_type': 4,
            '_uid': self.username_id,
            '_uuid': self.uuid,
            'caption': caption,
            'upload_id': upload_id,
            'device': self.DEVICE_SETTINTS,
            'edits': {
                'crop_original_size': [w * 1.0, h * 1.0],
                'crop_center': [0.0, 0.0],
                'crop_zoom': 1.0
            },
            'extra': {
                'source_width': w,
                'source_height': h,
            }})
        return self.send_request('media/configure/?', self.generate_signature(data))

    def edit_media(self, mediaId, captionText=''):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'caption_text': captionText
        })
        return self.send_request('media/' + str(mediaId) + '/edit_media/', self.generate_signature(data))

    def remove_self_tag(self, mediaId):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token
        })
        return self.send_request('media/' + str(mediaId) + '/remove/', self.generate_signature(data))

    def media_info(self, mediaId):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'media_id': mediaId
        })
        return self.send_request('media/' + str(mediaId) + '/info/', self.generate_signature(data))

    def delete_media(self, mediaId):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'media_id': mediaId
        })
        return self.send_request('media/' + str(mediaId) + '/delete/', self.generate_signature(data))

    def change_password(self, newPassword):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'old_password': self.password,
            'new_password1': newPassword,
            'new_password2': newPassword
        })
        return self.send_request('accounts/change_password/', self.generate_signature(data))

    def explore(self):
        return self.send_request('discover/explore/')

    def comment(self, mediaId, commentText):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'comment_text': commentText
        })
        return self.send_request('media/' + str(mediaId) + '/comment/', self.generate_signature(data))

    def delete_comment(self, mediaId, commentId):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token
        })
        return self.send_request('media/' + str(mediaId) + '/comment/' + str(commentId) + '/delete/',
                                 self.generate_signature(data))

    def change_profile_picture(self, photo):
        # TODO Instagram.php 705-775
        return False

    def remove_profile_picture(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token
        })
        return self.send_request('accounts/remove_profile_picture/', self.generate_signature(data))

    def set_private_account(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token
        })
        return self.send_request('accounts/set_private/', self.generate_signature(data))

    def set_public_account(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token
        })
        return self.send_request('accounts/set_public/', self.generate_signature(data))

    def get_profile_data(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token
        })
        return self.send_request('accounts/current_user/?edit=true', self.generate_signature(data))

    def edit_profile(self, url, phone, first_name, biography, email, gender):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'external_url': url,
            'phone_number': phone,
            'username': self.username,
            'full_name': first_name,
            'biography': biography,
            'email': email,
            'gender': gender,
        })
        return self.send_request('accounts/edit_profile/', self.generate_signature(data))

    def get_username_info(self, username_id):
        return self.send_request('users/' + str(username_id) + '/info/')

    def get_self_username_info(self):
        return self.get_username_info(self.username_id)

    def get_recent_activity(self):
        activity = self.send_request('news/inbox/?')
        return activity

    def get_following_recent_activity(self):
        activity = self.send_request('news/?')
        return activity

    def getv2_inbox(self):
        inbox = self.send_request('direct_v2/inbox/?')
        return inbox

    def get_user_tags(self, username_id):
        tags = self.send_request(
            'usertags/' + str(username_id) + '/feed/?rank_token=' + str(self.rank_token) + '&ranked_content=true&')
        return tags

    def get_self_user_tags(self):
        return self.get_user_tags(self.username_id)

    def tag_feed(self, tag):
        userFeed = self.send_request(
            'feed/tag/' + str(tag) + '/?rank_token=' + str(self.rank_token) + '&ranked_content=true&')
        return userFeed

    def get_media_likers(self, mediaId):
        likers = self.send_request('media/' + str(mediaId) + '/likers/?')
        return likers

    def get_geo_media(self, username_id):
        locations = self.send_request('maps/user/' + str(username_id) + '/')
        return locations

    def get_self_geo_media(self):
        return self.get_geo_media(self.username_id)

    def fb_user_search(self, query):
        query = self.send_request(
            'fbsearch/topsearch/?context=blended&query=' + str(query) + '&rank_token=' + str(self.rank_token))
        return query

    def search_users(self, query):
        query = self.send_request('users/search/?ig_sig_key_version=' + str(self.SIG_KEY_VERSION)
                                  + '&is_typeahead=true&query=' + str(query) + '&rank_token=' + str(self.rank_token))
        return query

    def search_username(self, usernameName):
        query = self.send_request('users/' + str(usernameName) + '/usernameinfo/')
        return query

    def sync_from_address_book(self, contacts):
        return self.send_request('address_book/link/?include=extra_display_name,thumbnails',
                                 "contacts=" + json.dumps(contacts))

    def search_tags(self, query):
        query = self.send_request(
            'tags/search/?is_typeahead=true&q=' + str(query) + '&rank_token=' + str(self.rank_token))
        return query

    def get_timeline(self):
        query = self.send_request('feed/timeline/?rank_token=' + str(self.rank_token) + '&ranked_content=true&')
        return query

    def get_user_feed(self, username_id, max_id='', min_timestamp=None):
        query = self.send_request(
            'feed/user/' + str(username_id) + '/?max_id=' + str(max_id) + '&min_timestamp=' + str(min_timestamp)
            + '&rank_token=' + str(self.rank_token) + '&ranked_content=true')
        return query

    def get_self_user_feed(self, max_id='', min_timestamp=None):
        return self.get_user_feed(self.username_id, max_id, min_timestamp)

    def get_hashtag_feed(self, hashtag, max_id=''):
        return self.send_request('feed/tag/' + hashtag + '/?max_id=' + str(
            max_id) + '&rank_token=' + self.rank_token + '&ranked_content=true&')

    def search_location(self, query):
        locationFeed = self.send_request('fbsearch/places/?rank_token=' + str(self.rank_token) + '&query=' + str(query))
        return locationFeed

    def get_location_feed(self, location_id, max_id=''):
        return self.send_request('feed/location/' + str(
            location_id) + '/?max_id=' + max_id + '&rank_token=' + self.rank_token + '&ranked_content=true&')

    def get_popular_feed(self):
        popularFeed = self.send_request(
            'feed/popular/?people_teaser_supported=1&rank_token=' + str(self.rank_token) + '&ranked_content=true&')
        return popularFeed

    def get_user_followings(self, username_id, max_id=''):
        return self.send_request('friendships/' + str(username_id) + '/following/?max_id=' + str(max_id)
                                 + '&ig_sig_key_version=' + self.SIG_KEY_VERSION + '&rank_token=' + self.rank_token)

    def get_self_users_following(self):
        return self.get_user_followings(self.username_id)

    def get_user_followers(self, username_id, max_id=''):
        if max_id == '':
            return self.send_request('friendships/' + str(username_id) + '/followers/?rank_token=' + self.rank_token)
        else:
            return self.send_request(
                'friendships/' + str(username_id) + '/followers/?rank_token=' + self.rank_token + '&max_id=' + str(
                    max_id))

    def get_self_user_followers(self):
        return self.get_user_followers(self.username_id)

    def like(self, media_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'media_id': media_id
        })
        return self.send_request('media/' + str(media_id) + '/like/', self.generate_signature(data))

    def unlike(self, media_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'media_id': media_id
        })
        return self.send_request('media/' + str(media_id) + '/unlike/', self.generate_signature(data))

    def get_media_comments(self, media_id):
        return self.send_request('media/' + media_id + '/comments/?')

    def set_name_and_phone(self, name='', phone=''):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'first_name': name,
            'phone_number': phone,
            '_csrftoken': self.token
        })
        return self.send_request('accounts/set_phone_and_name/', self.generate_signature(data))

    def get_direct_share(self):
        return self.send_request('direct_share/inbox/?')

    def backup(self):
        # TODO Instagram.php 1470-1485
        return False

    def follow(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'user_id': user_id,
            '_csrftoken': self.token
        })
        return self.send_request('friendships/create/' + str(user_id) + '/', self.generate_signature(data))

    def unfollow(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'user_id': user_id,
            '_csrftoken': self.token
        })
        return self.send_request('friendships/destroy/' + str(user_id) + '/', self.generate_signature(data))

    def block(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'user_id': user_id,
            '_csrftoken': self.token
        })
        return self.send_request('friendships/block/' + str(user_id) + '/', self.generate_signature(data))

    def unblock(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'user_id': user_id,
            '_csrftoken': self.token
        })
        return self.send_request('friendships/unblock/' + str(user_id) + '/', self.generate_signature(data))

    def user_friendship(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'user_id': user_id,
            '_csrftoken': self.token
        })
        return self.send_request('friendships/show/' + str(user_id) + '/', self.generate_signature(data))

    def get_liked_media(self, user_id=''):
        return self.send_request('feed/liked/?max_id=' + str(user_id))

    def generate_signature(self, data):

        parsed_data = urllib.quote(data)
        signed_body = hmac.new(self.IG_SIG_KEY.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
        signature = 'ig_sig_key_version={}&signed_body={}.{}'.format(
            self.SIG_KEY_VERSION,
            signed_body,
            parsed_data
        )

        return signature

    def generate_device_id(self, seed):
        volatile_seed = "12345"
        m = hashlib.md5()
        m.update(seed.encode('utf-8') + volatile_seed.encode('utf-8'))
        return 'android-' + m.hexdigest()[:16]

    def generate_uuid(self, type):
        # according to https://github.com/LevPasha/Instagram-API-python/pull/16/files#r77118894
        # uuid = '%04x%04x-%04x-%04x-%04x-%04x%04x%04x' % (random.randint(0, 0xffff),
        #    random.randint(0, 0xffff), random.randint(0, 0xffff),
        #    random.randint(0, 0x0fff) | 0x4000,
        #    random.randint(0, 0x3fff) | 0x8000,
        #    random.randint(0, 0xffff), random.randint(0, 0xffff),
        #    random.randint(0, 0xffff))
        generated_uuid = str(uuid.uuid4())
        if (type):
            return generated_uuid
        else:
            return generated_uuid.replace('-', '')

    def build_body(bodies, boundary):
        # TODO Instagram.php 1620-1645
        return False

    def send_request(self, endpoint, post=None, login=False):
        if (not self.is_logged_in and not login):
            raise Exception("Not logged in!\n")

        self.s.headers.update({'Connection': 'close',
                               'Accept': '*/*',
                               'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'User-Agent': self.USER_AGENT})

        if (post != None):  # POST
            response = self.s.post(self.API_URL + endpoint, data=post)  # , verify=False
        else:  # GET
            response = self.s.get(self.API_URL + endpoint)  # , verify=False
        self.logger.debug("'{}' {} {} {}".format(response.request.method, response.status_code,
                                                 ' -> '.join([r for r in response.history]), response.url))
        if response.status_code == 200:
            self.last_response = response
            self.last_json = json.loads(response.text)
            return True
        else:
            # logging.info("Request return {} error!".format(response.status_code))
            # for debugging
            try:
                self.last_response = response
                self.last_json = json.loads(response.text)
            except:
                pass
            return False

    def get_total_followers(self, username_id):
        followers = []
        next_max_id = ''
        while 1:
            self.get_user_followers(username_id, next_max_id)
            temp = self.last_json

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] == False:
                return followers
            next_max_id = temp["next_max_id"]

    def get_total_followings(self, username_id):
        followers = []
        next_max_id = ''
        while 1:
            self.get_user_followings(username_id, next_max_id)
            temp = self.last_json

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] == False:
                return followers
            next_max_id = temp["next_max_id"]

    def get_total_user_feed(self, username_id, min_timestamp=None):
        user_feed = []
        next_max_id = ''
        while 1:
            self.get_user_feed(username_id, next_max_id, min_timestamp)
            temp = self.last_json
            for item in temp["items"]:
                user_feed.append(item)
            if temp["more_available"] == False:
                return user_feed
            next_max_id = temp["next_max_id"]

    def get_total_self_user_feed(self, min_timestamp=None):
        return self.get_total_user_feed(self.username_id, min_timestamp)

    def get_total_self_followers(self):
        return self.get_total_followers(self.username_id)

    def get_total_self_followings(self):
        return self.get_total_followings(self.username_id)

    def get_total_liked_media(self, scan_rate=1):
        next_id = ''
        liked_items = []
        for x in range(0, scan_rate):
            temp = self.get_liked_media(next_id)
            temp = self.last_json
            next_id = temp["next_max_id"]
            for item in temp["items"]:
                liked_items.append(item)
        return liked_items
