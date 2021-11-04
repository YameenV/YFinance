import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# import
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():

    if not session.get("user_id"):
        return redirect("/login")

    """Show portfolio of stocks"""
    rows = db.execute('''SELECT symbol, transacted, SUM(shares) as totalShares
                        FROM transacation
                        WHERE user_id = :user_id
                        GROUP BY symbol
                        HAVING totalShares > 0;
                     ''', user_id = session["user_id"]
                        )
    print(rows)
    transaction = []
    main_total = 0
    for row in  rows:
        stock = lookup(row["symbol"])
        transaction.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "shares": row["totalShares"],
            "price": usd(stock["price"]),
            "total": usd(row["totalShares"] * stock["price"]),
            "transacted": row["transacted"]
        })
        main_total += row["totalShares"] * stock["price"]

    row = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])

    cash = row[0]["cash"]
    main_total += cash

    # print(rows)
    # print(transaction)
    return render_template("index.html", transaction = transaction, cash = usd(cash), main_total = usd(main_total) )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        quote = lookup(symbol)

        if quote == None:
            return apology("No quote found", 403)
        if not request.form.get("symbol"):
            return apology("Write a quote", 403)

        row = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        cash = row[0]["cash"]
        update_cash = cash - float(shares) * quote["price"]

        if update_cash < 0:
            return apology("Sorry cannot afford", 408)

        db.execute(" UPDATE users SET cash=:update_cash WHERE id=:id",
                    update_cash = update_cash,
                    id=session["user_id"])

        db.execute('''
            INSERT INTO transacation
            (user_id, symbol, name, shares, price)
            VALUES(:user_id, :symbol, :name, :shares, :price)
           ''',
           user_id = session["user_id"],
           symbol = quote["symbol"],
           name = quote["name"],
           shares = shares,
           price = usd(quote["price"])
        )

        return redirect("/")

    else:
         return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute('''SELECT symbol, transacted, shares
                        FROM transacation
                        WHERE user_id = :user_id;''',
                        user_id = session["user_id"] )

    transactions= []
    for row in  rows:
        stock = lookup(row["symbol"])
        transactions.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "shares": row["shares"],
            "price": usd(stock["price"]),
            "transacted": row["transacted"]
        })

    return render_template("history.html", transaction=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        print(request.form.get("symbol"))
        quote = lookup(request.form.get("symbol"))

        if quote == None:
            return apology("No quote found", 403)
        if not request.form.get("symbol"):
            return apology("Write a quote", 403)

        return render_template("quoted.html", quote={
            'name': quote['name'],
            'symbol': quote['symbol'],
            'price': usd(quote['price'])
        })

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        if not request.form.get("username"):
            return apology("must provide username", 403)

        if len(request.form.get("username")) <= 5:
            return apology("must 6 letter username")

        if not request.form.get("password"):
            return apology("must provide password", 403)

        if len(request.form.get("password")) <= 7:
            return apology("must 8 character password")

        if not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password does not match", 403)

        checkusername = db.execute("SELECT username FROM users WHERE username = :username",
                          username = request.form.get("username"))
        # print(checkusername)
        if len(checkusername) > 0:
            return apology("Username already taken", 409)

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username = request.form.get("username"), hash=generate_password_hash(request.form.get("password")))

    return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        quote = lookup(symbol)

        if quote == None:
            return apology("No quote found", 403)
        if not request.form.get("symbol"):
            return apology("Write a quote", 403)

        row = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        cash = row[0]["cash"]
        update_cash = cash + float(shares) * quote["price"]

        if update_cash < 0:
            return apology("Sorry cannot afford", 408)

        db.execute(" UPDATE users SET cash=:update_cash WHERE id=:id",
                    update_cash = update_cash,
                    id=session["user_id"])

        db.execute('''
            INSERT INTO transacation
            (user_id, symbol, name, shares, price)
            VALUES(:user_id, :symbol, :name, :shares, :price)
           ''',
           user_id = session["user_id"],
           symbol = quote["symbol"],
           name = quote["name"],
           shares =- int(shares),
           price = usd(quote["price"])
        )

        return redirect("/")

    else:

        no_share = db.execute(''' SELECT symbol
                              FROM transacation
                              WHERE user_id = :user_id
                              GROUP BY symbol
                              HAVING SUM(shares) > 0;
                                ''', user_id=session["user_id"])

        return render_template("sell.html", symbols=[ row["symbol"] for row in no_share ])



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
