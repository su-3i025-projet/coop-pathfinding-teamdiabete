# -*- coding: utf-8 -*-
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

game = Game()


def posValide(pos,wallStates,mapSize = 20):
    """
    Vérifie si la position passée en paramètre fait partie de la liste des murs ou sort de la carte
    Est utilisée pour construire l'a*
    """
    row,col = pos
    for w in wallStates:
        rw,cw = w
        if rw == row and cw == col:
            return False
    return row>=0 and row<mapSize and col>=0 and col<mapSize


def calculLongueurs(listeIters):
    """
    Calcule la longueur de chaque sous liste de la liste passée en paramètre
    renvoie la liste de ces longueurs (ordonnée identiquement à la liste origine) et la longueur maximale trouvée
    Est utilisée dans l'initialisation (pour calculer) et le main (pour recalculer) la longueur des différents chemins afin d'itérer
    le temps nécessaire au déroulement des parcours entiers de tous les joueurs meme si ces parcours sont modifiés en cours de route
    """
    listeLenParcours = [len(l) for l in listeIters]
    maxLen = max(listeLenParcours)
    return listeLenParcours,maxLen

def initPath1(posPlayers,players,goalStates,wallStates):
    """
    Initialise les chemins sans aucune gestion de collision qui sera laissée à strategieCollision
    """
    listeIters = []
    playerGoal = [goalStates[i] for i in range(len(players))]
    for i in range(len(posPlayers)):
        listeIters.append(astar([posPlayers[i]],[playerGoal[i]],wallStates))
    listeLenParcours,maxLen  = calculLongueurs(listeIters)
    return { "listeIters" : listeIters, "playerGoal" : playerGoal, "listeLenParcours" : listeLenParcours, "maxLen" : maxLen}

def detection(posPlayers,j,next_pos):
    """
    Vérifie si la destination du joueur j (next_pos) est déjà occupée par un autre joueur
    Est utilisée pour la détection de collision et le lancement de leur gestion dans le main
    """
    posAutresJoueurs = []
    for iter in range(len(posPlayers)):
        if iter != j:
            posAutresJoueurs.append(posPlayers[iter].get_rowcol())
    return next_pos in posAutresJoueurs

def strategieBasique1(numIter,numPlayer,listeIters,wallStates):
    #strategie à implementer
    """
    retourne la liste des tuples des positions du debut a la fin seulement pour le joueur en cours
    position du joueur collisionné = listeIters[numPlayer][numIter]
    calcul du nouveau parcours en considerant le nouveau mur auquel on a ajoute la position de la collision
    remplacement de la fin du parcours par le nouveau chemin calcule precedemment
    """
    if numIter == len(listeIters[numPlayer]) -1:
        return listeIters[numPlayer][:numIter] + [listeIters[numPlayer][numIter-1]] + [listeIters[numPlayer][-1]]
    wallStatesCopy = wallStates.copy()
    for i in range(len(listeIters)):
        if i != numPlayer:
            tmp = numIter
            if i > numPlayer:
                tmp-=1
            if len(listeIters[i]) <= tmp:
                 wallStatesCopy.append(listeIters[i][-1])
            if len(listeIters[i]) > tmp:
                wallStatesCopy.append(listeIters[i][tmp])
    newChemin = astar([listeIters[numPlayer][max(0, numIter-1)]], [listeIters[numPlayer][-1]], wallStatesCopy)

    newL = listeIters[numPlayer][:numIter]
    if(random.random() > 0.1*(numPlayer+1)):
        newL+= [listeIters[numPlayer][max(0, numIter-1)]]
    newL += newChemin
    return newL

def strategieSwap(numIter,numPlayer,listeIters,wallStates,players):
    """
    Fait echanger de place 2 joueurs face à face (ne fonctionne pas)
    """
    numBloqueur = 0
    tmp = 0
    for i in range(len(listeIters)):
        if i != numPlayer:
            tmp = numIter;
            if i > numPlayer:
                tmp-=1;
            if verif4cases(listeIters[numPlayer][numIter],listeIters[i][min(tmp,len(listeIters[i])-1)]):
                numBloqueur = i;
                break;
    if tmp >= len(listeIters[numBloqueur]):
        r,c = listeIters[numPlayer][numIter]
        players[numBloqueur].set_rowcol(r,c)
    else:
        listeIters[numBloqueur] = listeIters[numBloqueur][:tmp] + listeIters[numBloqueur][min(tmp+1,len(listeIters[i])-1):]
        r,c = listeIters[numPlayer][tmp]
        players[numBloqueur].set_rowcol(r,c)    
    time.sleep(1.0/6)
    #game.mainiteration()
    return listeIters[numPlayer]

