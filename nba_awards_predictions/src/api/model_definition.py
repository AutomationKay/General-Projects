import torch.nn as nn

class NBAAwardNet(nn.Module):
    def __init__(self, input_size: int):
        super(NBAAwardNet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 128), 
            nn.LeakyReLU(0.1),
            nn.Dropout(0.2),
            
            nn.Linear(128, 64),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.2),
            
            nn.Linear(64, 32),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.2),
            
            nn.Linear(32, 16),
            nn.LeakyReLU(0.1),
            
            nn.Linear(16, 1),
        )

    def forward(self, x):
        return self.network(x)