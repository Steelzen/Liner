#GCD GitLab repository: https://gitlab.griffith.ie/taehyung.kwon/cpa_assignment3
import datetime
import random
import shlex
from flask import Flask, render_template, request, redirect
from flask import session, url_for
from google.cloud import datastore
import google.oauth2.id_token
from google.auth.transport import requests

app = Flask(__name__)

datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


def retrieveUserInfo(claims):
    entity_key = datastore_client.key('User', claims['email'])
    entity = datastore_client.get(entity_key)

    return entity

def createUserInfo(claims):
    entity_key = datastore_client.key('User', claims['email'])
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'email': claims['email'],
        'name': None,
        'username': None,
        'following': [],
        'follower': [],
        'profile': None,
        'tweet_list':[]
    })

    datastore_client.put(entity)

def createTweet(username, content, time):
    id = random.getrandbits(63)

    entity_key = datastore_client.key('Tweet', id)
    # entity_key = datastore_client.key('Tweet')
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'id': id,
        'owner': username,
        'content': content,
        'time': time,
        'image': []
    })

    datastore_client.put(entity)

    return id


@app.route('/input_username', methods=['POST'])
def inputUsername ():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            warningInputUsername = None
            usernames = []
            
            query = datastore_client.query(kind="User")
            user_list = query.fetch()
            
            for i in user_list:
                usernames.append(i['username'])
                
            if request.form['username'] == "":
                warningInputUsername = 1
            elif request.form['username'] in usernames or request.form['username'] == "null":
                warningInputUsername = 2
            else:
                user_info.update({
                    'name': request.form['displayname'],
                    'username': request.form['username']
                    })
                    
                datastore_client.put(user_info)

        except ValueError as exc:
            error_message = str(exc)            

    return redirect(url_for('.root', warningInputUsername = warningInputUsername))


@app.route('/edit_user_name', methods=['POST'])
def editUserName():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            warning = None
                
            if request.form['name'] == "":
                warning = 1
            else:
                user_info.update({
                    'name': request.form['name']
                    })
                    
                datastore_client.put(user_info)

        except ValueError as exc:
            error_message = str(exc)            

    return redirect(url_for('.root', warning = warning))


@app.route('/edit_user_profile', methods=['POST'])
def editUserProfile():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            user_info.update({
                'profile': request.form['profile']
                })
                    
            datastore_client.put(user_info)

        except ValueError as exc:
            error_message = str(exc)            

    return redirect(url_for('.root'))  


@app.route('/upload_tweet', methods=['POST'])
def addTweet():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    warningUpload = None
    user = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            dt = datetime.datetime.now()

            tweet_list = user_info['tweet_list'] 

            if request.form['content'] == "":
                warningUpload = 1
            else:
                id = createTweet(user_info['username'], request.form['content'], dt)
                tweet_list.append(id)
                user_info.update({
                    'tweet_list': tweet_list
                })
                datastore_client.put(user_info)

        except ValueError as exc:
            error_message = str(exc)

    return redirect(url_for('.root', warningUpload = warningUpload))



@app.route('/search_by', methods=['GET','POST'])
def search():
    has_result = 0
    tweet = None

    search_list = []

    if request.form['search-by'] == "username":
        query_username = datastore_client.query(kind="User")
        query_username.add_filter('username', '=', request.form['search-by-option'])
        result_name = query_username.fetch()
                
        for i in result_name:
            search_list.append(i['username'])
        if not search_list == []:
            has_result = 1   
                                        
    elif request.form['search-by'] == "content":
        query_tweet = datastore_client.query(kind="Tweet")
        tweet = query_tweet.fetch()
        
        for k in tweet:
            if(k['content'].find(request.form['search-by-option']) != -1):
                search_list.append(k['id'])

        if not search_list == []:
            has_result = 1  

    return redirect(url_for('.rootSearch', search_by = request.form['search-by'], text = request.form['search-by-option'], has_result = has_result))



@app.route('/search/<search_by>/<text>', methods=['GET','POST'])
def rootSearch(search_by, text):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    user = None
    result_name = None
    result_content = None
    is_search = 1
    tweet = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            query_user = datastore_client.query(kind="User")
            query_user.add_filter('email', '=', claims["email"])
            user = query_user.fetch()

            search_list = []
            
            if search_by == "username":
                query_username = datastore_client.query(kind="User")
                query_username.add_filter('username', '=', text)
                result_name = query_username.fetch()
                                        
            elif search_by == "content":
                query_tweet = datastore_client.query(kind="Tweet")
                query_tweet.order = ['-time']
                tweet = query_tweet.fetch()

                for k in tweet:
                    if(k['content'].find(text) != -1):
                        search_list.append(k['id'])

                content_keys=[]

                for i in range(len(search_list)):
                    content_keys.append(datastore_client.key('Tweet', search_list[i]))  

                result_content = datastore_client.get_multi(content_keys)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('index.html', user_data=claims, error_message=error_message, 
    user_info = user_info, user = user, result_name = result_name, result_content = result_content, is_search = is_search)