def verif4cases(pos1, pos2):
    """
    vérifie si pos2 est adjacente directement à pos1
    """
    row, col = pos1
    return pos2 in [(row+1, col), (row, col+1),(row-1, col),(row, col-1)]

def pasDeGestion(numIter,numPlayer,listeIters):
    """
    Permet l'affichage des positions des collisions, utile pour vérifier le bon fonctionnement de la détection de collision
    et etre certain que ceux ci ne créent pas d'interférences avec cette détection
    """
    print("Collision en pos : ",listeIters[numPlayer][numIter])
    print(listeIters)
    #time.sleep(5)
    return listeIters[numPlayer]

def strategieCollision(numIter,numPlayer,listeIters,wallStates,players):
    """
    Le choix de la stratégie de gestion de collision s'effectue ici lorsqu'on choisit de gérer les collisions au moment du déroulement
    des parcours. Si on souhaite gérer l'évitement des autres joueurs au niveau de la création de parcours il faut créer de nouvelles
    fonctions à appeler dans initPath
    """
    return pasDeGestion(numIter,numPlayer,listeIters)
    #return strategieSwap(numIter,numPlayer,listeIters,wallStates,players)
    return strategieBasique1(numIter,numPlayer,listeIters, wallStates)

def verification_objet(pos,playerGoal,goalStates,numPlayer,posPlayers,score,accObjets,players,wallStates,minPos = 1,maxPos = 19):
    """
    Vérifie si on est sur la case de l'objet qu'on cherche à ramasser
        Si c'est le cas, on le ramasse et on le place dans la liste des objets en attente d'etre replacés
        puis on vérifie s'il reste des objets à ramasser
            S'il ne reste aucun objet à ramasser, on replace chaque objet de la liste d'attente de manière aléatoire
            en s'assurant qu'ils n'apparaitront pas dans une case contenant un autre objet ( objectif, joueur ou mur)
    La valeur de retour indique si un objet a été ramassé (True) ou non (False) mais n'est pas utilisée dans le main
    """
    row,col = pos
    nbPlayers = len(players)
    if (row,col) == playerGoal[numPlayer]: # Test : la position actuelle est-elle la position objectif?
        accObjets.append(players[numPlayer].ramasse(game.layers)) # Ramasser l'objet sur cette case et l'ajouter à la file d'attente pour le replacement
        game.mainiteration() # Rafraichissement de l'affichage pour faire disparaitre l'objet de l'ecran
        goalStates.remove((row,col)) # Retrait de la position des positions objectif
        score[numPlayer]+=1 # Ajout d'un point au joueur qui a ramassé l'objet

        if len(goalStates) == 0: # Test : reste-t-il des objectifs à atteindre?
            for a in range(nbPlayers): # Pour chaque joueur
                x = random.randint(minPos,maxPos) # Choix d'une position aléatoire dans les bornes passées en paramètre
                y = random.randint(minPos,maxPos)
                while (x,y) in wallStates or (x,y) in goalStates or (x,y) in posPlayers: # Tirage de position jusqu'à ce que la case tirée soit vide
                    x = random.randint(minPos,maxPos)
                    y = random.randint(minPos,maxPos)
                accObjets[a].set_rowcol(x,y) # Placement de l'objet à la case choisie
                goalStates.append((x,y)) # Ajout des coordonnées de l'objectif à la liste d'objectifs
                game.layers['ramassable'].add(accObjets[a]) # Ajout de l'image de l'objet à l'écran
                game.mainiteration() # Actualisation de l'écran pour y faire apparaitre le nouvel objet posé
            accObjets = [] # Liste d'objets en attente de placement vidée
        return True # Renvoie si oui ou non on a ramassé un objet
    return False;

