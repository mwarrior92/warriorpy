'''
    Marc Warrior put this code together, with some help from various entities
    on the internet (stack exchange).
    Contact Marc at warrior@u.northwestern.edu
'''
import subprocess
import diriofile as df
##################################################################
#          SHELL COMMANDS
##################################################################

def terminal(command):
    # run terminal commands with subprocess
    print(command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    first, second = p.communicate()
    print first
    print second
    if len(str(first)) > len(str(second)):
        return first
    else:
        return second


def terminal2(command):
    tmproot = df.getdir()
    tmpsh = tmproot+'blablablabla.sh'
    df.overwrite(tmpsh, command)
    terminal(['chmod +x '+tmpsh])
    print command
    out = terminal([tmpsh])
    print out
    df.remove(tmpsh)
