import psycopg2

try:
    conn = psycopg2.connect(
        dbname='fusionlab',
        user='fusion_admin',
        password='hello123',
        host='localhost'
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Drop problematic table
    try:
        cur.execute('DROP TABLE IF EXISTS central_mess_payments CASCADE')
        print('Dropped central_mess_payments')
    except:
        pass
    
    # Drop test database
    try:
        cur.execute('DROP DATABASE IF EXISTS test_fusionlab')
        print('Test database dropped')
    except:
        pass
    
    conn.close()
    print('Cleanup complete')
except Exception as e:
    print(f'Error: {e}')