def astar(initState, goalState, wallStates):
    """
    Calcule le plus court chemin pour aller de la position initiale à la position d'arrivée (sous forme [(x,y)] pour les deux)
    en tenant compte des murs (liste de tuples (x,y))
    Renvoie la liste des différentes positions requises pour y aller en se déplacant uniquement de manière verticale ou horizontale
    """
    if initState == goalState: # Test : Si la case d'arrivée est identique à celle de départ le chemin comporte uniquement cette case
        return goalState

    posDepart = { "pos" : initState[0], "score": 0} # Stockage de la position de départ (puis de la position précédente) et de sa distance avec le départ (score)
    """
    explored est la liste des cases explorées au format :
    [ (posx,posy) , nombre de cases parcourues , distance de Manhattan jusqu'a l'arrivee , case précédente ]
    la case précédente est celle qui a ouvert la case actuelle et sert à la construction de la liste de positions
    """
    explored = [[posDepart.get("pos"), 0, abs(initState[0][0] - goalState[0][0]) + abs(initState[0][1] - goalState[0][1]), None]]
    reserve = [] # Liste de cases à explorer dont on connait le score
    while(True): # Tant qu'aucun chemin n'est trouvé
        nbCasesValides = 0 # Sert à savoir si le joueur peut se déplacer
        for i in [(0,1),(0,-1),(1,0),(-1,0)]: # Exploration de toutes les cases adjacentes à la case actuelle
            next_row = posDepart.get("pos")[0]+i[0]
            next_col = posDepart.get("pos")[1]+i[1]
            nouvellePos = (next_row,next_col)
            if posValide(nouvellePos,wallStates):
                # Si le test n'est passé pour aucune des 4 cases, on est coincé entre 4 murs et on renvoie une liste vide pour l'indiquer
                nbCasesValides  +=1
            # Test : la future position est-elle explorable et non encore explorée?
            if posValide(nouvellePos,wallStates) and (nouvellePos not in [explored[i][0] for i in range(len(explored))]):

                if nouvellePos in goalState: # Test : la position est-elle la position objectif?
                    listeCoups = [] # Liste des positions successives à atteindre pour rejoindre l'objectif
                    listeCoups.append(nouvellePos) # Ajout de la position objectif
                    for truc in explored:
                        if truc[0] == posDepart.get("pos"): # Parcours de la liste de cases explorées pour trouver celle qui a ouvert la case actuelle
                            a = truc # Cette case est a
                            break
                    while a[3]: # Tant que a possède un père, ajout de la position de a dans la liste des positions qui se construit à l'envers
                        listeCoups.append(a[0])
                        nouvellePos = a[3]
                        for truc in explored: # Parcours (encore) de la liste de cases explorées pour trouver celle qui a ouvert la case actuelle
                            if truc[0] == nouvellePos:
                                a = truc
                                break
                    listeCoups.append(initState[0]) # Ajout de la position de départ à la liste de positions à atteindre
                    ltmp = []
                    for ii in range(len(listeCoups),0,-1): # Retournement de la liste de coups (la méthode reverse n'a pas l'effet escompté)
                        ltmp.append(listeCoups[ii-1])
                    return ltmp # Retour de la liste de positions à parcourir pour atteindre l'objectif


                if not (next_row,next_col) in reserve: # Test : la future position est-elle dans les cases dont on connait l'estimation de score?
                    esti = posDepart.get("score") + abs(next_row - goalState[0][0]) + abs(next_col - goalState[0][1]) # Calcul d'estimation de score
                    tmp = [nouvellePos,posDepart.get("score")+1,esti,posDepart.get("pos")]
                    explored.append(tmp) #Ajout de la case à la liste de cases explorées
                    reserve.append(tmp) #Ajout de la case à la liste de cases de la frontière ( qu'il sera possible d'utiliser pour ouvrir de nouvelles cases)
        if not nbCasesValides:
            return []
        minR = 99999999999999
        futureCase = None
        for i in reserve: # Pour chaque case à la frontière entre les cases explorées et non explorées, choix de celle dont l'estimation est
            if i[2] < minR: # la plus petite pour devenir la future case à explorer et recommencer la boucle avec
                minR = i[2]
                posDepart = { "pos" : i[0], "score" : i[1] }
                futureCase = i
        try:
            reserve.remove(futureCase) # S'il est impossible de retirer la case de la réserve, c'est car elle n'y est pas
        except: # Dans ce cas, on retourne un parcours vide car il est impossible de rejoindre la fin dans ces conditions
            return []

