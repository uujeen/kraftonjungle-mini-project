from flask import Flask, render_template, request, jsonify, session, redirect, url_for, g
import jwt
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('52.78.249.190', 27017)
db = client.jungle

app = Flask(__name__)
app.secret_key = 'test'


@app.route('/')
def index():
    return render_template("login.html")


@app.route('/sign_up', methods=['POST'])
def sign_up():
    if request.method == 'POST':
        # form -input 의 name 속성을 기준으로 가져오기
        user_num = 0
        user_name = request.form.get('user_name')
        user_id = request.form.get('user_id')
        user_pw1 = request.form.get('user_pw1')
        user_pw2 = request.form.get('user_pw2')

        # 유효성 검사 및 DB추가
        if user_pw1 == user_pw2:
            db.users.insert_one(
                {'user_num': user_num, 'user_name': user_name, 'user_id': user_id, 'user_pw': user_pw1})

            user_list = list(db.users.find({}))
            dicts = []
            for i in range(0, len(user_list)):
                temp = user_list[i]['user_num']
                dicts.append(temp)
            count = max(dicts)+1
            db.users.update_one({'user_num': 0}, {'$set': {'user_num': count}})
        else:
            return render_template('login.html')

    return render_template('login.html')


@app.route('/sign_in', methods=['POST'])
def sign_in():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_pw = request.form.get('user_pw')
        # 로그인 input에 담긴 id와 pw 받아옴

        # user_id로 찾아온 db상의 user_pw가 input에서 받은 user_pw와 일치하는지
        result = db.users.find_one({'user_id': user_id})
        user_num = result['user_num']
        user_name = result['user_name']
        if user_id == result['user_id'] and user_pw == result['user_pw']:
            token = jwt.encode({'user_num': user_num, 'user_id': user_id,
                               'user_name': user_name}, app.secret_key, algorithm='HS256')
            session['token'] = token
            return redirect(url_for('protected'))
        else:
            return render_template('login.html')


@app.route('/protected', methods=['GET'])
def protected():
    token = session.get('token')
    if token:
        try:
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            # print(data)
            return redirect(url_for('main'))
        except:
            session.pop('token', None)
            return jsonify({'error': 'Invalid token'}), 401
    else:
        return redirect(url_for('sign_up'))


@app.route('/main', methods=['GET'])
def main():
    token = session.get('token')
    if token:
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
    user_num = data['user_num']
    list_list = list(db.lists.find({}))
    print("리스트 돌기 전")
    for lists in list_list:
        local_date = datetime.fromisoformat(lists['list_date'])
        if datetime.now() > local_date:
            db.pastlists.insert_one({'list_num': lists['list_num'], 'list_title': lists['list_title'], 'list_date': lists['list_date'],
                                    'list_content': lists['list_content'], 'list_attendent': lists['list_attendent'], 'list_max': lists['list_max'], 'list_writer': lists['list_writer']})
            db.lists.delete_one({'list_num': lists['list_num']})
            print("리스트 도는중")
    print("리스트 돈 후")
    result = db.users.find_one({'user_num': int(user_num)})
    return render_template('main.html', user_name=result['user_name'], list_list=list_list)


@app.route('/new_post', methods=['POST'])
def new_post():
    token = session.get('token')
    if token:
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])

    user_name = data['user_name']
    user_num = data['user_num']

    list_num = 0
    list_title = request.form.get('list_title')
    list_date = request.form.get('list_date')
    list_content = request.form.get('list_content')
    list_attendent = ''.join(user_name)
    list_max = request.form.get('list_max')
    list_writer = user_name

    db.lists.insert_one({'list_num': list_num, 'list_title': list_title, 'list_date': list_date,
                        'list_content': list_content, 'list_attendent': list_attendent, 'list_max': list_max, 'list_writer': user_name})

    list_list = list(db.lists.find({}))
    dicts = []
    for i in range(0, len(list_list)):
        temp = list_list[i]['list_num']
        dicts.append(temp)
    count = max(dicts)+1
    db.lists.update_one({'list_num': 0}, {'$set': {'list_num': count}})

    return redirect(url_for('main', user_num=user_num))


