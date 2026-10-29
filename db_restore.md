# Database Restore Commands (`db_restore.md`)

The database `fusionlab` has been successfully created and restored using the SQL dump file `./fusionlab.sql`.

Below are the exact steps and commands used for the database restoration process:

---

### Step-by-Step Interactive SQL Commands

If you are executing inside `psql` shell:

```sql
-- 1. Connect to default postgres database
\c postgres

-- 2. Drop existing fusionlab database if it exists
DROP DATABASE IF EXISTS fusionlab;

-- 3. Create fresh fusionlab database
CREATE DATABASE fusionlab;

-- 4. Grant all permissions to fusion_admin user
GRANT ALL PRIVILEGES ON DATABASE fusionlab TO fusion_admin;
```

---

### Terminal Execution Commands (CLI)

From your terminal inside `/home/parth/Documents/Fusion/Fusion`:

```bash
# Set password variable and perform database setup + dump restore
PGPASSWORD=hello123 psql -U fusion_admin -h 127.0.0.1 -d postgres -c "DROP DATABASE IF EXISTS fusionlab;"
PGPASSWORD=hello123 psql -U fusion_admin -h 127.0.0.1 -d postgres -c "CREATE DATABASE fusionlab;"
PGPASSWORD=hello123 psql -U fusion_admin -h 127.0.0.1 -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE fusionlab TO fusion_admin;"

# 5. Restore database from fusionlab.sql dump file
PGPASSWORD=hello123 psql -U fusion_admin -h 127.0.0.1 -d fusionlab -f ./fusionlab.sql
```

---

### Single-Line Command

```bash
PGPASSWORD=hello123 psql -U fusion_admin -h 127.0.0.1 -d postgres -c "DROP DATABASE IF EXISTS fusionlab;" && \
PGPASSWORD=hello123 psql -U fusion_admin -h 127.0.0.1 -d postgres -c "CREATE DATABASE fusionlab;" && \
PGPASSWORD=hello123 psql -U fusion_admin -h 127.0.0.1 -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE fusionlab TO fusion_admin;" && \
PGPASSWORD=hello123 psql -U fusion_admin -h 127.0.0.1 -d fusionlab -f ./fusionlab.sql
```
