import os

from flask import Flask, session, render_template, request, redirect, url_for,jsonify, flash
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
  return render_template('index.html')


if __name__ == "__main__":
        main()


@app.route("/registration", methods=["POST","GET"])
def reg():
    if request.method == "GET":
        return render_template('registration.html')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    result = db.execute('SELECT username FROM "users" ').fetchall()
    #print(result)
    if result is not None:
     for name in result:
        if(username==name[0]):
            return render_template("registration.html", message='username exits')   #if username already exits
    if(password == confirm_password):
       secure_password = sha256_crypt.encrypt(str(confirm_password))     #securing password
       db.execute('INSERT INTO "users"(username,password) VALUES(:username,:password)', {"username": username,"password": secure_password})   # put into database
       db.commit()

       return redirect(url_for('main'))   # if all going good
    else:
       return render_template("registration.html", message='confirm_password must be same with password')  #if password and confirm_password dorsnot match


@app.route("/login", methods=["POST","GET"])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    result = db.execute('SELECT password FROM "users" WHERE username=(:username)',{"username":username}).fetchone() #fetch password corressponding username
    if result is None:
        return render_template("login.html",message='username not found must have to register') # username not register
    elif(sha256_crypt.verify(str(password),result[0])): #verifying password
        #print(password)
        session['user_id'] = username
        print(username,session.get('user_id'))
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
            isbn = str(search) # print(select,search)
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


@app.route("/detail/<string:isbn>",)
def detail(isbn):

    result = db.execute('SELECT isbn,title,author,year FROM "book" WHERE isbn=(:isbn) ',{"isbn":isbn}).fetchone()
    reviews = db.execute('SELECT review,point,username FROM "review" JOIN "users" ON users.id=review.user_id JOIN "book" ON book.id=review.book_id WHERE book.isbn=(:isbn)',{"isbn":isbn}).fetchall()
   # print( result,reviews,isbn)
    return render_template('detail.html',result=result, review=reviews,isbn=isbn)


@app.route("/search/<string:isbn>", methods=["POST","GET"])
def Review(isbn):
    review = request.form.get('review')
    point = int(request.form.get('point'))  # fetching data from the form
   # print(session.get('user_id'))
    if session.get('user_id') is None:      #looking for user_id
        return redirect(url_for('login'))                                     # ....error in redirecting to the same page after login  and after reviewing redirecting to detail page
    username = session.get('user_id')        #get user_id

    USERNAME = db.execute('SELECT username FROM "review" JOIN "users" ON users.id=review.user_id JOIN "book" ON book.id=review.book_id WHERE book.isbn=(:isbn)',{"isbn":isbn}).fetchall()  # checking if user already responses or not
    print(USERNAME)

    if USERNAME:              # check for if user is already responses or not
        flash('you have already reviewed')
        return redirect(url_for('detail', isbn=isbn))

    user_id = db.execute('SELECT id FROM "users" WHERE username=(:username)',{"username":username}).fetchone()  #fetching user_id from database
    book_id = db.execute('SELECT id FROM "book" WHERE isbn=(:isbn)',{"isbn":isbn}).fetchone()          #fetching book_id from databse
    if book_id is not None:                      #inserting review  and all stuffs to the database
      db.execute('INSERT INTO "review" (review,point,book_id,user_id) VALUES(:review, :point, :book_id, :user_id)',{"review":review, "point":point,"book_id":book_id[0], "user_id":user_id[0]})
      print(f'user_id{user_id[0]} , isbn_no {isbn},book_id{book_id[0]}, point{point}, review{review}')
      db.commit()
      return redirect(url_for('detail', isbn=isbn))    #if going all good then redirect it to the detail page
    return page_not_found('not found book of this isbn number')  #else error not found


@app.route("/api/<string:isbn>")
def get_api(isbn):
    #print(isbn)
    result = db.execute('SELECT * FROM "book" WHERE isbn=(:isbn)',{"isbn":isbn}).fetchone() #fetching detail related to book of query isbn value
    if result is None:
        return page_not_found("Not found detail")
    title = result[2]
    author = result[3]
    year = result[4]
    review = db.execute('SELECT count(review),AVG(point) FROM "review" JOIN "book" ON book.id=review.book_id WHERE book.isbn=(:isbn)', {"isbn":isbn}).fetchone()
    #print(review,review[0])


    return jsonify({
        "title":title,
        "author":author,
        "year":year,
        "isbn":isbn,
        "review_count":review[0],
        "average_score":format(review[1], '0.2f')
    })


@app.errorhandler(404)
def page_not_found(error):
   return render_template('error.html',message=error), 404













