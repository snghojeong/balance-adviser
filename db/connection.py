import util
import time
import re
import ast
import pymysql
import ConfigParser
from src import logger
#from cassandra.auth import PlainTextAuthProvider
#from cassandra.cluster import Cluster, Session
#from cassandra.policies import RoundRobinPolicy


class MySQLWrap(object):
    def __init__(self, app):
        self.con = None
        self.app = app

    def __del__(self):
        self._closeImpl()

    def connect(self):
        if self.con:
            self._closeImpl()

        self._connectImpl()

    @staticmethod
    def execute(app, query, commit=False):
        try:
            mysql_pre = app.app_ctx_globals_class.mysql
            assert mysql_pre
        except Exception as ex:
            mysql_pre = app.app_ctx_globals_class.mysql = MySQLWrap(app)

        retry_count = 0
        connected = mysql_pre.con is not None
        if connected == True:
            if str(mysql_pre.con.db).endswith("log") == True:
                try:
                    mysql = app.app_ctx_globals_class.mysql = MySQLWrap(app)
                    assert mysql
                except Exception as ex:
                    mysql = app.app_ctx_globals_class.mysql
                finally:
                    connected = mysql.con is not None
            else:
                mysql = mysql_pre
        else:
            mysql = app.app_ctx_globals_class.mysql = MySQLWrap(app)

        while True:
            try:
                retry_count += 1
                if not connected:
                    mysql.connect()
                    connected = True

                cursor = mysql.con.cursor()
                cursor.execute(query)
                if commit:
                    mysql.con.commit()
                else:
                    mysql.con.rollback()
                return cursor

            except pymysql.MySQLError as err:
                logger.writeLog(0, "MySQL Error code : %s" %
                                (str(err.args[0]),))
                if isinstance(err, pymysql.OperationalError):
                    if retry_count >= 3:
                        logger.writeLog(0, "We tried three times.")
                        raise RuntimeError("Connection Failed!")
                    connected = False
                    sleep_time = 2
                    logger.writeLog(
                        3, "Sleep %d seconds before trying reconnect." % (sleep_time,))
                    time.sleep(sleep_time)
                else:
                    logger.writeException(err)
                    raise err

            except Exception as ex:
                raise ex[1] if len(ex) > 1 else ex


    def _connectImpl(self):
        if self.con:
            self._closeImpl()

        db_config_str = self.app.iniconfig.get('db', 'connection')
        db_config = ast.literal_eval(
            '{\''+re.sub('=', '\':\'', re.sub(';', '\',\'', db_config_str))+'\'}')
        try:
            db_config['CONNECTION_CHIPER']
        except:
            db_config['CONNECTION_CHIPER'] = 1

        db_config['PWD'] = db_config['PWD'] if int(
            db_config['CONNECTION_CHIPER']) == 1 else util.decryptString(db_config['PWD'])
        if db_config['PWD'] == -1:
            raise AttributeError("Password Error", 1)
        db_config['UID'] = db_config['UID'] if int(
            db_config['CONNECTION_CHIPER']) == 1 else util.decryptString(db_config['UID'])
        if db_config['UID'] == -1:
            raise AttributeError("UID Error", 1)

        logger.writeLog(1, "DB Connection Start ({0}).".format(
            db_config['DATABASE']))
        self.con = pymysql.connect(host=db_config['SERVER'],
                                   user=db_config['UID'],
                                   passwd=db_config['PWD'],
                                   db=db_config['DATABASE'],
                                   port=int(db_config['PORT']),
                                   charset='utf8mb4')
        self.con.autocommit(True)
        logger.writeLog(
            1, "DB Connection Succesful. ({0})".format(self.con.db))

    def _closeImpl(self):
        if self.con:
            try:
                self.con.close()
            except Exception as ex:
                pass
            logger.writeLog(
                3, "DB Connection Close. ({0})".format(self.con.db))
            self.con = None


