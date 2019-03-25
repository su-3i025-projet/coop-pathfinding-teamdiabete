# -*- coding: utf-8 -*-

# Nicolas, 2015-11-18

from __future__ import absolute_import, print_function, unicode_literals
from gameclass import Game,check_init_game_done
from spritebuilder import SpriteBuilder
from players import Player
from sprite import MovingSprite
from ontology import Ontology
from itertools import chain
import pygame
import glo
import time
import random 
import numpy as np
import sys


# ---- ---- ---- ---- ---- ----
# ---- Misc                ----
# ---- ---- ---- ---- ---- ----




# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----

game = Game()

def init(_boardname=None):
    global player,game
    name = _boardname if _boardname is not None else 'pathfindingWorld3'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 10 # frames per second
    game.mainiteration()
    player = game.player
 
def astar(initState, goalState, wallStates):
    
    posDepart = { "pos" : initState[0], "score": 0}
    explored = [[posDepart.get("pos"), 0, abs(initState[0][0] - goalState[0][0]) + abs(initState[0][1] - goalState[0][1]), None]]
    reserve = []
    while(True):
        #print(explored,"\n")
        #time.sleep(0.5)
        for i in [(0,1),(0,-1),(1,0),(-1,0)]:        
            next_row = posDepart.get("pos")[0]+i[0]
            next_col = posDepart.get("pos")[1]+i[1]
            nouvellePos = (next_row,next_col)
            if (nouvellePos not in wallStates) and (nouvellePos not in [explored[i][0] for i in range(len(explored))]) and next_row>=0 and next_row<20 and next_col>=0 and next_col<20 :
                if nouvellePos in goalState:
                    listeCoups = []
                    listeCoups.append(nouvellePos)     
                    for truc in explored:
                        if truc[0] == posDepart.get("pos"):
                            a = truc
                            break                    
                    while a[3]:     
                        listeCoups.append(a[0])
                        nouvellePos = a[3] 
                        for truc in explored:
                            if truc[0] == nouvellePos:
                                a = truc
                                break 
                    listeCoups.append(initState[0])
                    ltmp = []
                    for ii in range(len(listeCoups),0,-1):
                        ltmp.append(listeCoups[ii-1])
                    return ltmp
                if not (next_row,next_col) in reserve:
                    esti = posDepart.get("score") + abs(next_row - goalState[0][0]) + abs(next_col - goalState[0][1])
                    tmp = [nouvellePos,posDepart.get("score")+1,esti,posDepart.get("pos")]
                    explored.append(tmp)
                    reserve.append(tmp)                
        minR = 99999999999999
        tmpTrucTruc = None
        for i in reserve:
            if i[2] < minR:
                minR = i[2]
                posDepart = { "pos" : i[0], "score" : i[1] }
                tmpTrucTruc = i
        reserve.remove(tmpTrucTruc)
            
        
    
def main():

    #for arg in sys.argv:
    iterations = 100 # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print ("Iterations: ")
    print (iterations)

    init()
    

    
    #-------------------------------
    # Building the matrix
    #-------------------------------
       
           
    # on localise tous les états initiaux (loc du joueur)
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print ("Init states:", initStates)
    
    # on localise tous les objets ramassables
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print ("Goal states:", goalStates)
        
    # on localise tous les murs
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
    #print ("Wall states:", wallStates)
        
    
    #-------------------------------
    # Building the best path with A*
    #-------------------------------
    path = astar(initStates,goalStates,wallStates)
        
    #-------------------------------
    # Moving along the path
    #-------------------------------
        
    # bon ici on fait juste un random walker pour exemple...
    

    row,col = initStates[0]
    #row2,col2 = (5,5)

    for i in range(len(path)):
    
    
        x_inc,y_inc = path[i]
        next_row = x_inc
        next_col = y_inc
        player.set_rowcol(next_row,next_col)
        print ("pos 1:",next_row,next_col)
        game.mainiteration()
            
        
            
        # si on a  trouvé l'objet on le ramasse
        if (row,col)==goalStates[0]:
            o = game.player.ramasse(game.layers)
            game.mainiteration()
            print ("Objet trouvé!", o)
            break
        '''
        #x,y = game.player.get_pos()
    
        '''

    pygame.quit()
    
        
    
   

if __name__ == '__main__':
    main()
    


