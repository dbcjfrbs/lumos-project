import pymysql

class MysqlConnector:
	def __init__(self, host, port, schema, user, passwd):
		self.host = host
		self.port = port
		self.schema = schema
		self.user = user
		self.passwd = passwd

	def execsql(self, query):
		conn_flag = 0
		result = None

		try:
			dbconn = pymysql.connect(host=self.host, port=self.port, user=self.user, database=self.schema, password=self.passwd)
			conn_flag = 1
			cur = dbconn.cursor()
			cur.execute(query)
			result = cur.fetchall()
		except pymysql.Error as e:
			print("ERROR(%d) : %s" % (e.args[0], e.args[1]))
		finally:
			if conn_flag == 1:
				conn_flag = 0
				dbconn.close()
			return result

	def execdml(self, query):
		conn_flag = 0
		result = 0

		try:
			dbconn = pymysql.connect(host=self.host, port=self.port, user=self.user, database=self.schema, password=self.passwd)
			conn_flag = 1
			cur = dbconn.cursor()
			result = cur.execute(query)
			dbconn.commit()
		except pymysql.Error as e:
			dbconn.rollback()
			print("ERROR(%d) : %s" % (e.args[0], e.args[1]))
		finally:
			if conn_flag == 1:
				dbconn.close()
			return result
