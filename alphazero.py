import os
import sys
import torch
import numpy as np
from tqdm import tqdm
from collections import deque

from connect4.connect4_network import Connect4_Network
from utils import setup_session, save_checkpoint, load_checkpoint
from mcts import MCTS

class AlphaZero:
    def __init__(self, game_rules, nnet, args):
        self.game_rules = game_rules
        self.nnet = nnet
        self.args = args

        self.oppnnet = Connect4_Network(self.game_rules, self.args)
        self.sess_num = setup_session()
        self.checkpoint_num = 0
        save_checkpoint(self.nnet, self.sess_num, self.checkpoint_num)
        load_checkpoint(self.oppnnet, self.sess_num, self.checkpoint_num)
        self.training_data = deque(maxlen=self.args.play_memory)

    def iterate(self):
        """
        The main training loop
        """
        for i in range(self.args.iterations):
            print(f"Iteration {i+1}/{self.args.iterations}")

            # self-play to generate training data
            print(f"\nSelf-play: ({self.args.episodes} episodes)")
            for sp in tqdm(range(self.args.episodes), desc="Self-play"):
                mcts = MCTS(self.game_rules, self.nnet, self.args)
                self.self_play(mcts)
                #examples = self.self_play(mcts)
                #self.training_data.extend(examples)

            # train the network
            print("\nTraining Neural Network")
            self.nnet.train(self.training_data)

            # pit the new and the previous networks against each other to evaluate the performance of the newly updated network
            print(f"\nPit Playoff Evaluation")
            wins, ties, losses = self.pit()

            score = wins / max((wins + losses), 1)
            print(f"W: {wins} - T: {ties} - L: {losses} - Score: {score}")

            if score >= self.args.playoff_score_threshold:
                print("Updated Network Accepted\n\n")
                self.checkpoint_num += 1
                save_checkpoint(self.nnet, self.sess_num, self.checkpoint_num)
                load_checkpoint(self.oppnnet, self.sess_num, self.checkpoint_num)
            else:
                print("Updated Network Rejected\n\n")
                load_checkpoint(self.nnet, self.sess_num, self.checkpoint_num)

    def self_play(self, mcts):
        sequence = []
        board = self.game_rules.start_board()
        cur_player = 1
        step = 0

        while not self.game_rules.terminal(board):
            step += 1
            board_perspective = self.game_rules.perspective(board, cur_player)
            temperature = int(step < self.args.exploration_temp_threshold)
            
            pi = mcts.tree_search(board_perspective, temperature)

            symmetric_positions = self.game_rules.get_symmetric_positions(board_perspective, pi)
            for sym_board, sym_pi in symmetric_positions:
                sequence.append((sym_board, sym_pi, cur_player))

            action = np.random.choice(self.game_rules.get_action_space(), p=pi)
            board, cur_player = self.game_rules.step(board, action, cur_player)

        value = self.game_rules.result(board, 1)
        for board, pi, player in sequence:
            v = (1 if player == value else -1) if value else 0
            self.training_data.append((board, pi, v))

    def pit(self):
        wins = 0
        ties = 0
        losses = 0

        for _ in tqdm(range(int(self.args.playoffs / 2)), desc="Playoff (as player 1)"):
            result = self.playoff(
                MCTS(self.game_rules, self.nnet, self.args),
                MCTS(self.game_rules, self.oppnnet, self.args)
            )
            if result == 1:
                wins += 1
            elif result == 0:
                ties += 1
            else:
                losses += 1

        for _ in tqdm(range(int(self.args.playoffs / 2)), desc="Playoff (as player 2)"):
            result = self.playoff(
                MCTS(self.game_rules, self.oppnnet, self.args),
                MCTS(self.game_rules, self.nnet, self.args)
            )
            if result == 1:
                losses += 1
            elif result == 0:
                ties += 1
            else:
                wins += 1

        return wins, ties, losses

    def playoff(self, mcts1, mcts2):
        cur_player = 1
        board = self.game_rules.start_board()

        while not self.game_rules.terminal(board):
            board_perspective = self.game_rules.perspective(board, cur_player)

            if cur_player == 1:
                pi = mcts1.tree_search(board_perspective, 0)
            else:
                pi = mcts2.tree_search(board_perspective, 0)

            action = np.argmax(pi)
            board, cur_player = self.game_rules.step(board, action, cur_player)

        if cur_player == 1:
            board = self.game_rules.perspective(board, cur_player)
            return self.game_rules.result(board, cur_player)
        else:
            return self.game_rules.result(board, 1)