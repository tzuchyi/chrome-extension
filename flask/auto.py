from __future__ import print_function

import re
import json
import time
import random
import lxml.html
import pymysql
import requests
from lxml.cssselect import CSSSelector

import select_db

# modified from https://github.com/egbertbouman/youtube-comment-downloader
YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v={youtube_id}'
YOUTUBE_COMMENTS_AJAX_URL = 'https://www.youtube.com/comment_service_ajax'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


def is_url(url):
    if len(url) == 0:
        return False
    if url[:32] == 'https://www.youtube.com/watch?v=' and len(url) == 43:
        v_id = url[32:43]
        return v_id
    elif url[:17] == 'https://youtu.be/' and len(url) == 28:
        v_id = url[17:28]
        return v_id
    elif url[:30] == 'https://m.youtube.com/watch?v=' and len(url) == 41:
        v_id = url[30:41]
        return v_id
    else:
        return False


def find_value(html, key, num_chars=2, separator='"'):
    pos_begin = html.find(key) + len(key) + num_chars
    pos_end = html.find(separator, pos_begin)
    return html[pos_begin: pos_end]


def ajax_request(session, url, params=None, data=None, headers=None, retries=5, sleep=20):
    for _ in range(retries):
        response = session.post(url, params=params, data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        if response.status_code in [403, 413]:
            return {}
        else:
            print('ajax_request delay :', sleep)
            time.sleep(sleep)


def download_comments(youtube_id, comment_limit, sleep=.1):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))
    html = response.text
    session_token = find_value(html, 'XSRF_TOKEN', 3)
    session_token = session_token.encode('ascii').decode('unicode-escape')

    data = json.loads(find_value(html, 'var ytInitialData = ', 0, '};') + '}')
    for renderer in search_dict(data, 'itemSectionRenderer'):
        ncd = next(search_dict(renderer, 'nextContinuationData'), None)
        if ncd:
            break

    if not ncd:
        print('comments disabled?')
        # Comments disabled?
        return

    continuations = [(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comments')]

    c = 0
    while continuations:
        print(c, comment_limit)
        if c > comment_limit and comment_limit != -1:
            break

        continuation, itct, action = continuations.pop()
        response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL,
                                params={action: 1,
                                        'pbj': 1,
                                        'ctoken': continuation,
                                        'continuation': continuation,
                                        'itct': itct},
                                data={'session_token': session_token},
                                headers={'X-YouTube-Client-Name': '1',
                                         'X-YouTube-Client-Version': '2.20201202.06.01'})

        if not response:
            break
        if list(search_dict(response, 'externalErrorMessage')):
            raise RuntimeError('Error returned from server: ' + next(search_dict(response, 'externalErrorMessage')))

        if action == 'action_get_comments':
            section = next(search_dict(response, 'itemSectionContinuation'), {})
            for continuation in section.get('continuations', []):
                ncd = continuation['nextContinuationData']
                continuations.append((ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comments'))
            for item in section.get('contents', []):
                continuations.extend([(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comment_replies')
                                      for ncd in search_dict(item, 'nextContinuationData')])

        elif action == 'action_get_comment_replies':
            continuations.extend([(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comment_replies')
                                  for ncd in search_dict(response, 'nextContinuationData')])

        for comment in search_dict(response, 'commentRenderer'):
            c += 1
            yield {'cid': comment['commentId'],
                   'text': ''.join([c['text'] for c in comment['contentText']['runs']]),
                   'time': comment['publishedTimeText']['runs'][0]['text'],
                   'author': comment.get('authorText', {}).get('simpleText', ''),
                   'channel': comment['authorEndpoint']['browseEndpoint']['browseId'],
                   'votes': comment.get('voteCount', {}).get('simpleText', '0'),
                   'photo': comment['authorThumbnail']['thumbnails'][-1]['url'],
                   'heart': next(search_dict(comment, 'isHearted'), False)}

        time.sleep(sleep)


def search_dict(partial, search_key):
    stack = [partial]
    while stack:
        current_item = stack.pop()
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                if key == search_key:
                    yield value
                else:
                    stack.append(value)
        elif isinstance(current_item, list):
            for value in current_item:
                stack.append(value)


def extract_comments(html):
    try:
        tree = lxml.html.fromstring(html)
        item_sel = CSSSelector('.comment-item')
        text_sel = CSSSelector('.comment-text-content')
        time_sel = CSSSelector('.time')
        author_sel = CSSSelector('.user-name')
        vote_sel = CSSSelector('.like-count.off')
        photo_sel = CSSSelector('.user-photo')
        heart_sel = CSSSelector('.creator-heart-background-hearted')

        for item in item_sel(tree):
            yield {'cid': item.get('data-cid'),
                   'text': text_sel(item)[0].text_content(),
                   'time': time_sel(item)[0].text_content().strip(),
                   'author': author_sel(item)[0].text_content(),
                   'channel': item[0].get('href').replace('/channel/', '').strip(),
                   'votes': vote_sel(item)[0].text_content() if len(vote_sel(item)) > 0 else 0,
                   'photo': photo_sel(item)[0].get('src'),
                   'heart': bool(heart_sel(item))}
    except:
        return {}

    for item in item_sel(tree):
        yield {'cid': item.get('data-cid'),
               'text': text_sel(item)[0].text_content(),
               'time': time_sel(item)[0].text_content().strip(),
               'author': author_sel(item)[0].text_content(),
               'channel': item[0].get('href').replace('/channel/', '').strip(),
               'votes': vote_sel(item)[0].text_content() if len(vote_sel(item)) > 0 else 0,
               'photo': photo_sel(item)[0].get('src'),
               'heart': bool(heart_sel(item))}


def extract_reply_cids(html):
    tree = lxml.html.fromstring(html)
    sel = CSSSelector('.comment-replies-header > .load-comments')
    return [i.get('data-cid') for i in sel(tree)]


def download_info(youtube_id, sleep=1):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    youtube_url = YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id)
    response = session.get(youtube_url)
    html = response.text
    data = json.loads(find_value(html, 'var ytInitialData = ', 0, '};') + '}')
    return extract_info(data)


def extract_info(data):
    title = ''.join([item['text'] for item in
                     list(search_dict(list(search_dict(data, 'videoPrimaryInfoRenderer'))[0], 'title'))[0]['runs']])
    view_count = list(search_dict(list(search_dict(data, 'shortViewCount'))[0], 'simpleText'))[0]
    published_time = list(search_dict(list(search_dict(data, 'publishedTimeText'))[0], 'simpleText'))[0]
    channel = list(search_dict(list(search_dict(data, 'videoOwnerRenderer'))[0], 'title'))[0]['runs'][0]['text']
    description = list(search_dict(list(search_dict(data, 'videoSecondaryInfoRenderer'))[0], 'description'))
    description = '' if len(description) == 0 else re.sub(r'\r\n+', '\n', '\n'.join([run['text'] \
                                                                                     for run in list(
            search_dict(list(search_dict(data, 'videoSecondaryInfoRenderer'))[0], 'description'))[0]['runs']]))
    unlike, like = '', ''
    for item in search_dict(data, 'toggleButtonRenderer'):
        for iconType in search_dict(item, 'defaultIcon'):
            if iconType.get('iconType', '') == 'DISLIKE':
                unlike_ = list(search_dict(list(search_dict(item, 'defaultText')), 'label'))
                if len(unlike_) != 0:
                    unlike = unlike_[0]
            if iconType.get('iconType', '') == 'LIKE':
                like_ = list(search_dict(list(search_dict(item, 'defaultText')), 'label'))
                print(like)
                if len(like_) != 0:
                    like = like_[0]

    try:
        hashtag = [t['text'] for t in list(search_dict(data, 'superTitleLink'))[0]['runs'] if t['text'].strip() != '']
    except:
        hashtag = []

    return {  # 'channel_id':channel_id,
        'title': title,
        'view_count': view_count,
        'published_time': published_time,
        'channel': channel,
        'hashtag': hashtag,
        'description': description,
        'num_like': like,
        'num_unlike': unlike
    }


def download_comments_chrome(youtube_id, comment_limit, sleep=.1):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))
    html = response.text
    session_token = find_value(html, 'XSRF_TOKEN', 3)
    session_token = session_token.encode('ascii').decode('unicode-escape')

    data = json.loads(find_value(html, 'var ytInitialData = ', 0, '};') + '}')
    for renderer in search_dict(data, 'itemSectionRenderer'):
        ncd = next(search_dict(renderer, 'nextContinuationData'), None)
        if ncd:
            break

    if not ncd:
        print('comments disabled?')
        # Comments disabled?
        return

    continuations = [(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comments')]

    c = 0
    while continuations:
        print(c, comment_limit)
        if c > comment_limit and comment_limit != -1:
            break

        continuation, itct, action = continuations.pop()
        response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL,
                                params={action: 1,
                                        'pbj': 1,
                                        'ctoken': continuation,
                                        'continuation': continuation,
                                        'itct': itct},
                                data={'session_token': session_token},
                                headers={'X-YouTube-Client-Name': '1',
                                         'X-YouTube-Client-Version': '2.20201202.06.01'})

        if not response:
            break
        if list(search_dict(response, 'externalErrorMessage')):
            raise RuntimeError('Error returned from server: ' + next(search_dict(response, 'externalErrorMessage')))

        if action == 'action_get_comments':
            section = next(search_dict(response, 'itemSectionContinuation'), {})
            for continuation in section.get('continuations', []):
                ncd = continuation['nextContinuationData']
                continuations.append((ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comments'))
            for item in section.get('contents', []):
                continuations.extend([(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comment_replies')
                                      for ncd in search_dict(item, 'nextContinuationData')])

        elif action == 'action_get_comment_replies':
            continuations.extend([(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comment_replies')
                                  for ncd in search_dict(response, 'nextContinuationData')])
        temp = []
        for comment in search_dict(response, 'commentRenderer'):
            c += 1

            temp.append({'cid': comment['commentId'],
                         'text': ''.join([c['text'] for c in comment['contentText']['runs']]),
                         'time': comment['publishedTimeText']['runs'][0]['text'],
                         'author': comment.get('authorText', {}).get('simpleText', ''),
                         'channel': comment['authorEndpoint']['browseEndpoint']['browseId'],
                         'votes': comment.get('voteCount', {}).get('simpleText', '0'),
                         'photo': comment['authorThumbnail']['thumbnails'][-1]['url'],
                         'heart': next(search_dict(comment, 'isHearted'), False)})

        time.sleep(sleep)
        return temp

def main_info(youtube_id, sleep=0.1):
    try:
        youtube_info = download_info(youtube_id)
        return True, [youtube_id, youtube_info]
    except Exception as e:
        print('Error:', str(e))
        # sys.exit(1)
        return False, None


def main_comment_chrome(youtube_id, comment_limit, sleep=0.1):
    try:
        if r'\"isLiveContent\":true' in requests.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id)).text:
            print('Live stream detected! Do not download anything!')
            return False, None
        comments = download_comments_chrome(youtube_id, comment_limit=comment_limit, sleep=sleep)
        return True, [youtube_id, comments]
    except Exception as e:
        print('Error:', str(e))
        # sys.exit(1)
        return False, None

def main_comment(youtube_id, comment_limit, sleep=0.1):
    try:
        if r'\"isLiveContent\":true' in requests.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id)).text:
            print('Live stream detected! Do not download anything!')
            return False, None
        comments = download_comments(youtube_id, comment_limit=comment_limit, sleep=sleep)
        return True, [youtube_id, comments]
    except Exception as e:
        print('Error:', str(e))
        # sys.exit(1)
        return False, None


def insert_comment_old(comment):
    print('insert comments to DB')
    db = select_db.db_operate()

    cursor = db.cursor()

    sql = """INSERT INTO total_review(review_id, text,time,author,channel,votes,video_id) VALUES """
    comments = comment[1]
    records = []
    for i in comments:
        vals = json.loads(i)
        records.append(str((vals['cid'], vals['text'].replace('"', '').replace("'", ''), vals['time'],
                            vals['author'].replace('"', '').replace("'", ''),
                            vals['channel'].replace('"', '').replace("'", ''), vals['votes'], comment[0])))

    cursor.executemany(sql, records)

    db.commit()
    db.close()
    print('Finish insert comment')


def auto_info_insert(vid):
    state, info_ = main_info(youtube_id=vid, sleep=0.1)
    if state == False:
        return False

    return select_db.insert_video(info_)


def auto_comment_insert(vid):
    state, comment_ = main_comment(youtube_id=vid, comment_limit=5000, sleep=0.1)
    if state == False:
        return False

    return select_db.insert_comment(comment_)


def auto_result_insert(vid, api_url):
    try:
        if requests.get(api_url, timeout=3).status_code == 405:
            if requests.post(api_url, json={'video_id': vid}).text == 'success':
                return True
    except:
        return False

def auto_result_lostcid_insert(vid,lost_cid, api_url):
    try:
        if requests.get(api_url, timeout=3).status_code == 405:
            if requests.post(api_url, json={'video_id': vid,'lost_cid':lost_cid}).text == 'success':
                return True
    except:
        return False


def main_result(vid):
    state = select_db.exist_result(vid)
    if state == True:
        scores, info = select_db.get_result(vid, 6)
        select_db.click_plus(vid)
        return True, scores, info
    else:
        return False, None, None


def main(vid, api_url):
    msg = '系統發生錯誤，請稍後再試。'

    if select_db.exist_video(vid) == False:
        print('do video')
        if auto_info_insert(vid) == False:
            return False, msg + 'Error 0'

    if select_db.exist_comment(vid) == False:
        print('do comment')
        if auto_comment_insert(vid) == False:
            return False, msg + 'Erro 1'

    if select_db.exist_result(vid) == False:
        print('do result')
        if auto_result_insert(vid, api_url) == False:
            return False, msg + 'Error 2'

    return True, None


def download_comments_list(youtube_id, comment_limit, sleep=.1):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))
    html = response.text
    session_token = find_value(html, 'XSRF_TOKEN', 3)
    session_token = session_token.encode('ascii').decode('unicode-escape')

    data = json.loads(find_value(html, 'var ytInitialData = ', 0, '};') + '}')
    for renderer in search_dict(data, 'itemSectionRenderer'):
        ncd = next(search_dict(renderer, 'nextContinuationData'), None)
        if ncd:
            break

    if not ncd:
        print('comments disabled?')
        # Comments disabled?
        return

    continuations = [(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comments')]

    c = 0
    while continuations:
        print(c, comment_limit)
        if c > comment_limit and comment_limit != -1:
            break

        continuation, itct, action = continuations.pop()
        response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL,
                                params={action: 1,
                                        'pbj': 1,
                                        'ctoken': continuation,
                                        'continuation': continuation,
                                        'itct': itct},
                                data={'session_token': session_token},
                                headers={'X-YouTube-Client-Name': '1',
                                         'X-YouTube-Client-Version': '2.20201202.06.01'})

        if not response:
            break
        if list(search_dict(response, 'externalErrorMessage')):
            raise RuntimeError('Error returned from server: ' + next(search_dict(response, 'externalErrorMessage')))

        if action == 'action_get_comments':
            section = next(search_dict(response, 'itemSectionContinuation'), {})
            for continuation in section.get('continuations', []):
                ncd = continuation['nextContinuationData']
                continuations.append((ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comments'))
            for item in section.get('contents', []):
                continuations.extend([(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comment_replies')
                                      for ncd in search_dict(item, 'nextContinuationData')])

        elif action == 'action_get_comment_replies':
            continuations.extend([(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comment_replies')
                                  for ncd in search_dict(response, 'nextContinuationData')])

        for comment in search_dict(response, 'commentRenderer'):
            c += 1
            yield comment['commentId']
        time.sleep(sleep)


def main_comment_list(youtube_id, comment_limit, sleep=0.1):
    try:
        if r'\"isLiveContent\":true' in requests.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id)).text:
            print('Live stream detected! Do not download anything!')
            return False, None
        comments = download_comments_list(youtube_id, comment_limit=comment_limit, sleep=sleep)
        return True, [youtube_id, comments]
    except Exception as e:
        print('Error:', str(e))
        # sys.exit(1)
        return False, None


def get_cid_list(youtube_id, comment_limit, sleep=0.1):
    try:
        cid_list = list(main_comment_list(youtube_id, comment_limit, sleep=sleep)[1][1])
        reply_cid_list = []
        for i in cid_list :
            if len(i) >=30:
                reply_cid_list.append(i)
        for i in reply_cid_list:
            cid_list.remove(i)
        count = len(cid_list)//20
        final = []
        for i in range(count):
            temp = cid_list[i*20:(i+1)*20]
            temp.reverse()
            for k in temp:
                final.append(k)
        temp = cid_list[count*20:]
        temp.reverse()
        for k in temp:
            final.append(k)
        return final,reply_cid_list
    except Exception as e:
        print('Error:', str(e))
        #sys.exit(1)
        return False, None



