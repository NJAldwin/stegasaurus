# return 1 if the bit is set, zero otherwise
def testbit(int, offset):
    mask = 1 << offset
    return min((int & mask), 1)

# return a new int with the selected bit set
def setbit(int, offset):
    mask = 1 << offset
    return (int | mask)

# return a new int with the selected bit unset
def clearbit(int, offset):
    mask = 1 << offset
    return (int & mask)

# return a new new with the selected bit inverted
def togglebit(int, offset):
    mask = 1 << offset
    return (int ^ mask)
