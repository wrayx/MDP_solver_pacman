# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import math
import random
import game
import time

INITIAL_REWARD = 0.01
INITIAL_REWARD_FOOD = 1.8
INITIAL_REWARD_CAPSULE = 2.0
DIRECTIONS = [Directions.NORTH, Directions.SOUTH, Directions.WEST, Directions.EAST]
ITERATION_THRESHOLD = 0.00001

#
# A class that creates a grid that can be used as a map
#
# The map itself is implemented as a nested list, and the interface
# allows it to be accessed by specifying x, y locations.
#
class Grid:
         
    # Constructor
    #
    # Note that it creates variables:
    #
    # grid:   an array that has one position for each element in the grid.
    # width:  the width of the grid
    # height: the height of the grid
    #
    # Grid elements are not restricted, so you can place whatever you
    # like at each location. You just have to be careful how you
    # handle the elements when you use them.
    def __init__(self, width, height):
        self.width = width
        self.height = height
        subgrid = []
        for i in range(self.height):
            row=[]
            for j in range(self.width):
                row.append(0)
            subgrid.append(row)

        self.grid = subgrid

    # Print the grid out.
    def display(self):       
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[i][j], '\t',
            # A new line after each line of the grid
            print 
        # A line after the grid
        print

    # The display function prints the grid out upside down. This
    # prints the grid out so that it matches the view we see when we
    # look at Pacman.
    def prettyDisplay(self):       
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[self.height - (i + 1)][j],  '\t',
            # A new line after each line of the grid
            print 
        # A line after the grid
        print
        
    # Set and get the values of specific elements in the grid.
    # Here x and y are indices.
    def setValue(self, x, y, value):
        self.grid[y][x] = value

    # set all values from the grid to the same number
    def setAllValue(self, value):
        for i in range(self.height):
            for j in range(self.width):
                self.grid[i][j] = value

    # get value at location (x, y) from the grid
    # if the location value does not exist on grid
    # then 0 is returned
    def getValue(self, x, y):
        value = 0
        try:
            # get value from the left of the state
            y = int(y)
            x = int(x)
            value = self.grid[y][x]
        except:
            value = '%'
            print "Position", x, ",", y, "does not exist"
        return value

    # Return width and height to support functions that manipulate the
    # values stored in the grid.
    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width


