import json
try:
	import _mysql
	mySQLworks = True
except:
	mySQLworks = False
import time
import StringIO

#tasks
task_insert_customer = "insert_customer"
task_update_customer = "update_customer"

# Customer Fields
cust_name = "name"
cust_company = "company"
cust_phone = "phone"

# Database Connection Details
dbHost = ''
dbUser = ''
dbPwd = ''
dbName = ''

# Database fields for the "queue" table
priority_id = 'priority_id'
task_type = 'task_type'
task_data = 'task_data'
error_type = 'error_type'
status = 'status'

# Used to Test when Database isn't working.
test_records = [
				[(1, 'update_customer', u'[{"name" : "Bill Bradley", "company" : "Boeing"}, ["phone", "322-234-2345"]]', '', 'pending')],
				[(1, 'insert_customer', u'[{"name" : "John Smith"}]', '', 'pending')],
				[(1, 'insert_customer', u'[{"company" : "Boeing"}]', '', 'pending')],
				[(1, 'insert_customer', u'[{"name" : "Bill Bradley", "company" : "Boeing"}]', '', 'pending')]
			    ]


"""
Parent class for creating a handler that takes tasks from a priority queue. 

Works with a queue table in database which must have a 'priority_id', 'status', 'error_type' and 'task_type' columns.  
Columns in addition to these are allowed but the tuple 'queue_fields' must be defined with a list of columns in the order
that they occur in the database.

The run() method goes through the table, getting the highest priority items first (1 = highest possible priority) and
executing the corresponding tasks.  Descendents of this class must define handlers for tasks that they support.

See Snipe_Task_Handler below for an implementation
"""
class Task_Handler():
	def __init__(self):
		if mySQLworks:
			mydbManager = SQL_Database_Manager()
		else:
			mydbManager = Dummy_Database_Manager()
		self.db_manager  = mydbManager
		self.valid_tasks = ()
		self.queue_fields = ()
		
	def run(self):
		while True:
			record = self._get_next_in_queue()
			if record:
				self._mark_as_processing(record)
				if self._valid_record(record):
					self._execute_task(record)
				else:
					self._report_error(record)
			else:
				time.sleep(5)

	"""
	_get_next_in_queue
	This returns a dictionary with values linked to corresponding database field headers
	Preconditions - the global list queue_fields includes the list  of database fields in order 
	"""
	def _get_next_in_queue(self):
		record = self.db_manager.get_next_record()
		task =  {}
		if record:
			for x in enumerate(self.queue_fields):
				task[x[1]] = record[0][x[0]]
		return task
	
	def _mark_as_processing(self, record):
		where_string = " ".join([ '%s="%s" AND ' % (x, record[x]) for x in record])[:-5]
		update_query =  'UPDATE queue SET %s="%s" WHERE %s;' % (status, 'processing', where_string)
		self.db_manager.execute_query(update_query)
		
	def _valid_record(self, record):
		if record[task_type] not in self.valid_tasks:
			record[error_type] = 'Invalid Task'
			return False
		return getattr(self, '_valid_%s' % record[task_type])(record)
	
	def _execute_task(self, record):
		getattr(self, '_execute_%s' % record[task_type])(record)
	
	def _report_error(self, record):
		error_query = 'UPDATE queue SET %s="failed", %s="%s" WHERE %s="pending"' % (status, error_type, record[error_type], status)
		self.db_manager.execute_query(error_query)
	
	"""
	validate()
	Determines whether the task_handler will be able to handle all tasks listed in it's valid_tasks field
	"""
	def validate(self):
		valid = True
		if len(self.valid_tasks) > 0:
			for x in valid_tasks:
				if not hasattr(self, '_execute_%s' % x):
					print "Warning: missing method: _execute_%s" % x
					valid = False
				if not hasattr(self, '_valid_%s' % x):
					print "Warning: missing method: _valid_%s" % x
					valid = False
		else:
			print "Warning: No valid tasks listed"
			valid = False
		return valid

"""
Dummy_Database_Manager
This was created to allow us to test the rest of the code when mySQL bindings aren't installed
"""
class Dummy_Database_Manager():
	def __init__(self):
		print "Initializing Database"
	
	def execute_query(self, query):
		print "Executing Query:\n %s\n" % query
		
	def get_next_record(self):
		print "Getting next record"
		if test_records:
			return test_records.pop()
		else:
			return []