class MySQLLogWrap(object):
    def __init__(self, app):
        self.con = None
        self.app = app

    def __del__(self):
        self._closeImpl()

    def connect(self):
        if self.con:
            self._closeImpl()
        self._connectImpl()

    def disconnect(self):
        if self.con:
            self._closeImpl()

    @staticmethod
    def execute(app, query, commit=False):
        try:
            mysql_pre = app.app_ctx_globals_class.mysql
            assert mysql_pre
        except Exception as ex:
            mysql_pre = app.app_ctx_globals_class.mysql = MySQLLogWrap(app)

        retry_count = 0
        connected = mysql_pre.con is not None
        if connected == True:
            if str(mysql_pre.con.db).endswith("log") == False:
                try:
                    mysql = app.app_ctx_globals_class.mysql = MySQLLogWrap(app)
                    assert mysql
                except Exception as ex:
                    mysql = app.app_ctx_globals_class.mysql
                finally:
                    connected = mysql.con is not None
            else:
                mysql = mysql_pre
        else:
            mysql = app.app_ctx_globals_class.mysql = MySQLLogWrap(app)

        while True:
            try:
                retry_count += 1
                if not connected:
                    mysql.connect()
                    connected = True

                cursor = mysql.con.cursor()
                cursor.execute(query)
                if commit:
                    mysql.con.commit()
                else:
                    mysql.con.rollback()
                return cursor

            except pymysql.MySQLError as err:
                logger.writeLog(0, "MySQL Error code : %s" %
                                (str(err.args[0]),))
                if isinstance(err, pymysql.OperationalError):
                    if retry_count >= 3:
                        logger.writeLog(0, "We tried three times.")
                        raise RuntimeError("Connection Failed!")
                    connected = False
                    sleep_time = 2
                    logger.writeLog(
                        3, "Sleep %d seconds before trying reconnect." % (sleep_time,))
                    time.sleep(sleep_time)
                else:
                    logger.writeException(err)
                    raise err
            except Exception as ex:
                raise ex[1] if len(ex) > 1 else ex

    @staticmethod
    def endConnection(app, commit=False):
        try:
            mysql_pre = app.app_ctx_globals_class.mysql
            assert mysql_pre
        except Exception as ex:
            mysql_pre = app.app_ctx_globals_class.mysql = MySQLLogWrap(app)

        try:
            mysql_pre.disconnect()
        except pymysql.MySQLError as err:
            logger.writeLog(0, "MySQL endConnection Error code : %s" %
                            (str(err.args[0]),))

    def _connectImpl(self):
        if self.con:
            self._closeImpl()

        db_config_str = self.app.iniconfig.get('log_db', 'connection')
        db_config = ast.literal_eval(
            '{\''+re.sub('=', '\':\'', re.sub(';', '\',\'', db_config_str))+'\'}')
        try:
            db_config['CONNECTION_CHIPER']
        except:
            db_config['CONNECTION_CHIPER'] = 1

        db_config['PWD'] = db_config['PWD'] if int(
            db_config['CONNECTION_CHIPER']) == 1 else util.decryptString(db_config['PWD'])
        if db_config['PWD'] == -1:
            raise AttributeError("Password Error", 1)
        db_config['UID'] = db_config['UID'] if int(
            db_config['CONNECTION_CHIPER']) == 1 else util.decryptString(db_config['UID'])
        if db_config['UID'] == -1:
            raise AttributeError("UID Error", 1)

        logger.writeLog(1, "DB Connection Start ({0}).".format(
            db_config['DATABASE']))
        self.con = pymysql.connect(host=db_config['SERVER'],
                                   user=db_config['UID'],
                                   passwd=db_config['PWD'],
                                   db=db_config['DATABASE'],
                                   port=int(db_config['PORT']),
                                   charset='utf8mb4')
        self.con.autocommit(True)
        logger.writeLog(1, "DB Connection Succesful. ({0})".format(
            db_config['DATABASE']))

    def _closeImpl(self):
        if self.con:
            try:
                self.con.close()
            except Exception as ex:
                pass
            logger.writeLog(
                3, "DB Connection Close. ({0})".format(self.con.db))
            self.con = None