def astar3D(initState, goalState, wallStates,listeChemins,posPlayers):
    """
    Calcule le plus court chemin pour aller de la position initiale à la position d'arrivée (sous forme [(x,y)] pour les deux)
    en tenant compte des murs (liste de tuples (x,y))
    Renvoie la liste des différentes positions requises pour y aller en se déplacant uniquement de manière verticale ou horizontale
    """
    if initState == goalState: # Test : Si la case d'arrivée est identique à celle de départ le chemin comporte uniquement cette case
        return goalState

    posDepart = { "pos" : initState[0], "score": 0} # Stockage de la position de départ (puis de la position précédente) et de sa distance avec le départ (score)
    """
    explored est la liste des cases explorées au format :
    [ (posx,posy) , nombre de cases parcourues , distance de Manhattan jusqu'a l'arrivee , case précédente ]
    la case précédente est celle qui a ouvert la case actuelle et sert à la construction de la liste de positions
    """
    explored = [[posDepart.get("pos"), 0, abs(initState[0][0] - goalState[0][0]) + abs(initState[0][1] - goalState[0][1]), None]]
    reserve = [] # Liste de cases à explorer dont on connait le score
    while(True): # Tant qu'aucun chemin n'est trouvé
        nbCasesValides = 0 # Sert à savoir si le joueur peut se déplacer
        for i in [(0,1),(0,-1),(1,0),(-1,0)]: # Exploration de toutes les cases adjacentes à la case actuelle
            next_row = posDepart.get("pos")[0]+i[0]
            next_col = posDepart.get("pos")[1]+i[1]
            nouvellePos = (next_row,next_col)
            wallStatesCopy = wallStates.copy()
            compteurTemps = posDepart.get("score") +1
            if compteurTemps == 0:
                wallStatesCopy += posPlayers
            for i in range(len(listeChemins)):
                wallStatesCopy.append(listeChemins[i][min(max(0,compteurTemps-1),len(listeChemins[i])-1)])
                wallStatesCopy.append(listeChemins[i][min(compteurTemps,len(listeChemins[i])-1)])
                wallStatesCopy.append(listeChemins[i][min(compteurTemps+1,len(listeChemins[i])-1)])                                    
            if posValide(nouvellePos,wallStatesCopy):
                # Si le test n'est passé pour aucune des 4 cases, on est coincé entre 4 murs et on renvoie une liste vide pour l'indiquer
                nbCasesValides  +=1
            # Test : la future position est-elle explorable et non encore explorée?
            if posValide(nouvellePos,wallStatesCopy) and (nouvellePos not in [explored[i][0] for i in range(len(explored))]):

                if nouvellePos in goalState: # Test : la position est-elle la position objectif?
                    listeCoups = [] # Liste des positions successives à atteindre pour rejoindre l'objectif
                    listeCoups.append(nouvellePos) # Ajout de la position objectif
                    for truc in explored:
                        if truc[0] == posDepart.get("pos"): # Parcours de la liste de cases explorées pour trouver celle qui a ouvert la case actuelle
                            a = truc # Cette case est a
                            break
                    while a[3]: # Tant que a possède un père, ajout de la position de a dans la liste des positions qui se construit à l'envers
                        listeCoups.append(a[0])
                        nouvellePos = a[3]
                        for truc in explored: # Parcours (encore) de la liste de cases explorées pour trouver celle qui a ouvert la case actuelle
                            if truc[0] == nouvellePos:
                                a = truc
                                break
                    listeCoups.append(initState[0]) # Ajout de la position de départ à la liste de positions à atteindre
                    ltmp = []
                    for ii in range(len(listeCoups),0,-1): # Retournement de la liste de coups (la méthode reverse n'a pas l'effet escompté)
                        ltmp.append(listeCoups[ii-1])
                    return ltmp # Retour de la liste de positions à parcourir pour atteindre l'objectif


                if not (next_row,next_col) in reserve: # Test : la future position est-elle dans les cases dont on connait l'estimation de score?
                    esti = posDepart.get("score") + abs(next_row - goalState[0][0]) + abs(next_col - goalState[0][1]) # Calcul d'estimation de score
                    tmp = [nouvellePos,posDepart.get("score")+1,esti,posDepart.get("pos")]
                    explored.append(tmp) #Ajout de la case à la liste de cases explorées
                    reserve.append(tmp) #Ajout de la case à la liste de cases de la frontière ( qu'il sera possible d'utiliser pour ouvrir de nouvelles cases)
        if not nbCasesValides:
            return []
        minR = 99999999999999
        futureCase = None
        for i in reserve: # Pour chaque case à la frontière entre les cases explorées et non explorées, choix de celle dont l'estimation est
            if i[2] < minR: # la plus petite pour devenir la future case à explorer et recommencer la boucle avec
                minR = i[2]
                posDepart = { "pos" : i[0], "score" : i[1] }
                futureCase = i
        try:
            reserve.remove(futureCase) # S'il est impossible de retirer la case de la réserve, c'est car elle n'y est pas
        except: # Dans ce cas, on retourne un parcours vide car il est impossible de rejoindre la fin dans ces conditions
            return []
