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
import util

INITIAL_REWARD=-0.04
GHOST_REWARD=-6
DIRECTIONS = [Directions.NORTH, Directions.SOUTH, Directions.WEST, Directions.EAST]

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

    def setAllValue(self, value):
        for i in range(self.height):
            for j in range(self.width):
                self.grid[i][j] = value

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

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"

        self.initial_reward=INITIAL_REWARD
        self.discount_factor=0.6

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running register InitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)
        # Make a map of the right size
        self.initial_map = self.makeMap(state)
        self.addWallsToMap(state, self.initial_map)
        self.updateFoodInMap(state, self.initial_map)
        # self.updateGhostInMap(state, self.initial_map)
        self.initial_map.display()
        # self.last_action = ''
        
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"

        # Make a map by creating a grid of the right size
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


    # Create a map with a current picture of the food that exists.
    def updateFoodInMap(self, state, grid):
        # for i in range(grid.getWidth()):
        #     for j in range(grid.getHeight()):
        #         if grid.getValue(i, j) == -1.8:
        #             grid.setValue(i, j, 0.01)
        food = api.food(state)
        for i in range(len(food)):
            # value = grid.getValue(food[i][0], food[i][1])
            grid.setValue(food[i][0], food[i][1], 0.8)


    # Create a map with a current picture of the food that exists.
    def updateGhostInMap(self, state, grid):
        ghosts_nearby_locations_distances = self.getLocationsNearGhosts(state)

        for i in range(grid.getWidth()):
            for j in range(grid.getHeight()):
                if grid.getValue(i, j) != "%":
                    value = self.calculateGhostReward((i,j), ghosts_nearby_locations_distances)
                    grid.setValue(i, j, value)

    # For now I just move randomly
    def getAction(self, state):

        pacman_current_position = api.whereAmI(state)
        print "I'm at:", pacman_current_position
        # the food at pacman's position is gone
        # self.initial_map.setValue(pacman_current_position[0], pacman_current_position[1], -0.8)

        ghosts_nearby_locations_distances = self.getLocationsNearGhosts(state)
        print ghosts_nearby_locations_distances

        new_map = self.makeMap(state)
        self.addWallsToMap(state, new_map)
        self.updateMapUtilities(state, new_map, ghosts_nearby_locations_distances)
        new_direction_map = self.makeMap(state)
        self.addWallsToMap(state, new_direction_map)

        self.initial_map.prettyDisplay()
        self.initial_map = new_map
        self.initial_map.prettyDisplay()
        
        print "Update direction map with new map utility"
        self.updateDirectionMap(new_map, new_direction_map)
        new_direction_map.prettyDisplay()

        legal = api.legalActions(state)
        # if Directions.STOP in legal:
        #     legal.remove(Directions.STOP)
        # if len(legal) > 1 and self.last_action != '':
        #     legal.remove(self.last_action)

        # Random choice between the legal options.
        # return api.makeMove(direction, legal)
        if new_direction_map.getValue(pacman_current_position[0], pacman_current_position[1]) == '':
            direction = random.choice(legal)
            # self.last_action = direction
        else:
            direction = new_direction_map.getValue(pacman_current_position[0], pacman_current_position[1])
        print "direction=", direction
        return api.makeMove(direction, legal)

    def positionHasFood(self, state, position):
        foodList = api.food(state)
        for food in foodList:
            if food[0] == position[0] and food[1] == position[1]:
                return True
        
        return False

    def targetPostionValue(self, map, position, direction, distance=1):
        result = '%'
        # position = (int(position[0]), int(position[1]))
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

    def positionNearGhost(self, position, ghosts_nearby_locations_distances):
        for location_distance in ghosts_nearby_locations_distances:
            if position[0] == location_distance[0][0] and position[1] == location_distance[0][1]:
                return True
        return False

    def getLocationsNearGhosts(self, state):
        ghosts = api.ghostStatesWithTimes(state)
        # directions = [Directions.NORTH, Directions.SOUTH, Directions.WEST, Directions.EAST]
        nearby_locations_distances = []
        for ghost in ghosts:
            ghost_position = ghost[0]
            # print "ghost: ", ghost
            for i in range(3):
                for direction in DIRECTIONS:
                    # print "ghost: ", ghost, "to the ", direction, ": "
                    value, value_position = self.targetPostionValue(self.initial_map, ghost_position, direction, distance=i)
                    if value != '%':
                        nearby_locations_distances.append((value_position, i))
                        # print direction, " - ", "value position: ", value_position, "value: ", value
                    if i == 0:
                        break

        return nearby_locations_distances

    def calculateGhostReward(self, position, ghosts_nearby_locations_distances):
        reward = 0
        for location_distance in ghosts_nearby_locations_distances:
            if position[0] == location_distance[0][0] and position[1] == location_distance[0][1]:
                reward += GHOST_REWARD + location_distance[1]
        
        return reward

    def positionHasCapsule(self, state, position):
        capsules = api.capsules(state)
        for capsule in capsules:
            if capsule[0] == position[0] and capsule[1] == position[1]:
                return True

        return False

    def updateMapUtilities(self, state, map, ghosts_nearby_locations_distances):
        # directions = [Directions.NORTH, Directions.SOUTH, Directions.WEST, Directions.EAST]
        for i in range(map.getWidth()):
            for j in range(map.getHeight()):
                if map.getValue(i, j) != '%':
                    # print 'test', map.getValue(i, j)
                    position = (i, j)
                    _, maximum_expected_utility = self.findMaximumExpectedUtility(position, DIRECTIONS)
                    updated_utility_value = self.updateUtility(state, position, maximum_expected_utility, ghosts_nearby_locations_distances)
                    map.setValue(i, j, updated_utility_value)
                    # direction_map.setValue(i, j, maximum_utility_direction)

    def updateDirectionMap(self, new_map, direction_map):
        # directions = [Directions.NORTH, Directions.SOUTH, Directions.WEST, Directions.EAST]
        for i in range(direction_map.getWidth()):
            for j in range(direction_map.getHeight()):
                if direction_map.getValue(i, j) != '%':
                    position = (i, j)
                    maximum_utility_direction, _ = self.findMaximumExpectedUtility(position, DIRECTIONS)
                    direction_map.setValue(i, j, maximum_utility_direction)

    # update utility function using bellman equation
    def updateUtility(self, state, position, maximum_expected_utility, ghosts_nearby_locations_distances):
        # position = api.whereAmI(state)
        # print "reward = ", self.calculateReward(state, position)
        updated_utility_value = self.calculateReward(state, position, ghosts_nearby_locations_distances) + self.discount_factor*maximum_expected_utility
        # self.map.setValue(position[0], position[1], updated_utility_value)

        return updated_utility_value

    def findMaximumExpectedUtility(self, position, directions):
        maximum_utility_direction = ''
        maximum_expected_utility = -100
        expected_utility = -10
        for d in directions:
            expected_utility, there_is_a_wall = self.calculateExpectedUtility(position, d)
            expected_utility = round(expected_utility, 2)
            # print "direction = ", d
            # print "expected utlity = ", expected_utility
            if there_is_a_wall:
                continue
            elif expected_utility > maximum_expected_utility:
                    maximum_expected_utility = expected_utility
                    maximum_utility_direction = d

        return maximum_utility_direction, maximum_expected_utility

    def calculateExpectedUtility(self, position, direction):
        # print "current position = ", position
        # position = api.whereAmI(state)
        expected_utility = 0
        probabilities = [0.8, 0.1, 0.1]
        there_is_a_wall = False
        u_north, _ = self.targetPostionValue(self.initial_map, position, Directions.NORTH)
        # print "current pos: ", position, self.initial_map.getValue(position[0], position[1]), "north: ", north_pos, u_north
        u_south, _ = self.targetPostionValue(self.initial_map, position, Directions.SOUTH)
        u_west, _ = self.targetPostionValue(self.initial_map, position, Directions.WEST)
        u_east, _ = self.targetPostionValue(self.initial_map, position, Directions.EAST)

        if u_north == '%':
            u_north = self.initial_map.getValue(position[0], position[1])
            if direction == Directions.NORTH:
                there_is_a_wall = True
        if u_south == '%':
            u_south = self.initial_map.getValue(position[0], position[1])
            if direction == Directions.SOUTH:
                there_is_a_wall = True
        if u_west == '%':
            u_west = self.initial_map.getValue(position[0], position[1])
            if direction == Directions.WEST:
                there_is_a_wall = True
        if u_east == '%':
            u_east = self.initial_map.getValue(position[0], position[1])
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

    def multiplyArray(self, arr1, arr2):
        # print arr1, arr2
        if len(arr1) != len(arr2):
            print 'arrays length are not stisfied'
            return
        res_arr = []
        for i in range(len(arr1)):
            res_arr.append(arr1[i] * arr2[i])

        return res_arr

    def calculateReward(self, state, position, ghosts_nearby_locations_distances):
        reward = self.initial_reward

        if self.positionNearGhost(position, ghosts_nearby_locations_distances):
            reward += self.calculateGhostReward(position, ghosts_nearby_locations_distances)
        
        if self.positionHasFood(state, position):
                reward += 1
            # if self.positionHasGhost(state, position):
            #     reward = -4.8
        if self.positionHasCapsule(state, position):
            reward += 1.8

        return reward