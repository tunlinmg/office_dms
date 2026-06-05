import mysql.connector
import config


def drop_database():
    db_name = config.DB_CONFIG.get("database")
    if not db_name:
        print("No database configured in config.DB_CONFIG.")
        return False

    try:
        conn = mysql.connector.connect(
            host=config.DB_CONFIG.get("host"),
            user=config.DB_CONFIG.get("user"),
            password=config.DB_CONFIG.get("password"),
            charset=config.DB_CONFIG.get("charset", "utf8mb4"),
        )
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        print(f"Database '{db_name}' has been dropped.")
        return True
    except mysql.connector.Error as err:
        print(f"Database drop failed: {err}")
        return False
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def main():
    drop_database()


if __name__ == "__main__":
    main()
