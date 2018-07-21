import codecs

path = "/Volumes/data/katy/PycharmProjects/DLL/automation/results/scratch.xml"

file = codecs.open(path, 'w', 'utf-8')

file.write("THIS IS SOME TEXT")
file.close()

file = codecs.open(path, 'r', 'UTF-8')

print(file.read())