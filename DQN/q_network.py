from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
import random
from collections import deque


class ZombieQNetwork(nn.Module):
    def __init__(self, input_shape, num_actions, vector_size) -> None:
        super(ZombieQNetwork, self).__init__()
        # input_shape to (4, 11, 11) -> (Channels, Height, Width)

        # Warstwy konwolucyjne (widzenie przestrzenne)
        # Wejście: 4 kanały (klatki), Wyjście: 32 filtry, Kernel: 3x3
        self.conv1 = nn.Conv2d(
            in_channels=input_shape[0],
            out_channels=32,
            kernel_size=3,
            stride=1,
            padding=1,
        )

        # Druga warstwa, żeby wyłapać bardziej złożone zależności
        self.conv2 = nn.Conv2d(
            in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1
        )

        # Obliczamy rozmiar po spłaszczeniu (Flatten)
        # Przy padding=1 i stride=1 wymiar 11x11 się nie zmienia.
        # Więc mamy 64 kanały * 11 * 11
        self.cnn_flatten_dim = 64 * 11 * 11

        # --- GAŁĄŹ 2: WEKTOR (SENSOR) ---
        # Wejście: 2 liczby (dx, dy)
        self.vector_fc = nn.Linear(vector_size, 32)  # Rozszerzamy 2 liczby do 32 cech

        # --- POŁĄCZENIE (FUSION) ---
        # Wejście do warstwy gęstej to suma cech z obrazu i z wektora
        combined_dim: int = self.cnn_flatten_dim + 32

        # Warstwy gęste (podejmowanie decyzji)
        self.fc1 = nn.Linear(combined_dim, 512)
        self.fc2 = nn.Linear(512, num_actions)  # Wyjście: Q-value dla każdej akcji

    def forward(self, image, vector):
        # 1. Przetwarzanie obrazu
        x_img: torch.Tensor = F.relu(self.conv1(image))
        x_img: torch.Tensor = F.relu(self.conv2(x_img))
        x_img: torch.Tensor = x_img.view(x_img.size(0), -1)  # Flatten

        # 2. Przetwarzanie wektora
        x_vec: torch.Tensor = F.relu(self.vector_fc(vector))

        # 3. Łączenie (Concatenate)
        # Łączymy wzdłuż wymiaru 1 (cechy), wymiar 0 to batch
        x_combined: torch.Tensor = torch.cat((x_img, x_vec), dim=1)

        # 4. Decyzja
        x: torch.Tensor = F.relu(self.fc1(x_combined))
        return self.fc2(x)


class ReplayBuffer:
    def __init__(self, capacity) -> None:
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done) -> None:
        # state to teraz krotka: (numpy_array, numpy_array)
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size) -> tuple[tuple[Any, ...], tuple[Any, ...], tuple[Any, ...], tuple[Any, ...], tuple[Any, ...]]:
        # Losujemy paczkę wspomnień do nauki
        batch = random.sample(self.buffer, batch_size)

        # Rozpakowujemy transponując listę krotek
        state, action, reward, next_state, done = zip(*batch)

        # ZMIANA: Zwracamy surowe krotki dla 'state' i 'next_state'.
        # Funkcja learn() sama sobie je rozdzieli na obrazy i wektory.
        # Dla action, reward i done możemy (ale nie musimy) użyć np.array,
        # bo to są proste liczby.
        return state, action, reward, next_state, done

    def __len__(self) -> int:
        return len(self.buffer)
