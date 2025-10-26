import psycopg2
import sqlalchemy as sa
import pandas as pd

class DB_PGSQL:
    """
    Simple connection handler to postgres database.
    DB object is initialised with a "connection" object from "creds"
    Normally, we should be able to use 
        db.read_sql(sql_query) to generate a pd dataframe
        db.upsert_df(data_frame, table_name, match_columns=None, schema=None, to_sql_kwargs={})
    Modelled by A Bonizec & L Guicheteau     
    """
    
    def __init__(self, conn, schema, env_suffix, port = None, application_name = None, verbose = True):
        self.connection = None
        self._engine = None
        self._cursor = None
        self.conn = conn
        self.schema = schema
        self.env_suffix = env_suffix
        self.port = 5432 if port is None else port
        self.application_name = application_name
        self.verbose = verbose

    def set_con(self, conn):
        self.connection = conn
        return self.connection

    def connect(self):

        keepalive_kwargs = {
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 5,
            "keepalives_count": 5,
        }
        
        try:
            if self.application_name != None:
                self.set_con(psycopg2.connect(host = self.conn.host, database = self.schema, user = self.conn.login, password = self.conn.password, port = self.port, application_name = self.application_name, **keepalive_kwargs))
            else:
                self.set_con(psycopg2.connect(host = self.conn.host, database = self.schema, user = self.conn.login, password = self.conn.password, port = self.port, **keepalive_kwargs))
            if self.connection.closed == 0:
                cursor = self.connection.cursor()
                cursor.execute("SELECT version();")
                record = cursor.fetchone()
                cursor.close()
                if self.verbose:
                    print("Connected to PostgreSQL Server version", record)
                    print("You're connected to database:", self.schema)

        except Exception as e:
            print("Error while connecting to PostgreSQL", e)
            
        return self.connection
           
    def create_engine(self, echo = False):
        if self.application_name is None:
            self.set_engine(sa.create_engine("postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}".format(user = self.conn.login, pw = self.conn.password, host = self.conn.host, port = self.port, db = self.schema), echo = echo))
        else:
            self.set_engine(sa.create_engine("postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}".format(user = self.conn.login, pw = self.conn.password, host = self.conn.host, port = self.port, db = self.schema), echo = echo, connect_args = {"application_name": self.application_name}))
        return self._engine

    def set_engine(self, engine):
        self._engine = engine
        return self._engine

    def get_engine(self):
        if self._engine is not None:
            return self._engine
        else:
            return self.create_engine()

    def del_engine(self):
        self._engine = None

    def get_con(self):
        if self.con_opened:
            return self.connection
        else:
            return self.connect()

    def del_con(self):
        if self.con_opened:
            self.connection.close()
        self.connection = None

    def set_cursor(self, cursor):
        self._cursor = cursor
        return self._cursor

    def get_cursor(self):
        del self.cursor
        return self.set_cursor(self.con.cursor())

    def del_cursor(self):
        if self.cursor_opened:
            self._cursor.close()
        self._cursor = None

    def get_columns(self, query, keep_alive = False):
        cur = self.exec_sql(query + " LIMIT 0", keep_alive)
        return [desc.name for desc in cur.description]

    def read_sql(self, query, keep_alive = False):
        try:
            z = pd.read_sql(query, con = self.con)
        except Exception as e:
            print("[PGS ERROR]", e)
            print("Warning: this query doesn't yield any result, please use exec_sql instead")
            z = None
        if not keep_alive:
            self.close()
        return z

    def query_in_chunks(self, query, chunk_size = 10000, keep_alive = False):
        """
        Retrieve data from a PostgreSQL database in chunks using a cursor.
        :param query: The SQL query to execute
        :param chunk_size: The number of rows to retrieve in each chunk
        :param keep_alive: Keep the connection alive or close it after the data is fetched
        :return: A generator that yields chunks of data
        """
        # Create a cursor for the database connection
        with self.cursor as cur:
            print("Query execution starting...")

            # Execute the query
            cur.execute(query)

            print("Query execution finished, retrieving data...")

            while True:
                # Fetch the next chunk of data
                chunk = cur.fetchmany(chunk_size)

                # If the chunk is empty, we have reached the end of the data
                if not chunk:
                    break

                # Yield the chunk
                yield chunk
                del chunk

        if not keep_alive:
            self.close()

    def upsert_df(self, data_frame, table_name, match_columns=None, schema=None, to_sql_kwargs={}):
        """
        Performs an "upsert" on a PostgreSQL table from a DataFrame.
        Constructs an INSERT … ON CONFLICT statement, uploads the DataFrame to a
        temporary table, and then executes the INSERT.
        Parameters
        ----------
        data_frame : pandas.DataFrame
            The DataFrame to be upserted.
        table_name : str
            The name of the target table.
        match_columns : list of str, optional
            A list of the column name(s) on which to match. If omitted, the
            primary key columns of the target table will be used.
        schema : str, optional
            The name of the schema containing the target table.
        """
        table_spec = ""
        if schema:
            table_spec += '"' + schema.replace('"', '""') + '".'
        table_spec += '"' + table_name.replace('"', '""') + '"'

        df_columns = list(data_frame.columns)
        if not match_columns:
            insp = sa.inspect(self.engine)
            match_columns = insp.get_pk_constraint(table_name, schema=schema)[
                "constrained_columns"
            ]
        columns_to_update = [col for col in df_columns if col not in match_columns]
        insert_col_list = ", ".join([f'"{col_name}"' for col_name in df_columns])
        stmt = f"INSERT INTO {table_spec} ({insert_col_list})\n"
        temp_table_name = "tmp_" + table_name
        stmt += f"SELECT {insert_col_list} FROM {temp_table_name}\n"
        match_col_list = ", ".join([f'"{col}"' for col in match_columns])
        stmt += f"ON CONFLICT ({match_col_list}) DO UPDATE SET\n"
        stmt += ", ".join(
            [f'"{col}" = EXCLUDED."{col}"' for col in columns_to_update]
        )

        with self.engine.begin() as conn:
            conn.execute("DROP TABLE IF EXISTS " + temp_table_name)
            conn.execute(
                f"CREATE TEMPORARY TABLE {temp_table_name} AS SELECT * FROM {table_spec} WHERE FALSE"
            )
            data_frame.to_sql(temp_table_name, conn, if_exists="append", index=False, **to_sql_kwargs)
            conn.execute(stmt)

    # functions for raw data (no pandas involved)
    def upsert_raw(self, data, column_names, table_name, match_columns=None, schema=None):
        """
        Performs an "upsert" on a PostgreSQL table from raw data: list of tuples (1 tuple = 1 row).
        Constructs an INSERT … ON CONFLICT statement, and uploads data row by row.
        Parameters
        ----------
        data : data in the form of a matrix
            The Data to be upserted.
        column_names: list
            The column names.
        table_name : str
            The name of the target table.
        match_columns : list of str, optional
            A list of the column name(s) on which to match. If omitted, the
            primary key columns of the target table will be used.
        schema : str, optional
            The name of the schema containing the target table.
        """

        if len(data) < 1:
            return False

        if len(data[0]) != len(column_names):
            print("Invalid number of columns", len(data[0]), "vs", len(column_names))
            return False

        table_spec = ""
        if schema:
            table_spec += '"' + schema.replace('"', '""') + '".'
        table_spec += '"' + table_name.replace('"', '""') + '"'

        df_columns = column_names
        if not match_columns:
            insp = sa.inspect(self.engine)
            match_columns = insp.get_pk_constraint(table_name, schema=schema)[
                "constrained_columns"
            ]
        columns_to_update = [col for col in df_columns if col not in match_columns]
        insert_col_list = ", ".join([f'"{col_name}"' for col_name in df_columns])
        insert_col_list_placeholder = ", ".join([f'%s' for col_name in df_columns])
        stmt = f"INSERT INTO {table_spec} ({insert_col_list})\n"
        stmt += f"VALUES ({insert_col_list_placeholder})\n"
        match_col_list = ", ".join([f'"{col}"' for col in match_columns])
        stmt += f"ON CONFLICT ({match_col_list}) DO UPDATE SET\n"
        stmt += ", ".join(
            [f'"{col}" = EXCLUDED."{col}"' for col in columns_to_update]
        )

        with self.engine.begin() as conn:
            for row in data:
                conn.execute(stmt, tuple(row))

    def exec_sql(self, query, params=None, keep_alive=False):
        with self.cursor as cur:
            try:
                # Use the parameterized query if params are provided
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
            except Exception as e:
                print("Error in PostgreSQL query:", e)
                self.con.rollback()  # Roll back the transaction on error
                raise  # Re-raise the exception for visibility
            else:
                self.con.commit()  # Commit only if no errors occurred
            if not keep_alive:
                self.close()
            return cur

    def to_sql(self, df, table_name, **kwargs):
        """
        Write records stored in a DataFrame to a SQL database.
        Parameters:
            df (pd.DataFrame): DataFrame to write.
            table_name (str): Name of the target table.
            kwargs: Additional arguments for pandas.DataFrame.to_sql.
        """
        with self.engine.begin() as conn:
            try:
                # Use schema from kwargs if provided; fall back to self.schema if not.
                schema = kwargs.pop('schema', self.schema)
                df.to_sql(table_name, conn, schema=schema, **kwargs)
            except Exception as e:
                print("Error exporting the data:", e)


    def cursor_is_opened(self):
        """
        To fully close this connection instance, use the function db.close().
        """
        return self._cursor is not None and not self._cursor.closed

    def con_is_opened(self):
        """
        To fully close this connection instance, use the function db.close().
        """
        return self.connection is not None and self.connection.closed == 0

    def close(self):
        """
        Fully close everything (cursor + connection) that is still opened.
        For good practice, call this function at the end of your script.
        """
        del self.cursor
        del self.con

    def __repr__(self):
        return f"<DB_PGSQL(postgresql+psycopg2://{self.conn.login}:***@{self.conn.host}:{self.port}/{self.schema}) - opened connection: {self.con_opened}, opened cursor: {self.cursor_opened}>"

    # Returns whether the instance cursor is still opened or not.
    # Important: don't forget to close the cursor after use (del db.cursor or db.close()).
    # -> This can block other queries from executing while it is opened.
    cursor_opened = property(cursor_is_opened)

    # Returns whether the instance connection is still opened or not.
    con_opened = property(con_is_opened)

    # sqlalchemy engine -> used mostly for exotic exports, for simple exports use .to_sql()
    engine = property(get_engine, set_engine, del_engine)

    # psycopg2 connection object -> used for everything
    con = property(get_con, set_con, del_con)

    # psycopg2 connection cursor -> used mostly to fetch big data in chunks
    cursor = property(get_cursor, set_cursor, del_cursor)


