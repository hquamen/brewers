####################################################
#
#	This is a module to help calculate similarity
#	scores between two different individuals in
#	the apprenticeship records.
#
####################################################


import math
from statistics import mean
import editdistance as ed

#
#	CONSTANTS
#

#	Standard Deviations for Gaussian curves
APPRENTICE_STANDARD_DEVIATION = 1.0
MASTER_STANDARD_DEVIATION = 6.2		# based on Pynder's apprenticeship SNA tree
MASTER_AVG_AGE = 42.4				# based on Pynder's apprenticeship tree
FATHER_STANDARD_DEVIATION = 10.0

#	How close to get on numerical solution?
# 	(trial and error established this)
DELTA_THRESHOLD = 0.006

#	+/- window on years to check;
#	- the min date, + the max date
WINDOW = 10

#	Birthdates of two people are too far apart at:
BIRTHDATE_MISMATCH = 100

#	Edit distance threshold; must be <= this:
EDIT_THRESHOLD = 2

#	Similarity threshold; must be greater than this:
SIMILARITY_THRESHOLD = 0.4



####################################################
#
#	FUNCTIONS
#
####################################################

def get_year_interval(x1, x2):
	start = min([x1, x2]) - WINDOW
	stop = max([x1, x2]) + WINDOW
	return start, stop

def gauss(x, birthyear, std_deviation):
	num = - (x - birthyear) ** 2
	denom = 2 * std_deviation ** 2
	return math.exp(num/denom)

def similarity(apprentice_estimated_birthdate, father_estimated_birthdate):
	best_year = None
	similarity_score = -1e6
	delta_at_year = None

	min_year_to_check, max_year_to_check = get_year_interval(apprentice_estimated_birthdate, father_estimated_birthdate)
	for x in range(min_year_to_check * 100, max_year_to_check * 100):
		year = x / 100
		y1 = gauss(year, apprentice_estimated_birthdate, APPRENTICE_STANDARD_DEVIATION)
		# y2 = gauss(year, father_estimated_birthdate, FATHER_STANDARD_DEVIATION)
		y2 = gauss(year, father_estimated_birthdate, MASTER_STANDARD_DEVIATION)
		delta = abs(y1 - y2)
		if delta < DELTA_THRESHOLD:
			avg = mean([y1, y2])
			if avg > similarity_score:
				best_year = year
				similarity_score = avg
				delta_at_year = delta
	return similarity_score, best_year


