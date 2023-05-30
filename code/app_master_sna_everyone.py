#################################################################
#
#	Brewers' Prosopography Project
#	H. Quamen
#	Spring 2023
#
#	Find the social network of apprentices who also later
#	served as master to subsequent generations of apprentices.
#
#	Input:
#		-- CSV_INPUT below
#	Output:
#		-- creates a directory inside OUTPUT_DIR for each 
#			apprentice who has a social network >= 2. The sub-
#			directory is named after the person plus the
#			year of their own apprenticeship. Example:
#					Ridgway_1598
#		-- also outputs a CSV file listing every apprentice
#			and how many apprentices + generations they have;
#			see REPORT_CSV below.
#
#################################################################

import similarity as sim 	# custom-written module for Brewers' Project

import csv
import editdistance as ed
import os

CSV_INPUT = "csv/all_records.csv"

OUTPUT_DIR = 'everyone/'


####################################################
#
#	LOAD CSV AND PROCESS
#
####################################################


#
#	Set up output CSV report file
#

REPORT_CSV = "everyone/apprentice_report.csv"
REPORT_HEADERS = ['year', 'last', 'first', 'apprentices', 'generations']

with open(REPORT_CSV, "w") as f:
	csvwriter = csv.writer(f)
	csvwriter.writerow(REPORT_HEADERS)

#
#	input the rows of indenture records
#

with open(CSV_INPUT) as file:
	csvreader = csv.DictReader(file)
	rows = [row for row in csvreader]

#
#	headers for Gephi CSV files
#

NODE_HEADERS = ["Id", "Label", "Apprentice_Id", "Year", "Generation"]
EDGE_HEADERS = ['Id', "Source", "Target", "Weight", "Type"]

WEIGHT = 1
TYPE = 'Directed'

#
#	loop through all the apprenticeship records
#

for outside_row_num, app_to_check in enumerate(rows):

	if outside_row_num % 100 == 0:
		print("\n---- {}".format(outside_row_num))

	start_node = int(app_to_check['apprentice_number'])


	#
	#	set up the stack -- when we find new
	#	apprentices, add them to this list
	#

	stack = []
	edge_id = 0
	node_id = 0
	total_apprentices = 1

	node_rows = []
	edge_rows = []

	stack.append(app_to_check)

	#
	# append our starting node to the node_rows list for Gephi
	#

	node_id += 1
	app_to_check['node_id'] = node_id	# give it a node_id for the later graph
	app_to_check['generation'] = 0
	label = app_to_check['apprentice_first'] + " " + app_to_check['apprentice_last'] + " (" + app_to_check['year'] + ")"
	app_id = app_to_check['apprentice_number']
	if len(app_to_check['year']) < 1:
		print("No year -- skipping {}".format(label))
		continue
	year = int(app_to_check['year'])
	node_row = [node_id, label, app_id, year, app_to_check['generation']]

	node_rows.append(node_row)

	#
	#	Start the iterative process: pop the next apprentice
	#	off the stack and see if this apprentice ever became
	#	a master; if so, add all his apprentices to the stack
	#	for later checking and add new edges to the edge_row list.
	#
	#	Continue as long as we have apprentices to check.
	#

	while len(stack) > 0:

		# apprentice should already be in the node list, so
		# don't add anything here.

		old_apprentice = stack.pop(0)
		# print("\tStack size: {}".format(len(stack)))

		for row_num, new_apprentice in enumerate(rows):
			
			# sanity checks -- for both master and apprentice;
			# bail on cases we don't need to check.

			if len(old_apprentice['apprentice_name']) < 1:
				# no name
				continue

			if len(old_apprentice['app_birth']) < 1:
				# no birthdate
				continue

			# skip if we're looking at the same new_apprentice
			if old_apprentice == new_apprentice:
				continue

			if len(new_apprentice['apprentice_name']) < 1:
				continue

			if len(new_apprentice['app_birth']) < 1:
				continue

			#
			#	simple sanity checks passed; move to more 
			#	sophisticated checks; these parameters are
			#	housed in the `similarity` module.
			#

			old_app_birthdate = int(old_apprentice['app_birth'])
			new_master_birthdate = int(new_apprentice['master_birth'])

			#
			# test: birthdates too far apart
			#

			if abs(old_app_birthdate - new_master_birthdate) > sim.BIRTHDATE_MISMATCH:
				continue

			#
			# test: edit distance not within appropriate window
			#

			edit_dist = ed.eval(new_apprentice['master_name'], old_apprentice['apprentice_name'])
			if edit_dist >= sim.EDIT_THRESHOLD:
				continue

			#
			# test our similarity scores (max overlap of gaussian birthyear curves)
			#

			similarity_score, best_year = sim.similarity(old_app_birthdate, new_master_birthdate)
			if similarity_score >= sim.SIMILARITY_THRESHOLD:
				# we have a match if we get all the way down here!
				
				# give this apprentice a new node ID for the graph
				node_id += 1
				new_apprentice['node_id'] = node_id
				new_apprentice['generation'] = old_apprentice['generation'] + 1

				# push new apprentice onto stack for later checking
				# to see if they ever became a master . . .
				stack.append(new_apprentice)

				# . . . build the node data for this apprentice . . .
				label = new_apprentice['apprentice_first'] + " " + new_apprentice['apprentice_last'] + " (" +\
					new_apprentice['year'] + ")"
				app_id = new_apprentice['apprentice_number']
				year = int(new_apprentice['year'])
				generation = new_apprentice['generation']
				node_row = [node_id, label, app_id, year, generation]

				# . . . and append this node to the collection, and . . .
				node_rows.append(node_row)

				# . . . also append this edge to the collection.
				edge_id += 1
				source = old_apprentice['node_id']
				target = new_apprentice['node_id']
				new_edge = [edge_id, source, target, WEIGHT, TYPE]

				edge_rows.append(new_edge)
				total_apprentices += 1


	# Done.

	app_report = "---- Total apprentices: {}\n".format(total_apprentices)

	max_generation = max(node_rows, key=lambda x: x[4])[4]
	gen_report = "---- Generation: {}\n".format(max_generation)

	#
	# write the CSV report
	#

	report_row = [app_to_check['year'], app_to_check['apprentice_last'], app_to_check['apprentice_first'],
		total_apprentices, max_generation]
	with open(REPORT_CSV, "a") as f:
		csvwriter = csv.writer(f)
		csvwriter.writerow(report_row)
		report_row = None

	#
	# We'll write the data for Gephi only if 
	# we have two or more generations. 
	#

	if max_generation >= 2:

		#
		#	establish directories and files (overwrite if they exist)
		#

		# mkdir and calculate path to files
		this_dir = OUTPUT_DIR + app_to_check['apprentice_last'] + "_" + app_to_check['year'] + "/"
		if not os.path.exists(this_dir):
			os.makedirs(this_dir)

		node_file = this_dir + 'nodes.csv'
		edge_file = this_dir + 'edges.csv'
		report_file = this_dir + 'report.txt'

		# write to files

		with open(node_file, "w") as f:
			csvwriter = csv.writer(f)
			csvwriter.writerow(NODE_HEADERS)
			csvwriter.writerows(node_rows)

		with open(edge_file, "w") as f:
			csvwriter = csv.writer(f)
			csvwriter.writerow(EDGE_HEADERS)
			csvwriter.writerows(edge_rows)

		with open(report_file, "w") as f:
			f.writelines([app_report, gen_report])
