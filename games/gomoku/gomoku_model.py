import torch
import torch.nn as nn

class Residual_Block(nn.Module):
    def __init__(self):
        super(Residual_Block, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=256, out_channels=256, kernel_size=(3, 3), stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(256)
        self.conv2 = nn.Conv2d(in_channels=256, out_channels=256, kernel_size=(3, 3), stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(256)
        
    def forward(self, x):
        residual = x
        r = x
        r = self.conv1(r)
        r = self.bn1(r)
        r = torch.relu(r)
        r = self.conv2(r)
        r = self.bn2(r)
        r += residual
        r = torch.relu(r)
        return r
        

class Gomoku_Model(nn.Module):
    def __init__(self, args):
        super(Gomoku_Model, self).__init__()
        self.args = args
        
        self.conv_block = nn.Sequential(
            nn.Conv2d(1, 256, kernel_size=(3, 3), stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU()
        )
        
        self.residual_blocks = []
        for _ in range(self.args.res_blocks):
            self.residual_blocks.append(Residual_Block())
        self.residual_tower = nn.Sequential(*self.residual_blocks)
        
        # policy
        self.pi_conv_bn = self.conv_bn(256, 2, kernel_size=1, stride=1)
        self.pi = nn.Linear(2 * 6 * 7, self.args.gomoku_size ** 2)

        # value
        self.v_conv_bn = self.conv_bn(256, 1, kernel_size=1, stride=1)
        self.v_fc = nn.Linear(self.args.gomoku_size ** 2, 256)
        self.v = nn.Linear(256, 1)

    def conv_bn(self, in_channels, out_channels, *args, **kwargs):
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, *args, **kwargs),
            nn.BatchNorm2d(out_channels)
        )
        
    def forward(self, x):
        x = x.reshape(x.shape[0], 1, self.args.gomoku_size, self.args.gomoku_size)
        r = self.conv_block(x)
        r = self.residual_tower(r)

        # policy
        pi = self.pi_conv_bn(r)
        pi = torch.relu(pi)
        pi = pi.reshape(pi.shape[0], -1)
        pi = self.pi(pi)

        # value
        v = self.v_conv_bn(r)
        v = torch.relu(v)
        v = v.reshape(v.shape[0], -1)
        v = self.v_fc(v)
        v = torch.relu(v)
        v = self.v(v)
        v = torch.tanh(v)

        return pi, v
