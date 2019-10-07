
fn = 'data/universities2.txt'


with open(fn) as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]
    n = len(lines)
    for i in range(n/2):
        print "%s -> %s" % (lines[2*i], lines[2*i+1])
