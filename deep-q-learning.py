import env.gridseedpygame as env
import numpy as np
import time

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

'''
The game support multiple seeds and players. In this example, I am considering only one player, 
4 rows and 4 cols, and one seed 
'''

# How many change of states should be used to train the model
train_iterations = 20000
# Once the model is trained, how many iterations should be rendered to show de results
test_iterations = 2000

# Q-learning parameters
discount = 0.9


class ANN(nn.Module):
    # ANN's layer architecture
    def __init__(self):
        # Initialize superclass
        super().__init__()
        # Fully connected layers
        self.inputs = 4
        self.outputs = 4
        self.l1 = nn.Linear(self.inputs, 4)  # To disable bias use bias=False
        self.l2 = nn.Linear(4, 4)
        self.l3 = nn.Linear(4, 4)
        self.l4 = nn.Linear(4, self.outputs)

        # Optimizer type
        self.learning_rate = 0.01
        self.optimizer = optim.Adam(self.parameters(), lr=self.learning_rate)

    # Define how the data passes through the layers
    def foward(self, x):
        # Passes x through layer one and activate with rectified linear unit function
        x = F.relu(self.l1(x))
        x = F.relu(self.l2(x))
        x = F.relu(self.l3(x))
        # Linear output layer
        x = self.l4(x)
        return x

    def feed(self, x):
        outputs = self.foward(x)
        return outputs

    # Train the network with one state
    def backward(self, output, target, t):
        # Zero the parameter gradients
        self.zero_grad()
        # Loss function
        loss_criterion = nn.MSELoss()
        # Calculate loss
        loss = loss_criterion(output, target)
        # Back propagate the loss
        loss.backward()
        print(loss)
        # Adjust the weights
        self.optimizer.step()
        return loss


def get_state(state, row_count, col_count):
    seed_pos = state.seed_pos
    one_pos = state.one_pos
    return [seed_pos[0] / row_count, seed_pos[1] / col_count, one_pos[0] / row_count, one_pos[1] / col_count]

if __name__ == '__main__':
    # Neural network
    model = ANN()
    # Instance of the game
    game_instance = env.Pygame()
    row_count = float(game_instance.row_count) - 1
    col_count = float(game_instance.col_count) - 1
    # Current state is a tuple(seed.x, seed.y, p_one.x, p_one.y)
    state_t = get_state(game_instance.game.reset(), row_count, col_count)
    # Training phase
    training = True
    for t in range(train_iterations):
        # Set tensor values
        input = torch.tensor([state_t])
        # Feed to check approximated Q-values
        output = model.feed(input)
        # print("input", input)
        # print("output", output)

        # Define action
        action = torch.argmax(output[0])
        # print(action)

        # Get state s_t + 1
        new_state, reward = game_instance.game.step(int(action) + 1, 1)
        state_t1 = get_state(new_state, row_count, col_count)

        # Calculate input given new state
        input1 = torch.tensor([state_t1])
        # Feed new state to calculate updated Q-value
        output1 = model.feed(input1)
        # print("input1", input1)
        # print("output1", output1)

        # Calculate max future q
        max_future_q = float(torch.max(output1[0]))
        # Current Q-value
        current_q = float(output[0][action])
        q_target = (0.8 * current_q) + (0.2 * (reward + (discount * max_future_q)))

        # Define target given updated Q-value
        target = output.detach().clone()
        target[0][action] = q_target
        # print("target", target)

        # Train
        loss = model.backward(output, target, 0)

        # Assume new state
        state_t = state_t1

        # Pump events
        game_instance.pump()
        game_instance.render()
        if t < train_iterations // 2:
            time.sleep(0.01)
        else:
            time.sleep(0.05)