@app.route('/<username>', methods=['GET','POST'])
def viewProfile(username):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    tweet = None
    tweet2 = None
    user = None 

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            query = datastore_client.query(kind="User")
            query.add_filter('username', '=', username)
            user = query.fetch()

            query_tweet = datastore_client.query(kind="Tweet")
            query_tweet.add_filter('owner', '=', username)
            query_tweet.add_filter('time', '>', 0)
            query_tweet.order = ['-time']
            tweet = query_tweet.fetch(limit=50)

   
        except ValueError as exc:
            error_message = str(exc)    
            
    return render_template('profile.html', user_data=claims, error_message=error_message, 
    user_info = user_info, user = user, tweet = tweet)          



@app.route('/follow/<username>', methods=['POST'])
def followUser(username):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    follower_entity = None
    userFollow = username

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            following_list = []
            follower_list = []

            following_list = user_info['following']
            following_list.append(username)
            user_info.update({
                'following': following_list
                })
            datastore_client.put(user_info)

            query_follower = datastore_client.query(kind='User')
            query_follower.add_filter('username', '=', username)
            user = query_follower.fetch()

            for i in user:
                email = i['email']

            follower_key = datastore_client.key('User', email)
            follower_entity = datastore_client.get(follower_key)
            follower_list = follower_entity['follower']
            follower_list.append(user_info['username'])
            follower_entity.update({
                'follower': follower_list
                })
            datastore_client.put(follower_entity)    

        except ValueError as exc:
            error_message = str(exc)

    return redirect(url_for('.viewProfile', username = userFollow))



@app.route('/unfollow/<username>', methods=['POST'])
def unfollowUser(username):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    follower_entity = None
    userFollow = username

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            following_list = []
            follower_list = []

            following_list = user_info['following']

            following_list[:] = [x for x in following_list if not x == username]

            user_info.update({
                'following': following_list
                })

            datastore_client.put(user_info)

            query_follower = datastore_client.query(kind='User')
            query_follower.add_filter('username', '=', username)
            user = query_follower.fetch()

            for i in user:
                email = i['email']

            follower_key = datastore_client.key('User', email)
            follower_entity = datastore_client.get(follower_key)
            follower_list = follower_entity['follower']

            follower_list[:] = [y for y in follower_list if not y == user_info['username']]

            follower_entity.update({
                'follower': follower_list
                })

            datastore_client.put(follower_entity)    

        except ValueError as exc:
            error_message = str(exc)

    return redirect(url_for('.viewProfile', username = userFollow))    


@app.route('/edit_tweet_popup/<int:id>', methods=['GET', 'POST'])
def editTweetPage(id):
    id_token = request.cookies.get("token")
    error_message = None
    tweet = None

    if id_token:
        try:
            query = datastore_client.query(kind="Tweet")
            query.add_filter('id', '=', id)
            tweet = query.fetch()


        except ValueError as exc:
            error_message = str(exc)    

    return render_template('edit_tweet_popup.html', error_message=error_message, tweet = tweet)


@app.route('/edit_tweet/<int:id>', methods=['POST'])
def editTweet(id):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    tweet = None
    warningEdit = None

    if id_token:
        try:
            dt = datetime.datetime.now()

            tweet_key = datastore_client.key('Tweet', id)
            tweet = datastore_client.get(tweet_key)

            if request.form['editTweet'] == "":
                warningEdit = 1
            else:
                tweet.update({
                    'content': request.form['editTweet'],
                    'time': dt
                })
                
                datastore_client.put(tweet)

                warningEdit = 2
                            
        except ValueError as exc:
            error_message = str(exc)
    
    return redirect(url_for('.editTweetPage', id = id, warningEdit = warningEdit))        


@app.route('/delete_tweet/<int:id>', methods=['POST'])
def deleteTweet(id):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)
            tweet_list = user_info['tweet_list']

            tweet_key = datastore_client.key('Tweet', id)
            datastore_client.delete(tweet_key)

            tweet_list[:] = [x for x in tweet_list if not x == id]

            user_info.update({
                'tweet_list': tweet_list
            })

            datastore_client.put(user_info)
            
        except ValueError as exc:
            error_message = str(exc)

    return redirect(url_for('.root'))

          
@app.route('/complete_task/<int:task_board_id>/<int:task_id>', methods=['GET','POST'])
def completeTask(task_board_id, task_id):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    task = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            dt = datetime.datetime.now()

            ancestor_key = datastore_client.key('TaskBoard', task_board_id)
            task_key = datastore_client.key('Task', task_id, parent = ancestor_key)
            task = datastore_client.get(key=task_key)
            task.update({
                'is_complete': True,
                'completion_time': dt
            })
            datastore_client.put(task)
  
        except ValueError as exc:
            error_message = str(exc)

    return redirect(url_for('.viewTaskBoard', id = task_board_id))  


@app.route('/')
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    user = None
    tweet = None
    is_search = 0

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            if user_info == None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)

            if(user_info['username']):
                query_user = datastore_client.query(kind="User")
                query_user.add_filter('email', '=', claims["email"])
                user = query_user.fetch()
                
                query_tweet = datastore_client.query(kind="Tweet")
                query_tweet.order = ['-time']
                tweet = query_tweet.fetch(limit=50)
  
    
        except ValueError as exc:
            error_message = str(exc)

    return render_template('index.html', user_data=claims, error_message=error_message, 
    user_info = user_info, user = user, tweet = tweet, is_search = is_search)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