def store_sql(df, db, table_name, mode='append', chunksize=50000, match_columns=[], index_columns=[]):
    """
    Store a DataFrame into a SQL database table with flexible modes of operation.

    Parameters:
        df (pd.DataFrame): The DataFrame to store in the SQL database.
        db (DB_PGSQL): An instance of the database interface class with methods like `to_sql`, `upsert_df`, and `exec_sql`.
        table_name (str): The name of the target table in the database.
        mode (str, optional): The mode of operation for storing the data. Can be one of:
            - 'append': Adds the data to the table without removing existing data.
            - 'upsert': Updates existing rows in the table based on match_columns; inserts new rows otherwise.
            - 'overwrite': Deletes the table if it exists and recreates it before inserting the data.
        chunk_size (int, optional): The number of rows to write at a time for performance. Defaults to 50,000.
        match_columns (list, optional): Columns to use for matching rows during upsert. Required if mode is 'upsert'.
        index_columns (list, optional): Columns to create indexes on after data insertion. Defaults to an empty list.

    Raises:
        ValueError: If an unsupported mode is provided.

    Example:
        store_sql(my_dataframe, my_db_instance, 'my_table', mode='overwrite', chunk_size=10000)
    """
    if mode == 'append':
        db.to_sql(df, table_name, if_exists='append', index=False, chunksize=chunksize, method='multi', schema='public')
    elif mode == 'upsert':
        if not match_columns:
            raise ValueError("match_columns must be specified when mode='upsert'")
        db.upsert_df(df, table_name, match_columns=match_columns)
    elif mode == 'overwrite':
        db.to_sql(df, table_name, if_exists='replace', index=False, chunksize=chunksize, method='multi', schema='public')  # Recreate and insert data
    else:
        raise ValueError(f"Unsupported mode: {mode}. Use 'append', 'upsert', or 'overwrite'.")

    # Create indexes if index_columns is provided
    if index_columns:
        for column in index_columns:
            try:
                index_name = f"{table_name}_{column}_idx"
                create_index_stmt = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column});"
                db.exec_sql(create_index_stmt)
                print(f"Index on '{column}' created successfully.")
            except Exception as e:
                print(f"Failed to create index on '{column}': {e}")