"""
MySQL_Database_Manager
Made to decouple database library specific functions from the rest of the code.
"""		
class MySQL_Database_Manager():
	def __init__(self):
		self._init_database()

	def _init_database(self):
		try:
			self["db"] = _mysql.connect(host=dbHost,user=dbUser, passwd=dbPwd,db=dbName)
		except:
			print "Error %d: %s" % (e.args[0], e.args[1])
			sys.exit(1)
	
	def execute_query(self, query):
		try:
			cur = self.db.cursor()
			cur.execute(query)
		except:
			print "Error %d: %s" % (e.args[0], e.args[1])
			sys.exit(1)

	def get_next_record(self):
		cur = self.db.cursor()
		getNextEntry = "SELECT * FROM queue WHERE STATUS='pending' queue ORDER BY status, priority_id LIMIT 1;"
		cur.execute(searchString)
		return cur.fetchall()
	
"""
Snipe_Task_Handler

This is a task handler that handles two tasks, insert_customer and update_customer.  The data
for the task is passed in through a json list.  Both tasks take as the first parameter, a dictionary of 
values for a customer.  update_customer takes an additional parameter a list that contains a field to change and a 
new value for that field.

[{"name" : "John Smith"}]
[{"name" : "John Smith", "company" : "Boeing"}, ["phone", "319-555-4444"]]
"""
class Snipe_Task_Handler(Task_Handler):

	
	def __init__(self):
		Task_Handler.__init__(self)
		self.valid_tasks = (task_insert_customer, task_update_customer)
		self.queue_fields = (priority_id, task_type, task_data, error_type, status)
		self.valid_cust_fields = (cust_name, cust_company, cust_phone)
	
	def _execute_insert_customer(self, task):
		data = json.load(StringIO.StringIO(task[task_data]))[0]
		if cust_phone not in data:
			data[cust_phone] = "None"
		if cust_company not in data:
			data[cust_company] = "None"
		insert_query = 'INSERT INTO customers (%s, %s, %s) VALUES ("%s", "%s", "%s");' % (cust_name, cust_company, cust_phone, data[cust_name], data[cust_company], data[cust_phone]) 
		self.db_manager.execute_query(insert_query)
		
	def _execute_update_customer(self, task):
		customer = json.load(StringIO.StringIO(task[task_data]))[0]
		change = json.load(StringIO.StringIO(task[task_data]))[1]
		where_string = " ".join(['%s="%s" AND ' % (x, task[x]) for x in task])[:-5]
		update_query =  'UPDATE customers SET %s="%s" WHERE %s;' % (change[0], change[1], where_string)
		self.db_manager.execute_query(update_query)

	def _valid_insert_customer(self, task):
		try:
			customer = json.load(StringIO.StringIO(task[task_data]))[0]
		except:
			task[error_type] = "Improperly Formatted JSON"
			return False
		customer_error =  self._is_not_customer(customer)
		if customer_error:
			task[error_type] = customer_error
			return False
		else:
			return True
	
	def _valid_update_customer(self, task):
		try:
			customer = json.load(StringIO.StringIO(task[task_data]))[0]
			change = json.load(StringIO.StringIO(task[task_data]))[1]
		except:
			task[error_type] = "Improperly Formatted JSON"
			return False
		customer_error =  self._is_not_customer(customer)
		if customer_error:
			task[error_type] = customer_error
			return False
		if len(change) != 2:
			task[error_type] = "Incorrect number of arguments in update value"
			return False
		if change[0] not in self.valid_cust_fields:
			task[error_type] = "%s is not a valid field" % change[0]
			return False
		return True

	"""
	_is_not_customer
	Takes parsed json data.  If it is not appropriately formatted as a customer, it returns a string describing
	the problem.  If the customer is correctly formatted, the empty string is returned.
	"""
	def _is_not_customer(self, cust):
		if not type(cust) is dict:
			return "Invalid Customer (must be a dictionary): " 
		elif cust_name not in cust:
			return "Invalid Customer (must have name field): " 
		else:
			for x in cust.keys():
				if x not in self.valid_cust_fields:
					return "Invalid Field: " + x + " in customer: " + cust[cust_name]
			for y in cust.values():
				if not type(y) is unicode:
					return "Invalid Value: " + y + " for customer " + cust[cust_name]
		return ''

if __name__ == "__main__":
	Snipe_Task_Handler().run()