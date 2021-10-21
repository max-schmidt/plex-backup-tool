class DatabaseObj:
	def __init__(self,conn, cursor_1, cursor_2):
		self.conn = conn
		self.cursor_1 = cursor_1
		self.cursor_2 = cursor_2
		