class MySQLSingleSystemWrap:
    def __init__(self):
        self.con = None
        self.defaultDB = None

    def __del__(self):
        self._closeImpl()

    def connect(self, iniconfig, targetdb=None):
        if self.con:
            self._closeImpl()

        self._connectImpl(iniconfig, targetdb)

    def disconnect(self):
        if self.con:
            self._closeImpl()

    @staticmethod
    def execute(self, query, iniconfig, targetdb=None, commit=False):
        retry_count = 0
        while True:
            try:
                retry_count += 1
                if not self.con:
                    self.connect(iniconfig, targetdb)
                    connected = True

                cursor = self.con.cursor()
                self.con.begin()
                cursor.execute(query)
                if commit:
                    self.con.commit()
                else:
                    self.con.rollback()
                returnData = cursor.fetchall()
                self.disconnect()
                return returnData

            except pymysql.MySQLError as err:
                logger.writeLog(0, "MySQL Error code : %s" %
                                (str(err.args[0]),))
                if isinstance(err, pymysql.OperationalError):
                    if retry_count >= 3:
                        logger.writeLog(
                            0, "We tried three times in MySQLSingleSystemWrap.")
                        raise RuntimeError("Connection Failed!")
                    connected = False
                    sleep_time = 2
                    logger.writeLog(
                        3, "Sleep %d seconds before trying reconnect." % (sleep_time,))
                    time.sleep(sleep_time)
                else:
                    logger.writeException(err)
                    raise err
            except Exception as ex:
                raise ex[1] if len(ex) > 1 else ex

    def _connectImpl(self, iniconfig, targetdb=None):
        if self.con:
            self._closeImpl()

        if targetdb == 2:
            db_config_str = iniconfig.get('log_db', 'connection')
        else:
            db_config_str = iniconfig.get('db', 'connection')

        db_config = ast.literal_eval(
            '{\''+re.sub('=', '\':\'', re.sub(';', '\',\'', db_config_str))+'\'}')
        try:
            db_config['CONNECTION_CHIPER']
        except:
            db_config['CONNECTION_CHIPER'] = 1

        db_config['PWD'] = db_config['PWD'] if int(
            db_config['CONNECTION_CHIPER']) == 1 else util.decryptString(db_config['PWD'])
        if db_config['PWD'] == -1:
            raise AttributeError("Password Error", 1)
        db_config['UID'] = db_config['UID'] if int(
            db_config['CONNECTION_CHIPER']) == 1 else util.decryptString(db_config['UID'])
        if db_config['UID'] == -1:
            raise AttributeError("UID Error", 1)

        if targetdb == 1 or targetdb == 2:
            self.defaultDB = db_config['DATABASE']
            targetdb = self.defaultDB
        else:
            self.defaultDB = "information_schema"
            targetdb = self.defaultDB

        logger.writeLog(1, "DB Connection Start ({0}).".format(targetdb))
        self.con = pymysql.connect(host=db_config['SERVER'],
                                   user=db_config['UID'],
                                   passwd=db_config['PWD'],
                                   db=targetdb,
                                   port=int(db_config['PORT']),
                                   charset='utf8')
        self.con.autocommit(True)
        logger.writeLog(
            1, "DB Connection Succesful. ({0})".format(self.con.db))

    def _closeImpl(self):
        if self.con:
            try:
                self.con.close()
            except Exception as ex:
                pass
            logger.writeLog(
                1, "DB Connection Close. ({0})".format(self.con.db))
            self.con = None

# class CassandraWrap(object):
#    def __init__(self, app):
#        self.con = None
#        self.session = None
#        self.app = app

#    def __del__(self):
#        self._closeImpl()

#    def connect(self):
#        if self.con:
#            self._closeImpl()

#        self._connectImpl()

#    @staticmethod
#    def execute(app, query, Paremeters=None):
#        return CassandraWrap._execute_impl(app, query, Session.execute, Paremeters)

#    @staticmethod
#    def execute_async(app, query, Parameters=None):
#        return CassandraWrap._execute_impl(app, query, Session.execute_async, Parameters)

#    @staticmethod
#    def _execute_impl(app, query, function, Parameters=None):
#        try:
#            cassandra = app.app_ctx_globals_class.cassandra
#            assert cassandra
#        except Exception as ex:
#            cassandra = app.app_ctx_globals_class.cassandra = CassandraWrap(app)

#        retry_count = 0
#        connected = cassandra.con is not None
#        while True:
#            try:
#                retry_count += 1
#                if not connected:
#                    cassandra.connect()
#                    connected = True

#                return function(cassandra.session, query, Parameters)

#            except Exception as err:
#                logger.writeException(err)
#                if retry_count >= 3:
#                    logger.writeLog(0, "We tried three times.")
#                    raise RuntimeError("Connection Failed!")
#                connected = False
#                sleep_time = 2
#                logger.writeLog(3, "Sleep %d seconds before trying reconnect." % (sleep_time,))
#                time.sleep(sleep_time)


#    def _connectImpl(self):
#        if self.con:
#            self._closeImpl()

#        cassandra_nodes_str = self.app.iniconfig.get('log_db', 'node')
#        cassandra_nodes = ast.literal_eval('[\''+re.sub(',', '\',\'', cassandra_nodes_str)+'\']')

#        logger.writeLog(3, "Log DB Connection Start.")
#        self.con = Cluster(cassandra_nodes,
#                           auth_provider=PlainTextAuthProvider(
#                               username=self.app.iniconfig.get('log_db', 'username'),
#                               password=self.app.iniconfig.get('log_db', 'password')),
#                           protocol_version=4,
#                           connect_timeout=self.app.iniconfig.getint('log_db', 'conn_timeout'),
#                           load_balancing_policy=RoundRobinPolicy())

#        database_name = self.app.iniconfig.get('log_db', 'database')\
#        if self.app.config.get('LOG_DB_NAME', None) is None\
#        else self.app.config['LOG_DB_NAME']
#        self.session = self.con.connect(database_name)

#        logger.writeLog(3, "Log DB Connection Succesful.")

#    def _closeImpl(self):
#        if self.session:
#            try:
#                self.session.shutdown()
#            except Exception as ex:
#                pass
#            self.session = None

#        if self.con:
#            try:
#                self.con.shutdown()
#            except Exception as ex:
#                pass
#            logger.writeLog(3, "Log DB Connection Close.")
#            self.con = None