def astar3DBis(initState, goalState, wallStates,listeChemins,posPlayers):
    if initState == goalState: # Test : Si la case d'arrivée est identique à celle de départ le chemin comporte uniquement cette case
        return goalState
    posDepart = { "pos" : initState[0], "score": 0} # Stockage de la position de départ (puis de la position précédente) et de sa distance avec le départ (score)
    explored = [[posDepart.get("pos"), 0, abs(initState[0][0] - goalState[0][0]) + abs(initState[0][1] - goalState[0][1]), None]]
    reserve = [] # Liste de cases à explorer dont on connait le score
    while(True): # Tant qu'aucun chemin n'est trouvé
        print(initState,goalState,posDepart)
        nbCasesValides = 0 # Sert à savoir si le joueur peut se déplacer
        for i in [(0,1),(0,-1),(1,0),(-1,0)]: # Exploration de toutes les cases adjacentes à la case actuelle
            next_row = posDepart.get("pos")[0]+i[0]
            next_col = posDepart.get("pos")[1]+i[1]
            nouvellePos = (next_row,next_col)
            wallStatesCopy = wallStates.copy()
            compteurTemps = posDepart.get("score") +1
            if compteurTemps == 0:
                wallStatesCopy += posPlayers
            for i in range(len(listeChemins)):
                wallStatesCopy.append(listeChemins[i][min(max(0,compteurTemps-1),len(listeChemins[i])-1)])
                wallStatesCopy.append(listeChemins[i][min(compteurTemps,len(listeChemins[i])-1)])
                wallStatesCopy.append(listeChemins[i][min(compteurTemps+1,len(listeChemins[i])-1)])                                    
            if posValide(nouvellePos,wallStatesCopy):
                # Si le test n'est passé pour aucune des 4 cases, on est coincé entre 4 murs et on renvoie une liste vide pour l'indiquer
                nbCasesValides  +=1
            # Test : la future position est-elle explorable et non encore explorée?
            if posValide(nouvellePos,wallStates) and not posValide(nouvellePos,wallStatesCopy):
                esti = posDepart.get("score") + 1 + abs(next_row - goalState[0][0]) + abs(next_col - goalState[0][1]) # Calcul d'estimation de score
                tmp = [posDepart,posDepart.get("score")+1,esti,posDepart.get("pos")]
                reserve.append(tmp)
                explored.append(tmp)
            if posValide(nouvellePos,wallStatesCopy) and (nouvellePos not in [explored[i][0] for i in range(len(explored))]):

                if nouvellePos in goalState: # Test : la position est-elle la position objectif?
                    listeCoups = [] # Liste des positions successives à atteindre pour rejoindre l'objectif
                    listeCoups.append(nouvellePos) # Ajout de la position objectif
                    listeTemporaire = []
                    for truc in explored:
                        if truc[0] == posDepart.get("pos"): # Parcours de la liste de cases explorées pour trouver celle qui a ouvert la case actuelle
                            listeTemporaire.append(truc)
                    scoreMax = 0
                    indiceTemporaire = 0
                    for t in range(len(listeTemporaire)):
                        if listeTemporaire[t][1] > scoreMax:
                            scoreMax =listeTemporaire[t][1]
                            indiceTemporaire = t
                    a = listeTemporaire[indiceTemporaire]
                    explored.remove(a)
                    while a[3]: # Tant que a possède un père, ajout de la position de a dans la liste des positions qui se construit à l'envers
                        listeCoups.append(a[0])
                        nouvellePos = a[3]
                        listeTemporaire = []
                        for truc in explored: # Parcours (encore) de la liste de cases explorées pour trouver celle qui a ouvert la case actuelle
                            if truc[0] == posDepart.get("pos"): # Parcours de la liste de cases explorées pour trouver celle qui a ouvert la case actuelle
                                listeTemporaire.append(truc)
                        scoreMax = 0
                        indiceTemporaire = 0
                        for t in range(len(listeTemporaire)):
                            if listeTemporaire[t][1] > scoreMax:
                                scoreMax =listeTemporaire[t][1]
                                indiceTemporaire = t
                        a = listeTemporaire[indiceTemporaire]
                        explored.remove(a)
                    listeCoups.append(initState[0]) # Ajout de la position de départ à la liste de positions à atteindre
                    ltmp = []
                    for ii in range(len(listeCoups),0,-1): # Retournement de la liste de coups (la méthode reverse n'a pas l'effet escompté)
                        ltmp.append(listeCoups[ii-1])
                    return ltmp # Retour de la liste de positions à parcourir pour atteindre l'objectif

                if not (next_row,next_col) in reserve: # Test : la future position est-elle dans les cases dont on connait l'estimation de score?
                    esti = posDepart.get("score") + abs(next_row - goalState[0][0]) + abs(next_col - goalState[0][1]) # Calcul d'estimation de score
                    tmp = [nouvellePos,posDepart.get("score")+1,esti,posDepart.get("pos")]
                    explored.append(tmp) #Ajout de la case à la liste de cases explorées
                    reserve.append(tmp) #Ajout de la case à la liste de cases de la frontière ( qu'il sera possible d'utiliser pour ouvrir de nouvelles cases)
        if not nbCasesValides:
            return []
        minR = 99999999999999
        futureCase = None
        for i in reserve: # Pour chaque case à la frontière entre les cases explorées et non explorées, choix de celle dont l'estimation est
            if i[2] < minR: # la plus petite pour devenir la future case à explorer et recommencer la boucle avec
                minR = i[2]
                posDepart = { "pos" : i[0], "score" : i[1] }
                futureCase = i
        try:
            reserve.remove(futureCase) # S'il est impossible de retirer la case de la réserve, c'est car elle n'y est pas
        except: # Dans ce cas, on retourne un parcours vide car il est impossible de rejoindre la fin dans ces conditions
            return []