@app.route('/mypage', methods=['GET'])
def mypage():
    token = session.get('token')
    if token:
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
    user_name = data['user_name']
    user_num = data['user_num']
    list_list = list(db.lists.find({'list_writer': user_name}))
    result = db.users.find_one({'user_num': user_num})

    return render_template('mypage.html', user_name=result['user_name'], list_list=list_list)


@app.route('/detail/<list_num>', methods=['GET'])
def detail(list_num):
    token = session.get('token')
    if token:
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
    user_name = data['user_name']
    list_one = db.lists.find_one({'list_num': int(list_num)})
    attendent_count = list_one['list_attendent']
    comment_list = db.comments.find({'comment_list_num': int(list_num)})

    return render_template('detail.html', list_one=list_one, attendent_count=attendent_count, user_name=user_name, comment_list=comment_list)


@app.route('/new_comment/<list_num>', methods=['POST'])
def new_comment(list_num):
    token = session.get('token')
    if token:
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])

    comment_num = 0
    comment_content = request.form.get('comment_content')
    comment_date = datetime.now()
    comment_user_name = data['user_name']
    comment_list_num = int(list_num)

    db.comments.insert_one({'comment_num': comment_num, 'comment_content': comment_content,
                           'comment_date': comment_date, 'comment_user_name': comment_user_name, 'comment_list_num': comment_list_num})

    comment_list = list(db.comments.find({}))
    dicts = []
    for i in range(0, len(comment_list)):
        temp = comment_list[i]['comment_num']
        dicts.append(temp)
    count = max(dicts)+1
    db.comments.update_one({'comment_num': 0}, {
                           '$set': {'comment_num': count}})

    return redirect(url_for('detail', list_num=list_num))


@app.route('/update/<list_num>', methods=['POST'])
def update(list_num):

    new_list_title = request.form.get('new_list_title')
    new_list_date = request.form.get('new_list_date')
    new_list_content = request.form.get('new_list_content')
    new_list_max = request.form.get('new_list_max')

    db.lists.update_one({'list_num': int(list_num)}, {
                        '$set': {'list_title': new_list_title}})
    db.lists.update_one({'list_num': int(list_num)}, {
                        '$set': {'list_date': new_list_date}})
    db.lists.update_one({'list_num': int(list_num)}, {
                        '$set': {'list_content': new_list_content}})
    db.lists.update_one({'list_num': int(list_num)}, {
                        '$set': {'list_max': new_list_max}})

    return redirect(url_for('mypage'))


@app.route('/delete/<list_num>', methods=['POST'])
def delete(list_num):

    db.lists.delete_one({'list_num': int(list_num)})

    return redirect(url_for('mypage'))


@app.route('/detail/attendent/<list_num>', methods=['GET'])
def attendent(list_num):
    token = session.get('token')
    if token:
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
    result = db.lists.find_one({'list_num': int(list_num)})
    list_attendent = result['list_attendent']
    user_name = data['user_name']
    new_list_attendent = list_attendent+', '+user_name

    db.lists.update_one({'list_attendent': list_attendent}, {
                        '$set': {'list_attendent': new_list_attendent}})

    return redirect(url_for('detail', list_num=int(list_num)))


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return render_template('login.html')


@app.route('/pasttable', methods=['GET'])
def pasttable():
    token = session.get('token')
    if token:
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
    user_num = data['user_num']
    list_list = list(db.pastlists.find({}).sort('list_date', -1))
    result = db.users.find_one({'user_num': int(user_num)})

    return render_template('pasttable.html', user_name=result['user_name'], list_list=list_list)


if __name__ == "__main__":
    app.run('0.0.0.0', port=5000, debug=True)
