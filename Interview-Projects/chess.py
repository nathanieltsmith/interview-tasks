#!/usr/bin/python
import sys

columnSize = 8
rowSize = 8


"""
This code is a response to the following program and was done in a timed environment

Write a command line program in whatever language you feel comfortable with – I should be able to run it on a Mac:
Input: a list of space separated numbers, each 0-63. The first number is the position of a knight on a chess board. Subsequent
numbers are the positions of one or more pawns on the chessboard
Output: a sequence of legal moves the knight makes to go and capture all the pawns. The moves can be output as a sequence of
numbers representing squares on the chessboard.
Numbers relate to squares on the board, where
0 is a1
1 is b1
…
8 is a2
….
63 is h8
in normal chess notation.
A chess board is notated as follows:
8
7
6
5
4
3
2
1 
   A  B  C  D  E  F  G  H
"""



""" Given a chess piece and a list of pawns return all of the fastest ways that piece can capture all of the pawns
	start - the starting position of the piece given by an integer.  Must be between 0 and rowLength * colLength -1
	pawns - a list of the location of all of the pawns
	moveFunc - a function that describes the movement of the piece.  See knightMove for a prototype
	rowLength, colLength - The dimensions of the board (usually 8 x 8 for a typical Chess board)
 	"""
def chessSearch(start, pawns, moveFunc, rowLength, colLength):
			dTable = createDistanceTable(start, moveFunc, pawns, rowLength, colLength)
			begin = [start]
			searchFunc = lambda x,y: dTable[str(x) +'to'+str(y)]
			masterList = []
			traverse(begin, pawns, 0, searchFunc, masterList)
			return minDist(masterList)

"""Returns all of the legal moves for a knight given a starting square"""
def knightMove(square, rowLength, colLength):
	column = square % rowLength
	row = int((square - column)/rowLength)
	legalMoves = [x[0] * rowLength + x[1] for x in
	    [[row + 2, column + 1],
             [row + 2, column - 1],
             [row - 2, column + 1],
             [row - 2, column - 1],
             [row + 1, column + 2],
             [row + 1, column - 2],
             [row - 1, column + 2],
             [row - 1, column - 2]] if (x[0] >= 0) and (x[0] < colLength) and (x[1] >= 0) and (x[1] < rowLength) ]
	return legalMoves

""" Check to see if list1 is a subset of list2 """
def sublist(list1, list2):
    set1 = frozenset(list1)
    set2 = frozenset(list2)
    return set2 <= set1

"""Helper Function for the Distance Table"""
def nextdegree(num, prev, moveNetwork):
	degree = set([])
	for y in [moveNetwork[x] for x in prev]:
		for x in y:
			degree.add(x)
	return degree

"""Helper Function for the Distance Table"""
def allreachable(start, moveFunc, pawns, rowLength, colLength):
	moveNetwork = [moveFunc(x,rowLength,colLength) for x in range(rowLength * colLength)]
	pawnSet = frozenset(pawns)
	degree = moveNetwork[start]
	allreachable = set(degree)
	degNum = 1
	while (len(allreachable) < 64):
		degNum = degNum + 1
		degree = nextdegree(degNum, degree, moveNetwork)
		pawnsReachable = degree.intersection(pawnSet)
		allreachable = allreachable.union(degree)
	return degNum

"""Helper Function for the Distance Table"""
def fillDistanceTable(start, distTable, moveFunc, pawns, rowLength, colLength):
	moveNetwork = [moveFunc(x,rowLength, colLength) for x in range (rowLength * colLength)]
	pawnSet = set(pawns)
	degree = set(moveNetwork[start])
	allreachable = set(degree)
	degNum = 1
	pawnsReachable = degree.intersection(pawnSet)
	for x in pawnsReachable:
		distTable[str(start) + 'to'+ str(x)] = degNum
		distTable[str(x) + 'to' + str(start)] = degNum
	pawnSet = pawnSet - pawnsReachable
	while (len(allreachable) < 64):
		degNum = degNum + 1
		degree = nextdegree(degNum, degree, moveNetwork)
		pawnsReachable = degree.intersection(pawnSet)
		for x in pawnsReachable:
			distTable[str(start) + 'to'+ str(x)] = degNum
			distTable[str(x) + 'to' + str(start)] = degNum
		pawnSet = pawnSet - pawnsReachable
		allreachable = allreachable.union(degree)
	return distTable

""" Creates a table of the distances between squares in terms of the number of moves"""
def createDistanceTable(start, moveFunc, pawns, rowLength, colLength):
	distTable = dict()
	fillDistanceTable(start, distTable, moveFunc, pawns, rowLength, colLength)
	for x in pawns:
		fillDistanceTable(x, distTable, moveFunc, pawns, rowLength, colLength)
	return distTable


def minDist(paths):
              minDist = min([x[1] for x in paths])
              return [x for x in paths if x[1] == minDist]

""" Helper function for chessSearch"""
def traverse(path, remaining, dist, distFunc, masterList):
	if len(remaining) > 0:
		for x in remaining:
			traverse(path[:] + [x], [y for y in remaining if y != x], dist + distFunc(path[-1] ,x), distFunc, masterList)
	else:
		masterList.append([path, dist])
		
""" Returns the quickest from point a to point b by a piece described by moveFunc on a rowLength * colLength board"""
def connectPoints(a, b , moveFunc, rowLength, colLength):
	moveNetwork = [moveFunc(x,rowLength,colLength) for x in range(rowLength * colLength)]
	paths = [[a]]
	while len([x for x in paths if x[-1] == b]) == 0:
		paths = [x + [y] for x in paths for y in moveNetwork[x[-1]]]
	return [x for x in paths if x[-1] == b][0]

""" Returns the quickest path for moving through a set of points in order"""
def constructPath(points, moveFunc, rowLength, colLength):
	path = [points[0]]
	for x in range(len(points)-1):
		path = path + connectPoints(points[x], points[x+1], moveFunc, rowLength, colLength)[1:]
	return path

if len(sys.argv)<3:
	print("Please enter a series of numbers to designate pawn positions")
else:
	startPosition = int(sys.argv[1])
	pawns = [int(x) for x in sys.argv[2:] if int(x) < columnSize * rowSize - 1 and int(x) >= 0]
	minList = chessSearch(startPosition, pawns, knightMove, rowSize, columnSize)
	"""we only return one solution because"""
	for x in (constructPath(minList[0][0], knightMove, rowSize, columnSize))[1:]:
		print(x)