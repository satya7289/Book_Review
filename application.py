import os

from flask import Flask, session, render_template, request, redirect, url_for,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def main():
  return render_template("index.html")


if __name__ == "__main__":
        main()


@app.route("/registration", methods=["POST","GET"])
def reg():

    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    result = db.execute('SELECT username FROM "user" ').fetchall()
    #print(result)
    if result is not None:
     for name in result:
        if(username==name[0]):
            return render_template("registration.html", message='username exits')   #if username already exits
    if(password == confirm_password):
       secure_password = sha256_crypt.encrypt(str(confirm_password))     #securing password
       db.execute('INSERT INTO "user"(username,password) VALUES(:username,:password)', {"username": username,"password": secure_password})   # put into database
       db.commit()

       return redirect(url_for('main'))   # if all going good
    else:
       return render_template("registration.html", message='confirm_password must be same with password')  #if password and confirm_password dorsnot match


@app.route("/login", methods=["POST","GET"])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    result = db.execute('SELECT password FROM "user" WHERE username=(:username)',{"username":username}).fetchone() #fetch password corressponding username
    if result is None:
        return render_template("login.html",message='username not found must have to register') # username not register
    elif(sha256_crypt.verify(str(password),result[0])): #verifying password
        #print(password)
        session['user_id'] = username
        return redirect(url_for('main'))
    else:
        return render_template("login.html",message='username or password is wrong')  #if password doesnot match with username


@app.route("/logout")
def logout():
    session.pop('user_id',None)
    return redirect(url_for('main'))


@app.route("/search", methods=["POST","GET"])
def search():
    select = request.form.get('select')
    search = request.form.get('search')
    if(search==''):
        return render_template("search.html",message='enter the what you search')
    if(select=='ISBN'):
        try:
            isbn = int(search) # print(select,search)
            result = db.execute('SELECT * FROM "book" WHERE isbn=(:isbn)',{"isbn":isbn}).fetchall()  # print(result)
            return render_template("result.html",result=result)
        except:
            return render_template("search.html",message='Enter isbn number')
    elif(select=='TITLE'):
       try:
         title = str(search) #print(select,title)
         result = db.execute('SELECT * FROM "book" WHERE title LIKE (:title) ',{"title":'%'+title+'%'}).fetchall()   # print(result)
         return render_template("result.html",result=result)
       except:
            return render_template("search.html", message='Enter name')
    elif (select == 'AUTHOR'):
        try:
            author = str(search)   # print(search, author)
            result = db.execute('SELECT * FROM "book" WHERE author LIKE (:author) ', {"author":'%'+ author +'%'}).fetchall()      #print(result)
            return render_template("result.html", result=result)
        except:
            return render_template("search.html", message='Enter name')
    elif (select == 'YEAR'):
        try:
            year = int(search)  #  print(select, year)
            result = db.execute('SELECT * FROM "book" WHERE year=(:year)',{"year":year}).fetchall()     #  print(result)
            return render_template("result.html",result=result)
        except:
            return render_template("search.html", message='Enter the year')
    else:
        return render_template("search.html",message='select to search')


@app.route("/api/<int:isbn>")
def get_api(isbn):
    #print(isbn)
    result = db.execute('SELECT * FROM "book" WHERE isbn=(:isbn)',{"isbn":isbn}).fetchone() #fetching detail related to book of query isbn value
    if result is None:
        return page_not_found("Not found detail")
    title = result[2]
    author = result[3]
    year = result[4]

    #query for review has been left

    return jsonify({
        "title":title,
        "author":author,
        "year":year,
        "isbn":isbn,
        "review":34,
        "average_score":5.0
    })


@app.errorhandler(404)
def page_not_found(error):
   return render_template('error.html',message=error), 404













