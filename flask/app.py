from flask import Flask,request
from flask_cors import CORS
import auto
import select_db
from datetime import timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
CORS(app)


model_api = "https://a21f0dd52837.ngrok.io"

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/chrome',methods=['POST'])
def test():
    if request.method=='POST':
        data = request.get_json(force=True)
        url = data['url']
        cid_list = data['cid_list']
        vid = auto.is_url(url)
        state, msg = auto.main(vid,model_api)
        if state == True:
            lost_cid = select_db.check_lost(vid,cid_list)
            if len(lost_cid)!=0:
                check = auto.auto_result_lostcid_insert(vid,lost_cid,model_api)
                print(check)
                if check == False:
                    return msg
            result = select_db.get_chrome_score(vid, cid_list)
            return result
        else:
            return msg


if __name__ == '__main__':
    app.run()
