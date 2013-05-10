#Put your flask here
from flask import Flask, session, redirect, abort, render_template, g, request
import os
import json
import md5

app = Flask(__name__)

# This is here so that app is defined

from authentication import get_salt, requires_auth
from answer_q import *
from get_user_data import *
from db import connect_database
import static

@app.before_request
def initialise():
	g.db = connect_database()

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/get_question', methods=['POST', 'GET'])
def get_question():
	question = session['curr_q'] = get_q(session['username'])
	return json.dumps({'qid': question.qno, 'question':question.body, 'type': question.qtype})

@app.route('/answer_question', methods=['POST', 'GET'])
def answer_question():
	question = session['curr_q']
	correctAnswer = question.ans
	userAnswer = json.loads(request.data)['answer']

	cur = g.db.cursor()
	cur.execute('select count(*) from answers where regnum = %s and qno = %s', (session['username'], question.qno))
	answeredBefore = cur.fetchone()[0] > 0
	if not answeredBefore:
		cur.execute('insert into answers values (%s, %s, %s)', (session['username'], question.qno, userAnswer))
	else:
		cur.execute('update answers set answer = %s where regnum = %s and qno = %s', (userAnswer, session['username'], question.qno))
	cur.close()
	g.db.commit()

	return json.dumps({'correct': correctAnswer == userAnswer})

@app.route('/get_rate_question')
def get_rate_question():
	session['rate_q']=get_q(session['username'],True)
	return json.dumps({'question':session['rate_q'].body,'answer':session['rate_q'].ans})

@app.route('/rate_question')
@requires_auth(['users', 'admin'])
def rate_question():
	data=json.loads(request.data)
	record_rating(session['username'],session['rate_q'].qno,data['points'],data['reason'])
	return ""

@app.route('/performance')
def performance():
	name=json.loads(request.data)['name']
	ans=answer_info(name)
	return json.dumps({'total_answered':ans.total,'total_correct':ans.correct,'details':ans.detail})

@app.route('/questions')
def questions():
	name=json.loads(request.data)['name']
	return json.dumps({'question_info':question_info(name)})

@app.route('/classlist')
def classlist():
	return json.dumps({'classlist':get_classlist()})

@app.route('/score_questions')
def show_score_questions():
	return json.dumps({'diff_data':score_questions()})

@app.route('/check_weak_questions')
def show_check_weak_question():
	return json.dumps({'questions':check_weak_question()})

@app.route('/update_weak_questions')
def do_update_weak_questions():
	data=json.loads(request.data)
	update_weak_question(data['trues'],data['falses'])
	return ""

@app.route('/make_test')
def make_test():
	ans=gen_test()
	return json.dumps({'questions':ans[0],'answers':ans[1]})

app.secret_key = ' \xfe#\x9eO\xd1,\xd3\xb14\xfe\xca\x12\xee\xb1\x89\xd9\xf4\xa1[\x0e\xcb\x0f\xe8'
if __name__ == "__main__":
	#conn = psycopg.connect("dbname=dbass user=dbass host=hamdulay.co.za")
	#cur = conn.cursor()
	app.run()
