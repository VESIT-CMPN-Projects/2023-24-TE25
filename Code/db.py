from PyQt5 import QtSql


db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
db.setDatabaseName("data.sqlite")
if not db.open():
    print("Error")

# query.exec_("create table user (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username VARCHAR(100) NOT NULL, email VARCHAR(100) NOT NULL, password VARCHAR(100) NOT NULL);")
# query.exec_(
#     "insert into user (username, email, password) values ('Manigandan', 'mani@gmail.com', 'mani');")

# query.exec_("select * from userdata where id = 1;")
# query.first()
# print(query.value('username'), query.value('password'))


def signup(query, username, email, password):
    if not query.exec_("""create table user (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username VARCHAR(100) NOT NULL, email VARCHAR(100) NOT NULL, password VARCHAR(100) NOT NULL);"""):
        print(f"Error creating table: {query.lastError().text()}")
        return
    print(username, email, password)
    try:
        query.exec_(
            f"insert into user (username, email, password) values ('{username}', '{email}', '{password}');")
    except Exception as e:
        print(e)


def user_exists(query, username):
    query.exec_("select * from users where username = '%s';" % (username))
    query.first()
    return query.value("username") is not None


def login(query, username, password):
    query.exec_("select * from user where username = '%s' and password = '%s';" %
                (username, password))
    query.first()
    return (
        query.value("username") is not None
        and query.value("password") is not None
    )


def add_stream_links(user_id, stream_link):
    query = QtSql.QSqlQuery()
    print(user_id, stream_link)
    if not query.exec_("""
            CREATE TABLE IF NOT EXISTS stream_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stream_link VARCHAR(200),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """):
        print(f"Error creating table: {query.lastError().text()}")
        return

    query.prepare(
        "INSERT INTO stream_links (user_id, stream_link) VALUES (?, ?)")
    query.addBindValue(user_id)
    query.addBindValue(stream_link)
    if not query.exec_():
        print(f"Error inserting row: {query.lastError().text()}")
        return

    print("Row inserted successfully.")


def get_stream_links(user_id):
    query = QtSql.QSqlQuery()
    query.exec_(f"SELECT * FROM stream_links WHERE user_id = {user_id}")
    links = []
    while query.next():
        user_id = query.value(1)
        stream_link = query.value(2)
        links.append(stream_link)

    return links
