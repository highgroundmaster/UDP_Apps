from random import randint, getrandbits
import sys

toss = 'e' == input('(o)dd or (e)ven: ')
throw = lambda: int(input('throw [0 - 6]: ')) % 7


def botchoice():
    c = randint(0, 6)
    print(f'bot threw      {c}')
    return c


isfirstplayer = toss == ((throw() + botchoice()) % 2 == 0)
if isfirstplayer:
    firstbat = 't' == input('Player won the toss. Ba(t) or Bal(l): ')
else:
    firstbat = bool(getrandbits(1))
    print("Bot won the toss and it chose to " + f"{'Bat' if not firstbat else 'Ball'}")


def Innings(inn, target=sys.maxsize):
    s = 0
    while True:
        p = throw()
        b = botchoice()
        if p == b:
            print('HOWZATTT!!!')
            break
        s += p if inn else b
        if s > target:
            break
    print(f'Score: {s}')
    return s


print('\n\nFirst Innings ....\n')
f = Innings(firstbat)

print('\n\nSecond Innings ....\n')
l = Innings(not firstbat, f)

if f != l:
    res = 'You Won' if firstbat == (f > l) else 'You Lost'
    res += f" By {abs(f - l)}"
else:
    res = f'Draw. Both scored {f}'

print(res)