def initPath2(posPlayers,players,goalStates,wallStates):
    """
    Initialise les chemins en considérant les chemins déjà générés comme des murs, sauf si ca implique de ne laisser aucun
    chemin disponible pour un agent, dans ce cas il ne tiendra pas compte de ces restrictions et les collisions potentiellement
    engendrées sont laissées à strategieCollision
    """
    listeIters = []
    playerGoal = [goalStates[i] for i in range(len(players))]
    wallStatesCopy = wallStates.copy()
    for i in range(len(posPlayers)):
        chemin = astar([posPlayers[i]],[playerGoal[i]],wallStatesCopy)
        if(len(chemin) > 0):
            listeIters.append(chemin)
        else:
            print("chemin par defaut joueur ", i)
            listeIters.append(astar([posPlayers[i]],[playerGoal[i]],wallStates))
        wallStatesCopy += listeIters[-1]
    listeLenParcours,maxLen  = calculLongueurs(listeIters)
    return { "listeIters" : listeIters, "playerGoal" : playerGoal, "listeLenParcours" : listeLenParcours, "maxLen" : maxLen}

def initPath3(posPlayers,players,goalStates,wallStates):
    listeIters = []
    playerGoal = [goalStates[i] for i in range(len(players))]
    for i in range(len(posPlayers)):
        listeIters.append(astar([posPlayers[i]],[playerGoal[i]],wallStates))
    """
    on en choisit un au hasard
    on le met dans la liste 1
    pour chaque autre astar
    on regarde s'i y a au moins une case en commun avec ceux de la liste 1
    sinon on l'ajoute a la liste 1
    si oui on cree la liste i+1
    etc on va dans i+2 i+3 jusqu'a ce qu'ils soient tous dans une liste
    une fois que tout ça est fait
    ceux de la liste 1 on les touche pas
    ceux de la liste 2 et plus on les freeze pendant n iterations avec n = longueu max dans liste 1 etc
    etc...
    """
    L0 = []
    L0.append([0])
    for i in range(1, len(listeIters)): #pour chaque autre astar
        for j in listeIters[i]: #pour chaque case de ce astar
            for l in range(len(L0)): #pour chaque sous liste de L0
                for k in L0[0]: # pour chaque astar deja dans la classe 0
                    if j in listeIters[k]: #on verifie si l'iteration est deja dans un des astar de la classe courante
                        continue;



    listeLenParcours,maxLen  = calculLongueurs(listeIters)
    return { "listeIters" : listeIters, "playerGoal" : playerGoal, "listeLenParcours" : listeLenParcours, "maxLen" : maxLen}

