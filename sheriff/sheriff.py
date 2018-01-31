import random
import gym
import os

import ai


class SheriffChaseEnv(ai.MDP):
    """ Simple 1D criminal chase game implemented as an OpenAI Gym environment extended to MDP.
    The goal is to catch the criminal 'o' and avoid prison '#' by walking sheriff '*' left or right.
    """
    size = 10
    prison = 7
    criminal = 3

    action_space = gym.spaces.Discrete(2)
    observation_space = gym.spaces.Discrete(size)
    metadata = {'render.modes': ['ansi']}
    reward_range = (-1, +1)
    discount_factor = 0.9

    def __init__(self):
        self.sheriff = None

    def step(self, action):
        """ Run one time-step of the game dynamics. Based on the provided action sheriff moves
        left or right and wraps around the boundaries of the game. """
        assert self.action_space.contains(action)
        self.sheriff, reward = self.transition(self.sheriff, action)
        done = (reward != 0)
        info = {}
        observation = self.sheriff
        return observation, reward, done, info

    def transition(self, observation, action):
        """ Return transition to where the action makes the MDP transition to from observation. """
        assert self.action_space.contains(action)
        assert self.observation_space.contains(observation)
        action_to_step = {0: -1, 1: +1}
        step = action_to_step[action] if observation not in [self.criminal, self.prison] else 0
        transition = (observation + step) % self.size
        transition_to_reward = {self.criminal: +1, self.prison: -1}
        reward = transition_to_reward.get(transition, 0)
        return transition, reward

    def reset(self):
        """ Reset the state of the environment and return the initial observation. """
        population = [obs for obs in range(self.size) if obs not in [self.prison, self.criminal]]
        self.sheriff = random.choice(population)
        observation = self.sheriff
        return observation

    def render(self, mode='human', policy=None):
        """ Render the environment for debugging and visualization. """
        if mode == 'ansi':
            action_map = {0: "<", 1: ">"}
            observation_map = {self.sheriff: "*", self.prison: "#", self.criminal: "o"}
            if policy is not None:
                chars = [observation_map.get(obs, action_map[policy[obs]]) for obs in range(self.observation_space.n)]
            else:
                chars = [observation_map.get(obs, "-") for obs in range(self.observation_space.n)]
            return "".join(chars)
        else:
            return super(self).render(mode=mode)

    def seed(self, seed=None):
        """ Set the seed for the random number generator. """
        if seed is None:
            seed = int(os.urandom(n=8).hex(), base=16)
        random.seed(a=seed)
        return [seed]

    def __str__(self):
        return self.render(mode='ansi')


if __name__ == '__main__':
    gym.envs.registration.register(id='SheriffChase-v0', entry_point='sheriff:SheriffChaseEnv')
    game = gym.make('SheriffChase-v0')
    game.reset()
    actions_keymap = {"l": 0, "r": 1}
    policy_vi = ai.value_iteration(mdp=game)
    policy_pi = ai.policy_iteration(mdp=game)
    policy_ql = ai.q_learning(env=game)
    game.reset()

    print("Catch criminal 'o', avoid prison '#' and have fun :)")
    print("|{policy}|  Hint from value iteration algorithm".format(policy=game.render('ansi', policy_vi)))
    print("|{policy}|  Hint from policy iteration algorithm".format(policy=game.render('ansi', policy_pi)))
    print("|{policy}|  Hint from q learning algorithm".format(policy=game.render('ansi', policy_ql)))

    done = False
    while not done:
        prompt = "|{game}|  Move sheriff '*' left or right (L <*> R) : ".format(game=game.render('ansi'))
        key = input(prompt)[0].lower()
        action = actions_keymap.get(key, 0)
        observation, reward, done, info = game.step(action)

    if reward > 0:
        print("You won :)")
    if reward < 0:
        print("You lost :(")
