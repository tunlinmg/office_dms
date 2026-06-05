import config

print('Testing config.init_db()')
config.init_db()
print('init_db done')
conn = config.get_db_connection()
print('conn', conn is not None)
if conn:
    cursor = conn.cursor()
    cursor.execute('SHOW TABLES')
    print('tables:', cursor.fetchall())
    cursor.execute('SHOW TABLES LIKE "user%"')
    print('user tables:', cursor.fetchall())
    cursor.execute('SHOW TABLES LIKE "%user%"')
    print('tables like user:', cursor.fetchall())
    cursor.close()
    conn.close()