class MDPAgent(Agent):


    # Constructor 
    #
    # Note that it creates variables including:
    #
    # an reward assigned when ever pacman stays on the map
    # initial_reward: an reward assigned when ever pacman stays on the map
    # food_reward: reward added to the location that contains food
    # capsule_reward: reward added to the location that contains capsule
    # edible_ghost_reward: reward added to the location that has an edible/scared ghost
    # ghost_reward: a negative reward for location that has an active ghost
    #
    # discount_factor: a number between 0 and 1 that decides 
    # the preference of the agent for current over future rewards
    #
    # iteration_threshold: when the change in values is below this iteration threshold, 
    # stop the iteration
    #
    # self.total_food_num: variable for total number of food on map
    #
    # Grid elements are not restricted, so you can place whatever you
    # like at each location. You just have to be careful how you
    # handle the elements when you use them.
    #
    # this gets run when we first invoke pacman.py
    def __init__(self):

        # time the program for testing
        self.start_time = time.time()
        print "Starting up MDPAgent!"
        name = "Pacman"

        # assign reward values
        # an reward assigned when ever pacman stays on the map
        self.initial_reward=INITIAL_REWARD
        self.food_reward=INITIAL_REWARD_FOOD
        self.capsule_reward=INITIAL_REWARD_CAPSULE
        self.edible_ghost_reward=3.0
        self.ghost_reward=-4

        # assign discount factor
        self.discount_factor=0.8

        # assign iteration threshold
        self.iteration_threshold=ITERATION_THRESHOLD

        # variable for total number of food on map
        self.total_food_num=0

    # The function gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running register InitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)

        # initialise reward value at the start of each run
        self.food_reward=INITIAL_REWARD_FOOD
        self.capsule_reward=INITIAL_REWARD_CAPSULE

        # Make a map of the right size for utlity values
        self.utility_map = self.makeMap(state, initial_value=INITIAL_REWARD)
        self.addWallsToMap(state, self.utility_map)
        self.updateFoodInMap(state, self.utility_map)
        self.updateGhostInMap(state, self.utility_map)
        self.utility_map.prettyDisplay()

        # Make a map of the right size for 
        # direction that gives maximum utility value
        self.direction_map = self.makeMap(state, initial_value="")
        self.addWallsToMap(state, self.direction_map)

        # get the total (initial) number of food from the map
        self.total_food_num = len(api.food(state))
        
    # The function gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"

        # display time for testing
        print"--- ", round((time.time() - self.start_time), 2), " seconds ---"
        print "final food reward = ", self.food_reward

    # Function that makes a map by creating a grid of the right size
    # 
    # an initial value can be assigned to all cells 
    # using the optional parameter 'initial_value'
    def makeMap(self, state, initial_value=INITIAL_REWARD):
        corners = api.corners(state)
        # print corners
        height = self.getLayoutHeight(corners)
        width  = self.getLayoutWidth(corners)
        map = Grid(width, height)
        # First, make all grid elements with an initial value
        map.setAllValue(initial_value)

        return map
        
    # Functions to get the height and the width of the grid.
    #
    # We add one to the value returned by corners to switch from the
    # index (returned by corners) to the size of the grid (that damn
    # "start counting at zero" thing again).
    def getLayoutHeight(self, corners):
        height = -1
        for i in range(len(corners)):
            if corners[i][1] > height:
                height = corners[i][1]
        return height + 1

    def getLayoutWidth(self, corners):
        width = -1
        for i in range(len(corners)):
            if corners[i][0] > width:
                width = corners[i][0]
        return width + 1

    # Functions to manipulate the map.
    #
    # Put every element in the list of wall elements into the map
    def addWallsToMap(self, state, grid):
        walls = api.walls(state)
        for i in range(len(walls)):
            grid.setValue(walls[i][0], walls[i][1], '%')


    # Put every element in the list of food elements 
    # into the map as an initial utility value defined 
    # from the registerInitialState() function
    def updateFoodInMap(self, state, grid):
        food = api.food(state)
        for i in range(len(food)):
            value = grid.getValue(food[i][0], food[i][1])
            grid.setValue(food[i][0], food[i][1], value+self.food_reward)

    # Put every element in the list of capsule elements 
    # into the map as an initial utility value defined 
    # from the registerInitialState() function
    def updateCapsuleInMap(self, state, grid):
        capsules = api.capsules(state)
        for i in range(len(capsules)):
            value = grid.getValue(capsules[i][0], capsules[i][1])
            grid.setValue(capsules[i][0], capsules[i][1], value+self.capsule_reward)

    # Put every element in the list of ghosts into the map
    # the initial utility value is obtained by calculateGhostReward() function
    def updateGhostInMap(self, state, grid):

        ghosts_nearby_locations_distances = self.getLocationsNearGhosts(state)

        for i in range(grid.getWidth()):
            for j in range(grid.getHeight()):
                if grid.getValue(i, j) != "%":
                    # grid.getValue(i, j) + 
                    value = grid.getValue(i, j) + self.calculateGhostReward((i,j), ghosts_nearby_locations_distances)
                    grid.setValue(i, j, value)

    # Function that gives pacman a direction to go on to the next state
    def getAction(self, state):

        # get the current position of the pacman
        pacman_current_position = api.whereAmI(state)
        print "I'm at:", pacman_current_position

        # get locations to avoid that are near the ghost
        # with additional information 
        # including it's distance to the ghost and ghost's scared time
        ghosts_nearby_locations_distances = self.getLocationsNearGhosts(state)
        print ghosts_nearby_locations_distances

        # ratio between the total number of food at the beginning of the game 
        # and the current remaining number of food
        total_food_ratio = self.total_food_num / len(api.food(state))
        
        # update the food reward based on the remaining number of food. 
        # so that when there is less food left, 
        # pacman will try it best to finish the game as soon as it can
        if total_food_ratio > 5:
            self.food_reward = INITIAL_REWARD_FOOD + 3
            # self.capsule_reward = INITIAL_REWARD_CAPSULE + 3
        elif total_food_ratio > 3:
            self.food_reward = INITIAL_REWARD_FOOD + 2
            # self.capsule_reward = INITIAL_REWARD_CAPSULE + 2
        elif total_food_ratio > 1:
            self.food_reward = INITIAL_REWARD_FOOD + 1
            # self.capsule_reward = INITIAL_REWARD_CAPSULE + 1

        # initialise the utility map
        self.utility_map.setAllValue(self.initial_reward)
        self.addWallsToMap(state, self.utility_map)
        self.updateFoodInMap(state, self.utility_map)
        self.updateGhostInMap(state, self.utility_map)

        # initialise the direction map
        self.direction_map.setAllValue("")
        self.addWallsToMap(state, self.direction_map)

        # display the initial map
        self.utility_map.prettyDisplay()

        # value iteration for the map
        self.updateMapUtilities(state, ghosts_nearby_locations_distances)

        # display the current map
        # self.utility_map.prettyDisplay()
        self.direction_map.prettyDisplay()

        legal = api.legalActions(state)
        # if Directions.STOP in legal:
        #     legal.remove(Directions.STOP)

        # Random choice between the legal options.
        # return api.makeMove(direction, legal)
        if self.direction_map.getValue(pacman_current_position[0], pacman_current_position[1]) == '':
            direction = random.choice(legal)
        else:
            direction = self.direction_map.getValue(pacman_current_position[0], pacman_current_position[1])

        print "result direction =", direction
        return api.makeMove(direction, legal)

    # Function to get whether an known position contains food
    def positionHasFood(self, state, position):
        foodList = api.food(state)
        for food in foodList:
            if food[0] == position[0] and food[1] == position[1]:
                return True
        
        return False
    
    # Function to get whether an known position contains capsule
    def positionHasCapsule(self, state, position):
        capsules = api.capsules(state)
        for capsule in capsules:
            if capsule[0] == position[0] and capsule[1] == position[1]:
                return True

        return False

    # Function to get a target position's value from the map 
    # given a position and the next direction 
    # e.g. what is the position's value to the south of (1,1) on utility map ?
    def targetPositionValue(self, map, position, direction, distance=1):
        result = '%'
        result_position = position
        if direction == Directions.NORTH:
            result_position = (position[0], position[1]+distance)
            result = map.getValue(position[0], position[1]+distance)
        if direction == Directions.SOUTH:
            result_position = (position[0], position[1]-distance)
            result = map.getValue(position[0], position[1]-distance)
        if direction == Directions.WEST:
            result_position = (position[0]-distance, position[1])
            result = map.getValue(position[0]-distance, position[1])
        if direction == Directions.EAST:
            result_position = (position[0]+distance, position[1])
            result = map.getValue(position[0]+distance, position[1])

        return result, result_position

    # Function to get whether an known position is near to the ghost
    def positionNearGhost(self, position, ghosts_nearby_locations_distances):
        for location_distance_pair in ghosts_nearby_locations_distances:
            if position[0] == location_distance_pair[0][0] and position[1] == location_distance_pair[0][1]:
                return True
        return False

    # Function to calculate the manhattan distance between 2 positions
    def getManhattanDistance(self, position, ghost_postion):
        return abs(position[0]-ghost_postion[0]) + abs(position[1]-ghost_postion[1])

    # Function to get all the locations that are near the ghost
    # which is also a list of locations that pacman should try to avoid
    #
    # The returned value are formatted as follows: 
    # ((x, y), distance to the ghost, ghost edible time) 
    # the function so through each position on the map 
    # and calculate distance between it and each of the ghost. 
    # If the distance is below a certain threshold 
    # and there is no wall between them, then this location will get added on to the "unsafe location list"
    # if there are walls between them, then the location in discarded as it should be relatively safe for pacman to be there
    def getLocationsNearGhosts(self, state):

        # get all the information required: 
        # locations of walls and locations of ghosts
        ghosts = api.ghostStatesWithTimes(state)
        walls = api.walls(state)
        # the list that contains all of the locations to avoid
        nearby_locations_distances = []

        for ghost in ghosts:

            ghost_position = ghost[0]

            for i in range(self.utility_map.getWidth()):
                for j in range(self.utility_map.getHeight()):
                    distance = self.getManhattanDistance((i, j), ghost_position)

                    # if the distance between the position and the ghost is below 4
                    if distance < 4:
                        
                        # if there are walls between the current position and the ghost
                        # then there is no need to worry 
                        if self.getNumWallBetween(walls, (i, j), ghost_position) > 0:
                            # print "[walls between", (i, j),"and", ghost_position, "]"
                            # continue to the next position
                            continue
                        
                        # check if the location already exists on the list
                        for nearby_locations_distance in nearby_locations_distances:
                            if nearby_locations_distance[0][0] == i and nearby_locations_distance[0][1] == j:
                                # if distance is nearer here
                                if nearby_locations_distance[1] > distance:
                                    nearby_locations_distance = ((i, j), distance, ghost[1])
                                    print "location repeated!", (i, j)
                                    break
                        
                        # add this new location to the list 
                        # that contains all of the locations to avoid
                        # format: ((x, y), distance to the ghost, ghost edible time)
                        nearby_locations_distances.append(((i, j), distance, ghost[1]))

        return nearby_locations_distances

    # Function to get number of walls between two locations
    def getNumWallBetween(self, walls, position, target_position):

        wall_num = 0
        position = (int(position[0]), int(position[1]))
        target_position = (int(target_position[0]), int(target_position[1]))

        # if positions are neither on the same column or same horizontal line
        # then walls in between both directions needed to be calculated
        if position[0] != target_position[0] and position[1] != target_position[1]:
            original_target_position = target_position
            target_position = (position[0], target_position[1])
            if position[1] > target_position[1]:
                list = range(target_position[1], position[1])
            else:
                list = range(position[1], target_position[1])
                
            for num in list:
                if (position[0], num) in walls:
                    wall_num += 1
            
            target_position = (original_target_position[0], position[1])
            if position[0] > target_position[0]:
                list = range(target_position[0], position[0])
            else:
                list = range(position[0], target_position[0])
                
            for num in list:
                if (num, position[1]) in walls:
                    wall_num += 1

        # if positions are on the same horizontal line
        elif position[0] == target_position[0]:
            
            if position[1] > target_position[1]:
                list = range(target_position[1], position[1])
            else:
                list = range(position[1], target_position[1])
                
            for num in list:
                if (position[0], num) in walls:
                    wall_num += 1

        # if positions are on the same column
        elif position[1] == target_position[1]:
            
            if position[0] > target_position[0]:
                list = range(target_position[0], position[0])
            else:
                list = range(position[0], target_position[0])
                
            for num in list:
                if (num, position[1]) in walls:
                    wall_num += 1

        return wall_num

    # Function that gives the reward for those positions that are near the ghost
    # based on infomation including distance to the ghost and remaining scared time 
    # 
    # if the ghost is scared then a positive reward is assigned,
    # otherwise an negative reward is assigned based on its distance to the ghost. 
    # The closer to the ghost, lower reward (an even more negative value) is assigned.
    def calculateGhostReward(self, position, ghosts_nearby_locations_distances):
        reward = 0
        for location_distance in ghosts_nearby_locations_distances:
            if position[0] == location_distance[0][0] and position[1] == location_distance[0][1]:
                distance_to_ghost = location_distance[1]
                scaredTime = location_distance[2]
                
                if scaredTime > 2:
                    # there are plenty of scared time, 
                    # so an extra edible_ghost_reward is added. 
                    # The distance is also involved here 
                    # as if pacman is too far away from the ghost then there is no need to chase it
                    reward = self.edible_ghost_reward - (distance_to_ghost*0.5)
                    # TODO testing required here
                    # reward = self.edible_ghost_reward
                elif scaredTime > 0:
                    reward = (distance_to_ghost*0.5)
                else:
                    # the ghost is not scared
                    # nearby ghost has lower rewards
                    reward += self.ghost_reward + (distance_to_ghost*0.5)
        
        return reward

    # Function that updates the utility value from the self.utility_map 
    # until all values on the map converges
    def updateMapUtilities(self, state, ghosts_nearby_locations_distances):
        
        # initially, the values are not converging
        converge = False

        # continue the calculation until the value converges
        while not converge:
            
            # calculate the utility value at each position
            for i in range(self.utility_map.getWidth()):
                for j in range(self.utility_map.getHeight()):
                    if self.utility_map.getValue(i, j) != '%':
                        # print 'test', self.utility_map.getValue(i, j)
                        converge = True
                        position = (i, j)
                        # calculate the maximum utility value, and the direction that lead to it
                        maximum_expected_utility_direction, maximum_expected_utility = self.findMaximumExpectedUtility(position, DIRECTIONS)
                        # get new utility value for the current iteration
                        updated_utility_value = self.updateUtility(state, position, maximum_expected_utility, ghosts_nearby_locations_distances)
                        
                        # testing convergence for the cell
                        if abs(updated_utility_value - self.utility_map.getValue(i, j)) > self.iteration_threshold:
                            # print "not converge yet"
                            converge = False
                        
                        # fill new values onto the map
                        self.utility_map.setValue(i, j, updated_utility_value)
                        self.direction_map.setValue(i, j, maximum_expected_utility_direction)
            
            # print "not converge yet"
            self.utility_map.prettyDisplay()
            print "================"

    # Function that calculate the utility value using Bellman equation
    def updateUtility(self, state, position, maximum_expected_utility, ghosts_nearby_locations_distances):
        # position = api.whereAmI(state)
        # print "reward = ", self.calculateReward(state, position)
        updated_utility_value = self.calculateReward(state, position, ghosts_nearby_locations_distances) + self.discount_factor*maximum_expected_utility

        return updated_utility_value

    # Function that find the maximum expected utility from different directions
    # which returns the direction that gives the maximum expected utility and the utility value
    def findMaximumExpectedUtility(self, position, directions):
        maximum_utility_direction = ''
        maximum_expected_utility = -100
        expected_utility = -100
        # total_num_utilities = 0
        # equal_num_utilities = 0

        # loops through all directions
        for d in directions:
            # calculate the expected utility in direction d
            expected_utility, there_is_a_wall = self.calculateExpectedUtility(position, d)
            # expected_utility = round(expected_utility, 2)
            # if expected_utility == maximum_expected_utility:
            #     equal_num_utilities += 1
            # print "direction = ", d
            # print "expected utlity = ", expected_utility
            
            # if there is a wall in direction, 
            # then ignore this direction and continue the iteration
            if there_is_a_wall:
                continue
            
            # store the maximum expected utility value
            elif expected_utility > maximum_expected_utility:
                maximum_expected_utility = expected_utility
                maximum_utility_direction = d
            
            # total_num_utilities+=1

        # if utility to go all directions are the same
        # if total_num_utilities == equal_num_utilities:
        #     maximum_utility_direction = ''

        return maximum_utility_direction, maximum_expected_utility

    # Function that calculate the expected utility at the specified position in the given direction
    def calculateExpectedUtility(self, position, direction):
        expected_utility = 0
        probabilities = [0.8, 0.1, 0.1]
        there_is_a_wall = False

        # get the last iteration utility value at 4 different directions
        u_north, _ = self.targetPositionValue(self.utility_map, position, Directions.NORTH)
        u_south, _ = self.targetPositionValue(self.utility_map, position, Directions.SOUTH)
        u_west, _ = self.targetPositionValue(self.utility_map, position, Directions.WEST)
        u_east, _ = self.targetPositionValue(self.utility_map, position, Directions.EAST)

        # if there is a wall in the given direction
        if u_north == '%':
            u_north = self.utility_map.getValue(position[0], position[1])
            if direction == Directions.NORTH:
                there_is_a_wall = True
        if u_south == '%':
            u_south = self.utility_map.getValue(position[0], position[1])
            if direction == Directions.SOUTH:
                there_is_a_wall = True
        if u_west == '%':
            u_west = self.utility_map.getValue(position[0], position[1])
            if direction == Directions.WEST:
                there_is_a_wall = True
        if u_east == '%':
            u_east = self.utility_map.getValue(position[0], position[1])
            if direction == Directions.EAST:
                there_is_a_wall = True
        
        if direction == Directions.NORTH:
            utilities = [u_north, u_west, u_east]
        elif direction == Directions.SOUTH:
            utilities = [u_south, u_east, u_west]
        elif direction == Directions.WEST:
            utilities = [u_west, u_south, u_north]
        elif direction == Directions.EAST:
            utilities = [u_east, u_north, u_south]
        
        expected_utility = sum(self.multiplyArray(utilities, probabilities))

        return expected_utility, there_is_a_wall

    # Function that multiples each element of 2 arrays (with the same length) 
    # and produce a result array
    def multiplyArray(self, arr1, arr2):
        # print arr1, arr2
        if len(arr1) != len(arr2):
            print 'arrays length are not stisfied'
            return
        res_arr = []
        for i in range(len(arr1)):
            res_arr.append(arr1[i] * arr2[i])

        return res_arr

    # Function that culculate the reward value of the specified position
    # 
    # if the position is near the ghost then we assign the value 
    # based on the information got from the function getLocationsNearGhosts() 
    # and the function calculateGhostReward() that calculate the reward based on that. 
    # otherwise a (partially) fixed reward is assigned to the position that contains food and capsule
    def calculateReward(self, state, position, ghosts_nearby_locations_distances):

        reward = self.initial_reward

        # if the position nears the ghost
        if self.positionNearGhost(position, ghosts_nearby_locations_distances):
            reward += self.calculateGhostReward(position, ghosts_nearby_locations_distances)
        else:
            # if position contains the food
            if self.positionHasFood(state, position):
                # TODO modify food reward
                reward += self.food_reward
            # if position contains the capsule
            if self.positionHasCapsule(state, position):
                reward += self.capsule_reward

        return reward