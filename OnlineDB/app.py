from flask import Flask, render_template
import psycopg2
import os

app = Flask(__name__)

# Database connection settings
DATABASE_URL = os.environ.get('DATABASE_URL')


@app.route('/')
def index():
    # Connect to the database
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    # Replace this query with one relevant to your database schema
    cur.execute('SELECT * FROM listings')
    rows = cur.fetchall()

    # Close connection
    cur.close()
    conn.close()

    # Render the data on a web page
    return render_template('index.html', rows=rows)


if __name__ == "__main__":
    app.run(debug=True)