def initPath3D(posPlayers,players,goalStates,wallStates):
    """
    Initialise les chemins en considérant les chemins déjà générés comme des murs, sauf si ca implique de ne laisser aucun
    chemin disponible pour un agent, dans ce cas il ne tiendra pas compte de ces restrictions et les collisions potentiellement
    engendrées sont laissées à strategieCollision
    """
    listeIters = []
    playerGoal = [goalStates[i] for i in range(len(players))]
    for i in range(len(posPlayers)):
        chemin = astar3D([posPlayers[i]],[playerGoal[i]],wallStates,listeIters,posPlayers)
        if(len(chemin) > 0):
            listeIters.append(chemin)
        else:
            print("chemin par defaut joueur ", i)
            listeIters.append(astar([posPlayers[i]],[playerGoal[i]],wallStates))
    listeLenParcours,maxLen  = calculLongueurs(listeIters)
    return { "listeIters" : listeIters, "playerGoal" : playerGoal, "listeLenParcours" : listeLenParcours, "maxLen" : maxLen}

def initPath3DBis(posPlayers,players,goalStates,wallStates):
    """
    Initialise les chemins en considérant les chemins déjà générés comme des murs, sauf si ca implique de ne laisser aucun
    chemin disponible pour un agent, dans ce cas il ne tiendra pas compte de ces restrictions et les collisions potentiellement
    engendrées sont laissées à strategieCollision
    """
    listeIters = []
    playerGoal = [goalStates[i] for i in range(len(players))]
    for i in range(len(posPlayers)):
        print(i)
        chemin = astar3DBis([posPlayers[i]],[playerGoal[i]],wallStates,listeIters,posPlayers)
        if(len(chemin) > 0):
            listeIters.append(chemin)
        else:
            print("chemin par defaut joueur ", i)
            listeIters.append(astar([posPlayers[i]],[playerGoal[i]],wallStates))
    listeLenParcours,maxLen  = calculLongueurs(listeIters)
    return { "listeIters" : listeIters, "playerGoal" : playerGoal, "listeLenParcours" : listeLenParcours, "maxLen" : maxLen}


def initPath(initStates,players,goalStates,wallStates):
    """
    Retourne la manière d'initialiser les parcours que l'on a choisie
    """
    return initPath3DBis(initStates,players,goalStates,wallStates)

# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----

def init(_boardname=None):
    global player,game
    # pathfindingWorld_MultiPlayer4
    name = _boardname if _boardname is not None else 'pathfindingWorld_MultiPlayer1'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 15# frames per second

    game.mainiteration()
    game.mask.allow_overlaping_players = True
    #player = game.player

def main():
    init('pathfindingWorld_MultiPlayer1')
    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)
    score = [0]*nbPlayers

    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]

    #version infinie et alternative avec gestion de collision
    accObjets = []
    while 1:
        posPlayers = initStates
        dicoTmp = initPath(initStates,players,goalStates,wallStates)
        listeIters = dicoTmp["listeIters"]
        playerGoal = dicoTmp["playerGoal"]
        listeLenParcours = dicoTmp["listeLenParcours"]
        maxLen = dicoTmp["maxLen"]
        i = 0
        while i < maxLen:
            # print(i,maxLen,[len(l) for l in listeIters])
            for j in range(nbPlayers): # on fait bouger chaque joueur séquentiellement
                if i >= listeLenParcours[j]:
                    continue  #si un joueur a fini on le fait pas bouger
                row,col = listeIters[j][i]
                next_pos = (row, col)
                #print(posAutresJoueurs,next_pos)
                if detection(players,j,next_pos):
                    listeIters[j] = strategieCollision(i,j,listeIters,wallStates,players)
                    listeLenParcours,maxLen  = calculLongueurs(listeIters)
                    row,col = listeIters[j][i]
                players[j].set_rowcol(row,col)
                posPlayers[j] = (row,col)
                game.mainiteration()


                # si on a  trouvé un objet on le ramasse
                a = verification_objet((row,col),playerGoal,goalStates,j,posPlayers,score,accObjets,players,wallStates,12,19)
                #if a:
                #    break
            i+=1
        print(maxLen)
        #print ("scores:", score)
    pygame.quit()

if __name__ == '__main__':
    main()
