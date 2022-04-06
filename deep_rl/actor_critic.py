#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import torch
from torch import nn
from torch.distributions import MultivariateNormal


####
class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim, exploration_param=0.05, device="cpu"):
        super(ActorCritic, self).__init__()
        # output of actor in [0, 1]
        self.actor = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, action_dim),
            nn.Sigmoid()
        )
        # critic
        self.critic = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        self.device = device
        self.action_var = torch.full((action_dim,), exploration_param ** 2).to(self.device)  # 填充一维向量，长度是action_dim
        # print("action var:",self.action_var)
        self.random_action = True
    
    def forward(self, state):
        # print("forward")
        # print(state)
        value = self.critic(state)
        
        action_mean = self.actor(state)
        # print("action_mean",action_mean)
        cov_mat = torch.diag(self.action_var).to(self.device)  ## 一维向量填充成对角矩阵
        dist = MultivariateNormal(action_mean, cov_mat)
        # print("dist:",dist)
        
        if not self.random_action:
            action = action_mean
        else:
            action = dist.sample()
        
        action_logprobs = dist.log_prob(action)  # 参考https://pytorch.apachecn.org/docs/0.3/distributions.html 梯度上升 强化学习
        
        return action.detach(), action_logprobs, value
    
    def evaluate(self, state, action):
        # print("evaluate")
        action_mean = self.actor(state)
        cov_mat = torch.diag(self.action_var).to(self.device)
        dist = MultivariateNormal(action_mean, cov_mat)
        
        action_logprobs = dist.log_prob(action)
        dist_entropy = dist.entropy()
        value = self.critic(state)
        
        return action_logprobs, torch.squeeze(value), dist_entropy

