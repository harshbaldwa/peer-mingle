import random

names_list = [
    "Alligator", "Anteater", "Armadillo", "Auroch", "Axolotl", "Badger",
    "Bat", "Bear", "Beaver", "Blobfish", "Buffalo", "Camel", "Chameleon",
    "Cheetah", "Chipmunk", "Chinchilla", "Chupacabra", "Cormorant", "Coyote",
    "Crow", "Dingo", "Dinosaur", "Dog", "Dolphin", "Dragon", "Duck",
    "Elephant", "Ferret", "Fox", "Frog", "Giraffe", "Goose", "Gopher",
    "Grizzly", "Hamster", "Hedgehog", "Hippo", "Hyena", "Jackal", "Jackalope",
    "Ibex", "Ifrit", "Iguana", "Kangaroo", "Kiwi", "Koala", "Kraken", "Lemur",
    "Leopard", "Liger", "Lion", "Llama", "Manatee", "Mink", "Monkey", "Moose",
    "Narwhal", "Nyan Cat", "Orangutan", "Otter", "Panda", "Penguin",
    "Platypus", "Python", "Pumpkin", "Quagga", "Quokka", "Rabbit", "Raccoon",
    "Rhino", "Sheep", "Shrew", "Skunk", "Slow Loris", "Squirrel", "Tiger",
    "Turtle", "Unicorn", "Walrus", "Wolf", "Wolverine", "Wombat", "Zebra"
]


def get_random_name():
    return random.choice(names_list)
