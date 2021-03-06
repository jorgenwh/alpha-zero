import numpy as np
from rules import Rules

class Connect4Rules(Rules):
    def __init__(self):
        pass

    def step(self, board, action, player):
        assert self.get_valid_actions(board, player)[action]
        r = self.__lowest_row(board, action)
        new_board = board.copy()
        new_board[r,action] = player
        return new_board, -player

    def get_action_space(self):
        return 7

    def __lowest_row(self, board, action):
        for r in range(5, -1, -1):
            if not board[r,action]:
                return r

    def get_valid_actions(self, board, player):
        valid_actions = [0] * self.get_action_space()
        for a in range(self.get_action_space()):
            if not board[0,a]:
                valid_actions[a] = 1
        return valid_actions

    def get_start_board(self):
        return np.zeros((6, 7))

    def perspective(self, board, player):
        return board * player

    def tostring(self, board):
        return board.tostring()

    def terminal(self, board):
        return sum(self.get_valid_actions(board, 1)) == 0 or sum(self.get_valid_actions(board, -1)) == 0 or self.is_winner(board, 1) or self.is_winner(board, -1)

    def result(self, board, player):
        if self.is_winner(board, player):
            return 1.0
        elif self.is_winner(board, -player):
            return -1.0
        else:
            return 0.0

    def is_winner(self, board, player):
        for c in range(7):
            for r in range(6):
                if c < 4:
                    if board[r,c] == board[r,c+1] == board[r,c+2] == board[r,c+3] == player:
                        return True
                if r < 3:
                    if board[r,c] == board[r+1,c] == board[r+2,c] == board[r+3,c] == player:
                        return True
                if c < 4 and r < 3:
                    if board[r,c] == board[r+1,c+1] == board[r+2,c+2] == board[r+3,c+3] == player:
                        return True
                if c < 4 and r >= 3:
                    if board[r,c] == board[r-1,c+1] == board[r-2,c+2] == board[r-3,c+3] == player:
                        return True
        return False

    def name(self):
        return "Connect 4"